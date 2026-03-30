from datetime import datetime, timedelta
from typing import Annotated

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from cachetools import TTLCache
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.settings import EnvironmentOption, settings
from cnaas_nac.models.endpoint import EndpointGroup

# TODO: Change this to something else
group_cache = TTLCache(maxsize=1000, ttl=300)  # type: ignore[var-annotated]

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


class JWKSCache:
    def __init__(self, ttl: int = 300):
        self._cache = None
        self._expires_at = None
        self._ttl = ttl

    async def get_jwks(self):
        now = datetime.now()

        if self._cache and now < self._expires_at:
            return self._cache

        now = datetime.now()
        if self._cache and now < self._expires_at:
            return self._cache

        jwks = await oauth_client.fetch_jwk_set()

        self._cache = jwks
        self._expires_at = now + timedelta(seconds=self._ttl)

        return self._cache


jwks_cache = JWKSCache()


class User(BaseModel):
    name: str
    group_ids: list[int]
    is_admin: bool = False


async def get_current_user(
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    # Local development token validation skip oauth
    if settings.ENVIRONMENT == EnvironmentOption.LOCAL:
        key = settings.SECRET_KEY
    else:
        jwks = await jwks_cache.get_jwks()
        key = jwks

    if not token or not token.credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token.",
        )

    try:
        # Validate the token
        claims = jwt.decode(token.credentials, key=key)

        claims.validate()

        name: str = claims.get(settings.OIDC_USERNAME_ATTRIBUTE, "")
        groups: list = claims.get(settings.OIDC_GROUPS_ATTRIBUTE, [])
        is_admin: bool = settings.OIDC_ADMIN_GROUP in groups

        group_ids: list[int]

        # TODO: Change this to something else
        # Admin can see all groups
        if is_admin:
            group_ids = []
        elif name in group_cache:
            group_ids = group_cache[name]
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

            group_cache[name] = group_ids

        user = User(name=name, group_ids=group_ids, is_admin=is_admin)

        request.state.current_user = user
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
