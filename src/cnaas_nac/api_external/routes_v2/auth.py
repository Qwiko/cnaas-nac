from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from cnaas_nac.models.radcheck import RadCheck
from cnaas_nac.core.db import get_async_session

from cnaas_nac.schemas.auth import AuthBase, AuthResponse

from cnaas_nac.core.exceptions import NotFound

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("", response_model=AuthResponse)
async def read_auth(
    db: Annotated[AsyncSession, Depends(get_async_session)], response: Response
) -> Any:
    """
    Retrieve auth.
    """

    users = (await db.execute(select(RadCheck))).scalars().all()

    if not users:
        raise NotFound()

    response.headers["X-Total-Count"] = str(len(users))

    return users


@router.post("", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def post_auth(
    input_auth: AuthBase,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Post auth.
    """

    existing_user = (await db.execute(select(RadCheck).where(RadCheck.username == input_auth.username))).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    user = RadCheck(username = input_auth.username,
        attribute = "Cleartext-Password",
        op = ":=" if input_auth.enabled else "",
        value = input_auth.username
    )
    
    db.add(user)
    await db.commit()
    return user
