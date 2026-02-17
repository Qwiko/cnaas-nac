from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.coa import CoA
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.radcheck import RadCheck
from cnaas_nac.models.radreply import RadReply
from cnaas_nac.schemas.auth import AuthBase, AuthCreate, AuthResponse, AuthUpdate
from netutils.mac import is_valid_mac, mac_to_format
logger = get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("", response_model=list[AuthResponse])
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
    input_auth: AuthCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Post auth.
    """

    existing_user = (
        await db.execute(
            select(RadCheck).where(RadCheck.username == input_auth.username)
        )
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    user = RadCheck(
        username=input_auth.username,
        attribute="Cleartext-Password",
        op=":=" if input_auth.enabled else "",
        value=input_auth.username,
    )

    db.add(user)
    await db.commit()
    return user


@router.put("/{username}", response_model=AuthResponse)
async def put_auth(
    username: str,
    input_auth: AuthUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks
) -> Any:
    """
    Put auth.
    """
    
    if is_valid_mac(username):
        username = mac_to_format(username, "MAC_COLON_TWO")

    existing_user = (
        await db.execute(select(RadCheck).where(RadCheck.username == username))
    ).scalar_one_or_none()
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No user found with username: {username}",
        )

    if existing_user.enabled != input_auth.enabled:
        existing_user.op = ":=" if input_auth.enabled else ""

    await db.execute(
        update(RadReply)
        .where(
            RadReply.username == username,
            RadReply.attribute == "Tunnel-Private-Group-Id",
        )
        .values(value=str(input_auth.vlan))
    )

    await db.commit()
    await db.refresh(existing_user)

    recent_nasport = (
        (
            await db.execute(
                select(NasPort)
                .where(
                    NasPort.username == username,
                )
                .order_by(NasPort.last_seen.desc())
            )
        )
        .scalars()
        .first()
    )

    if recent_nasport:
        coa = CoA(recent_nasport)

        background_tasks.add_task(coa.send_packet)

    response: AuthResponse = {
        "id": existing_user.id,
        "username": existing_user.username,
        "enabled": input_auth.enabled,
        "vlan": input_auth.vlan,
    }

    return response
