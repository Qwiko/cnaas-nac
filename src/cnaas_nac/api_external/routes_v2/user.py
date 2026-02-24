from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.coa import CoA
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.filters.user import UserFilter
from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.user import User
from cnaas_nac.schemas.generic import Username
from cnaas_nac.schemas.user import AuthCreate, AuthResponse, AuthUpdate

logger = get_logger()

router = APIRouter(prefix="/user", tags=["user"])


@router.get("", response_model=list[AuthResponse])
async def read_user(
    user_filter: Annotated[UserFilter, FilterDepends(UserFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Get users.
    """

    query = select(User)
    query = user_filter.filter(query)
    query = user_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(User)
    count_query = user_filter.filter(count_query)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


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
        await db.execute(select(User).where(User.username == input_user.username))
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    user = User(**input_user.model_dump())

    db.add(user)

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
        await db.execute(select(User).where(User.username == username))
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
        await db.execute(select(User).where(User.username == username))
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
        await db.execute(select(User).where(User.username == username))
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
