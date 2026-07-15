from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.security import User, get_current_user
from cnaas_nac.models.radiusadminevent import (
    RadiusAdminEvent,
    RadiusCommand,
    RadiusDebugLog,
)
from cnaas_nac.schemas.debug import DebugBase, DebugLog

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def post_debug(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    input_debug: DebugBase,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Start debugging.
    """

    debug_event = RadiusAdminEvent(
        command=RadiusCommand.DEBUG_START,
        payload=input_debug.model_dump(exclude_unset=True),
    )

    db.add(debug_event)
    await db.commit()


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


@router.get("/logs", response_model=list[DebugLog])
async def get_debug_logs(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Any:
    """
    Get debug logs.
    """

    debug_logs = (await db.execute(select(RadiusDebugLog))).scalars().all()

    response.headers["X-Total-Count"] = str(len(debug_logs))

    return debug_logs
