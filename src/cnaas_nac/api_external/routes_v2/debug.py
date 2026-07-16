import asyncio
from collections import deque
from collections.abc import AsyncIterable
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import async_session_factory, get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.security import User, get_current_user
from cnaas_nac.models.radiusadminevent import (
    RadiusAdminEvent,
    RadiusCommand,
    RadiusDebugLog,
)
from cnaas_nac.schemas.debug import DebugBase, DebugLog

router = APIRouter(prefix="/debug", tags=["debug"])


class CustomDebugBase(DebugBase):
    id: int


@router.get("", response_model=Optional[CustomDebugBase])
async def get_debug(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Any:
    """
    Get active debugging.
    """

    stmt = (
        select(RadiusAdminEvent)
        .where(
            RadiusAdminEvent.command.in_(
                [RadiusCommand.DEBUG_STOP, RadiusCommand.DEBUG_START]
            )
        )
        .limit(100)
        .distinct()
        .order_by(RadiusAdminEvent.created_at.desc())
    )

    event = (await db.scalars(stmt)).first()

    if not event or not event.payload:
        raise NotFound()

    return {"id": event.id, **event.payload}


class CustomDebugResponse(BaseModel):
    id: int


@router.post(
    "", response_model=CustomDebugResponse, status_code=status.HTTP_201_CREATED
)
async def post_debug(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    input_debug: DebugBase,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Any:
    """
    Start debugging.
    """

    debug_event = RadiusAdminEvent(
        command=RadiusCommand.DEBUG_START,
        payload=input_debug.model_dump(exclude_unset=True, exclude_none=True),
    )

    db.add(debug_event)
    await db.commit()

    return debug_event


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_debug(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Stop debugging.
    """

    debug_event = RadiusAdminEvent(command=RadiusCommand.DEBUG_STOP)

    db.add(debug_event)
    await db.commit()


@router.get("/logs", response_class=EventSourceResponse)
async def get_debug_logs(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AsyncIterable[DebugLog]:
    """Stream debug logs"""

    seen_ids: deque[int] = deque(maxlen=5000)

    try:
        while not await request.is_disconnected():
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=5)

            async with async_session_factory() as db:
                stmt = (
                    select(RadiusDebugLog)
                    .where(RadiusDebugLog.created_at >= cutoff)
                    .order_by(
                        RadiusDebugLog.created_at,
                        RadiusDebugLog.id,
                    )
                    .limit(5000)
                )

                result = await db.execute(stmt)

                for log in result.scalars():
                    if log.id in seen_ids:
                        continue

                    seen_ids.append(log.id)

                    yield log # type: ignore

            await asyncio.sleep(1)

    except asyncio.CancelledError:
        raise


@router.delete("/logs", status_code=status.HTTP_204_NO_CONTENT)
async def delete_debug_logs(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Clear debug logs.
    """

    # This clears the actual logs file on radius
    debug_event = RadiusAdminEvent(command=RadiusCommand.DEBUG_CLEAR)

    # Delete all logs
    await db.execute(delete(RadiusDebugLog))

    db.add(debug_event)
    await db.commit()
