import requests
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, HTTPException, Request, Response
from starlette.responses import RedirectResponse

from cnaas_nac.core.security import oauth_client
from cnaas_nac.core.settings import settings

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

    # Prepare the redirect
    response = RedirectResponse(url=settings.FRONTEND_CALLBACK_URL)

    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True if settings.ENVIRONMENT != "local" else False,
            samesite="lax",
            max_age=token.get("expires_in", 3600),
        )

    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True if settings.ENVIRONMENT != "local" else False,
            samesite="lax",
            path="/api/v1.0/auth/refresh",
            max_age=60 * 60 * 24 * 14,
        )

    return response


@router.get("/refresh")
async def refresh(request: Request, response: Response):
    """Refresh access token using refresh token"""
    await oauth_client.load_server_metadata()

    ret = requests.post(
        oauth_client.server_metadata["token_endpoint"],
        data={
            "grant_type": "refresh_token",
            "refresh_token": request.cookies.get("refresh_token"),
            "client_id": oauth_client.client_id,
            "client_secret": oauth_client.client_secret,
        },
    )

    refresh_data: dict = ret.json()
    access_token = refresh_data.get("access_token")
    refresh_token = refresh_data.get("refresh_token")

    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True if settings.ENVIRONMENT != "local" else False,
            samesite="lax",
            max_age=refresh_data.get("expires_in", 3600),
        )

    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True if settings.ENVIRONMENT != "local" else False,
            samesite="lax",
            path="/api/v1.0/auth/refresh",
            max_age=60 * 60 * 24 * 14,
        )

    return {"message": "token updated"}


# @router.get('/logout')
# async def logout(request: Request):
#     # Retrieve the ID token you stored during login
#     id_token = request.session.pop('id_token', None)
#     redirect_uri = request.url_for('logged_out')
#     return await oauth_client.logout_redirect(
#         request,
#         post_logout_redirect_uri=str(redirect_uri),
#         id_token_hint=id_token,
#     )

# @router.get('/logged-out')
# async def logged_out(request: Request):
#     state_data = await oauth_client.validate_logout_response(request)
#     return PlainTextResponse('You have been logged out.')
