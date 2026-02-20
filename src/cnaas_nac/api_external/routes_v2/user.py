from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.coa import CoA
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.logging import get_logger
from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.radcheck import RadCheck
from cnaas_nac.models.radreply import RadReply
from cnaas_nac.schemas.auth import AuthCreate, AuthResponse, AuthUpdate
from cnaas_nac.schemas.generic import Username

logger = get_logger()

router = APIRouter(prefix="/user", tags=["user"])


@router.get("", response_model=list[AuthResponse])
async def read_user(
    db: Annotated[AsyncSession, Depends(get_async_session)], response: Response
) -> Any:
    """
    Retrieve user.
    """

    users = (await db.execute(select(RadCheck))).scalars().all()

    if not users:
        raise NotFound()

    response.headers["X-Total-Count"] = str(len(users))

    return users


@router.post("", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def post_user(
    input_user: AuthCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Post user.
    """

    existing_user = (
        await db.execute(
            select(RadCheck).where(RadCheck.username == input_user.username)
        )
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    user = RadCheck(**input_user.model_dump())

    tunnel_id = RadReply(
        username=input_user.username,
        attribute="Tunnel-Private-Group-Id",
        op=":=",
        value=str(input_user.vlan),
    )
    tunnel_medium = RadReply(
        username=input_user.username,
        attribute="Tunnel-Medium-Type",
        op=":=",
        value="IEEE-802",
    )

    db.add(user)
    db.add(tunnel_id)
    db.add(tunnel_medium)
    await db.commit()
    return user


@router.get("/{username}", response_model=AuthResponse)
async def read_username(
    username: Username,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Retrieve individual user.
    """

    user = (
        await db.execute(select(RadCheck).where(RadCheck.username == username))
    ).scalar_one_or_none()

    if not user:
        raise NotFound()

    return user


@router.put("/{username}", response_model=AuthResponse)
async def put_user(
    username: Username,
    input_user: AuthUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Put user.
    """

    existing_user = (
        await db.execute(select(RadCheck).where(RadCheck.username == username))
    ).scalar_one_or_none()
    if not existing_user:
        raise NotFound()

    for k, v in input_user.model_dump().items():
        if getattr(existing_user, k) != v:
            setattr(existing_user, k, v)

    await db.commit()
    await db.refresh(existing_user)

    recent_nasport = (
        (
            await db.execute(
                select(NasPort)
                .where(
                    NasPort.username == username,
                )
                .order_by(NasPort.updated_at.desc())
            )
        )
        .scalars()
        .first()
    )

    # TODO: Check if another user have connected on this port after this username.
    # Then we should not bounce the port and assume the username is already disconnected.

    if recent_nasport:
        coa = CoA(recent_nasport)

        background_tasks.add_task(coa.send_packet)

    return existing_user


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: Username,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks,
) -> None:
    """
    Delete user.
    """

    user = (
        await db.execute(select(RadCheck).where(RadCheck.username == username))
    ).scalar_one_or_none()

    if not user:
        raise NotFound()

    recent_nasport = (
        (
            await db.execute(
                select(NasPort)
                .where(
                    NasPort.username == username,
                )
                .order_by(NasPort.updated_at.desc())
            )
        )
        .scalars()
        .first()
    )

    # TODO: Check if another user have connected on this port after this username.
    # Then we should not bounce the port and assume the username is already disconnected.

    if recent_nasport:
        # Move this object to outside the session.
        db.expunge(recent_nasport)
        coa = CoA(recent_nasport)

        background_tasks.add_task(coa.send_packet)

    await db.delete(user)

    await db.commit()

    return None
