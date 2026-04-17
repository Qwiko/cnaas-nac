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
    oauth_client,
)
from cnaas_nac.core.settings import EnvironmentOption, settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
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
):
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
async def logout(request: Request, response: Response):
    # Retrieve the ID token you stored during login

    # TODO
    # Remove internal session
    # Logout session in oidc?

    return


@router.get("/me")
async def me(
    request: Request, current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user information"""

    return current_user.model_dump(include={"name"})


@router.get("/permissions")
async def get_permissions(current_user: Annotated[User, Depends(get_current_user)]):
    """Get user permissions"""
    # TODO actually map to rbac roles here.

    return {
        "endpoint": ["GET", "POST", "PUT", "DELETE"],
        "endpoint_group": ["GET", "POST", "PUT", "DELETE"],
        "policy": ["GET", "POST", "PUT", "DELETE"],
        "nas_port": ["GET", "POST", "PUT", "DELETE"],
        "accounting": ["GET", "POST", "PUT", "DELETE"],
        "authentication": ["GET", "POST", "PUT", "DELETE"],
        "radius_client": ["GET", "POST", "PUT", "DELETE"],
        "vlan": ["GET", "POST", "PUT", "DELETE"],
    }
