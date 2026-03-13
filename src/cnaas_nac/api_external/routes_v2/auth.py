import requests
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.responses import RedirectResponse
from urllib.parse import urlencode
from cnaas_nac.core.security import get_current_user, oauth_client
from cnaas_nac.core.settings import settings, EnvironmentOption

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    """
    OAuth Login
    """
    redirect_uri = request.url_for("callback")
    return await oauth_client.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request):
    """
    OAuth callback
    """
    try:
        token = await oauth_client.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error.error}")

    # Extract the tokens
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")

    params = {"access_token": access_token}

    query_string = urlencode(params)

    response = RedirectResponse(url=settings.FRONTEND_CALLBACK_URL + "?" + query_string)

    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True
            if settings.ENVIRONMENT == EnvironmentOption.PRODUCTION
            else False,
            samesite="lax",
            path="/api/v2/auth/refresh",
            max_age=60 * 60 * 24 * 14,
        )

    return response


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    """Refresh access token using refresh token"""
    await oauth_client.load_server_metadata()

    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    ret = requests.post(
        oauth_client.server_metadata["token_endpoint"],
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": oauth_client.client_id,
            "client_secret": oauth_client.client_secret,
        },
    )

    refresh_data: dict = ret.json()
    access_token = refresh_data.get("access_token")
    refresh_token = refresh_data.get("refresh_token")

    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="Missing access token")

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=(
            True if settings.ENVIRONMENT == EnvironmentOption.PRODUCTION else False
        ),
        samesite="lax",
        path="/api/v2/auth/refresh",
        max_age=60 * 60 * 24 * 14,
    )

    return {"access_token": access_token}


@router.post("/logout")
async def logout(request: Request, response: Response):
    # Retrieve the ID token you stored during login

    # TODO
    # Remove internal session
    # Logout session in oidc?

    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=True if settings.ENVIRONMENT == EnvironmentOption.PRODUCTION else False,
        samesite="lax",
        path="/api/v1.0/auth/refresh",
        max_age=0,
    )

    return


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    """Get current user information"""

    return {"name": current_user.get(settings.OIDC_USERNAME_ATTRIBUTE)}


@router.get("/permissions")
async def get_permissions(current_user=Depends(get_current_user)):
    """Get user permissions"""
    # TODO actually map to rbac roles here.

    return {
        "endpoint": ["GET", "POST", "PUT", "DELETE"],
        "endpoint_group": ["GET", "POST", "PUT", "DELETE"],
        "policy": ["GET", "POST", "PUT", "DELETE"],
        "nas_port": ["GET", "POST", "PUT", "DELETE"],
        "accounting": ["GET", "POST", "PUT", "DELETE"],
        "authentication": ["GET", "POST", "PUT", "DELETE"],
        "vlan": ["GET", "POST", "PUT", "DELETE"],
    }
