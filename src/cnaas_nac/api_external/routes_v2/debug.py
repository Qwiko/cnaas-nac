from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
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


# @router.get("", response_model=DebugBase)
# async def get_debug(
#     db: Annotated[AsyncSession, Depends(get_async_session)],
#     current_user: Annotated[User, Depends(get_current_user)],
# ) -> Any:
#     """
#     Get active debugging.
#     """

#     debug_event = RadiusAdminEvent(
#         command=RadiusCommand.DEBUG_START,
#         payload=input_debug.model_dump(exclude_unset=True),
#     )

#     db.add(debug_event)
#     await db.commit()

#     return debug_event.payload


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


@router.delete("/logs", status_code=status.HTTP_204_NO_CONTENT)
async def delete_debug_logs(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Clear debug logs.
    """

    debug_event = RadiusAdminEvent(command=RadiusCommand.DEBUG_CLEAR)

    db.add(debug_event)
    await db.commit()
