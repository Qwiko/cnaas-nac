from datetime import datetime, timedelta, timezone
from typing import Annotated

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from cnaas_nac.core.settings import settings
from cnaas_nac.models.endpoint import EndpointGroup

oauth = OAuth()

oauth.register(
    "oidc",
    client_id=settings.OIDC_CLIENT_ID,
    client_secret=settings.OIDC_CLIENT_SECRET,
    server_metadata_url=settings.OIDC_DISCOVERY_URL,
    client_kwargs={"scope": "openid profile email"},
)

oauth_client: StarletteOAuth2App = oauth.oidc


bearer = HTTPBearer(auto_error=False)


async def create_access_token(
    db: AsyncSession,
    username: str,
    groups: list[str],
) -> str:
    """
    Generates a JWT access token with user information and group memberships.
    """

    is_admin: bool = settings.OIDC_ADMIN_GROUP in groups

    # Fetch group IDs from the database
    # Admin can see all groups
    if is_admin:
        group_ids = []
    else:
        group_ids = list(
            (
                await db.execute(
                    select(EndpointGroup.id)
                    .distinct()
                    .where(EndpointGroup.name.in_(groups))
                )
            )
            .scalars()
            .all()
        )

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRATION_MINUTES
    )

    data = {
        "username": username,
        "groups": groups,
        "group_ids": group_ids,
        "is_admin": is_admin,
        "exp": expire,
    }

    # Encode the token using your secret key and the HS256 algorithm
    header = {"alg": "HS256"}
    token_bytes = jwt.encode(header, data, settings.SECRET_KEY)

    return token_bytes.decode("utf-8")


class User(BaseModel):
    name: str
    groups: list[str] = []
    group_ids: list[int] = []
    permissions: dict[str, list[str]] = {}
    is_admin: bool = False


async def get_current_user(
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> User:
    if not token or not token.credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token.",
        )

    try:
        # Validate the token
        claims = jwt.decode(token.credentials, key=settings.SECRET_KEY)

        claims.validate()

        username: str = claims.get("username", "user")
        groups: list[str] = claims.get("groups", [])
        group_ids: list[int] = claims.get("group_ids", [])
        is_admin: bool = claims.get("is_admin", False)

        user = User(
            name=username, groups=groups, group_ids=group_ids, is_admin=is_admin
        )

        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
