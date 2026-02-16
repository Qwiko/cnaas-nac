from typing import Annotated, Any
from fastapi import status, Response

from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.db import get_async_session
from cnaas_nac.models.radreply import RadReply


router = APIRouter(prefix="/vlans", tags=["vlans"])


@router.get("", response_model=list[int])
async def get_vlans(
    db: Annotated[AsyncSession, Depends(get_async_session)], response: Response
) -> Any:
    """
    Get vlans.
    """

    vlans = (
        (
            await db.execute(
                select(RadReply.value).where(
                    RadReply.attribute == "Tunnel-Private-Group-Id"
                )
            )
        )
        .scalars()
        .all()
    )

    if not vlans:
        raise NotFound()

    response.headers["X-Total-Count"] = str(len(vlans))

    return vlans

@router.get("/{vlan_id}", response_model=list[str])
async def get_vlans_name(
    vlan_id: str,
    db: Annotated[AsyncSession, Depends(get_async_session)], response: Response
) -> Any:
    """
    Get vlans.
    """

    users = (
        (
            await db.execute(
                select(RadReply.username).where(
                    RadReply.attribute == "Tunnel-Private-Group-Id", RadReply.value == vlan_id
                )
            )
        )
        .scalars()
        .all()
    )

    if not users:
        raise NotFound()

    response.headers["X-Total-Count"] = str(len(users))

    return users