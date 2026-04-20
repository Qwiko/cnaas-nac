from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from authlib.jose.errors import JoseError

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
from cnaas_nac.models.rbac import RBAC

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

def _create_jwt_token(data: dict[str, Any]) -> str:
    header = {"alg": "HS256"}
    token_bytes = jwt.encode(header, data, settings.SECRET_KEY)
    try:
        jwt_token = str(token_bytes.decode("utf-8"))
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return jwt_token

async def create_access_token(
    db: AsyncSession,
    username: str,
    groups: list[str],
) -> str:
    """
    Generates a JWT access token with user information and group memberships.

    Args:
        username (str): The username of the user.
        groups (list[str]): A list of group names the user belongs to, this usually comes from OIDC.

    Returns:
        str: The generated JWT access token.

    """

    is_admin: bool = settings.OIDC_ADMIN_GROUP in groups

    # Fetch group IDs from the database
    # Admin can see all groups
    if is_admin:
        endpoint_group_ids = []
    else:
        endpoint_group_ids = list(
            (
                await db.execute(
                    # select(RBAC.allowed_endpoint_groups)
                    select(EndpointGroup.id)
                    .select_from(RBAC)
                    .join(RBAC.allowed_endpoint_groups)
                    .where(RBAC.name.in_(groups))
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRATION_MINUTES
    )

    permissions = await get_user_permissions(db, username, groups, is_admin)

    data = {
        "username": username,
        "rbac_groups": groups,
        "endpoint_group_ids": endpoint_group_ids,
        "is_admin": is_admin,
        "permissions": permissions,
        "exp": expire,
    }

    # Encode the token using your secret key and the HS256 algorithm
    return _create_jwt_token(data)


class User(BaseModel):
    username: str
    rbac_groups: list[str] = []
    endpoint_group_ids: list[int] = []
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

    except JoseError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    # Create a User object from the claims
    user = User(**claims)

    # Admin user have full access
    if user.is_admin:
        return user

    # Validate the user permissions
    url_path = request.url.path.removeprefix("/api/v2/")
    method = request.method

    # All users can access /auth endpoints
    if url_path.startswith("auth/"):
        return user

    if url_path not in user.permissions or method not in user.permissions[url_path]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return user


async def get_user_permissions(
    db: AsyncSession, username: str, groups: list[str], is_admin: bool = False
) -> dict[str, list[str]]:
    if is_admin:
        return {
            "endpoint": ["GET", "POST", "PUT", "DELETE"],
            "endpoint_group": ["GET", "POST", "PUT", "DELETE"],
            "policy": ["GET", "POST", "PUT", "DELETE"],
            "nas_port": ["GET", "POST", "PUT", "DELETE"],
            "accounting": ["GET", "POST", "PUT", "DELETE"],
            "authentication": ["GET", "POST", "PUT", "DELETE"],
            "radius_client": ["GET", "POST", "PUT", "DELETE"],
            "vlan": ["GET", "POST", "PUT", "DELETE"],
            "rbac": ["GET", "POST", "PUT", "DELETE"],
        }

    # Fetch permissions based on user's groups and RBAC settings
    db_rbac = (
        (await db.execute(select(RBAC).where(RBAC.name.in_(groups)))).scalars().all()
    )

    permissions: dict[str, list[str]] = {}
    for rbac in db_rbac:
        for perm in rbac.permissions:
            if perm.path not in permissions:
                permissions[perm.path] = list()
            for method in perm.methods:
                if method not in permissions[perm.path]:
                    permissions[perm.path].append(method)

    return permissions
