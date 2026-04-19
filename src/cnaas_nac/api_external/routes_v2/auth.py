from typing import Annotated
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.security import (
    User,
    create_access_token,
    get_current_user,
    get_user_permissions,
    oauth_client,
)
from cnaas_nac.core.settings import EnvironmentOption, settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """
    OAuth Login
    """
    redirect_uri = request.url_for("callback")

    if settings.ENVIRONMENT == EnvironmentOption.PRODUCTION:
        redirect_uri = redirect_uri.replace(scheme="https")

    return await oauth_client.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> RedirectResponse:
    """
    OAuth callback
    """
    try:
        token = await oauth_client.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error.error}")

    # Extract the access_token
    oidc_token = token.get(settings.OIDC_TOKEN_ATTRIBUTE)

    # Get values from the OIDC token. The username and groups attributes are configurable in settings.
    username: str = oidc_token.get(settings.OIDC_USERNAME_ATTRIBUTE, "")
    groups: list[str] = oidc_token.get(settings.OIDC_GROUPS_ATTRIBUTE, [])

    if not username:
        raise HTTPException(status_code=400, detail="Username not found in token")

    # Create new internal jwt token that cnaas_nac have full control over.
    access_token = await create_access_token(db, username, groups)

    query_string = urlencode({"access_token": access_token})

    response = RedirectResponse(url=settings.FRONTEND_CALLBACK_URL + "?" + query_string)

    return response


@router.post("/logout")
async def logout(request: Request, response: Response) -> None:
    # Retrieve the ID token you stored during login

    # TODO
    # Remove internal session
    # Logout session in oidc?

    return


@router.get("/me", response_model=User)
async def me(
    request: Request, current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current user information"""

    return current_user


@router.get("/permissions")
async def get_permissions(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[str]]:
    """Get user permissions"""
    return await get_user_permissions(
        db, current_user.username, current_user.rbac_groups, current_user.is_admin
    )
