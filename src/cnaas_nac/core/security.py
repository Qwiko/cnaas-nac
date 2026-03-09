from typing import Annotated

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    SecurityScopes,
)
from starlette.requests import Request

from cnaas_nac.core.settings import settings, EnvironmentOption

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
    def __init__(self):
        self._cache = None

    async def get_jwks(self):
        if not self._cache:
            self._cache = await oauth_client.fetch_jwk_set()
        return self._cache


jwks_cache = JWKSCache()


async def get_current_user(
    request: Request,
    security_scopes: SecurityScopes,
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
):
    # Local development token validation skip oauth
    if settings.ENVIRONMENT == EnvironmentOption.LOCAL:
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Missing token, must send bearer token in local-mode.",
            )
        try:
            claims = jwt.decode(token.credentials, settings.SECRET_KEY)
            claims.validate()
            return claims
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=401,
                detail="Token validation-error.",
            )

    if token:
        access_token = token.credentials
    else:
        # Cookie access_token is the access_token
        access_token = request.cookies.get("access_token", "")

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Missing access_token.",
        )

    try:
        # Validate the token
        jwks = await jwks_cache.get_jwks()

        claims = jwt.decode(access_token, key=jwks)

        claims.validate()

        return claims
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
