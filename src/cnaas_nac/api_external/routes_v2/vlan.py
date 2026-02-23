from typing import Annotated, Any
from fastapi import Response

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.db import get_async_session
from cnaas_nac.models.user import User
from cnaas_nac.schemas.generic import VlanID, Username

router = APIRouter(prefix="/vlan", tags=["vlan"])


@router.get("", response_model=list[VlanID])
async def get_vlans(
    db: Annotated[AsyncSession, Depends(get_async_session)], response: Response
) -> Any:
    """
    Get vlans.
    """

    vlans = (await db.execute(select(User.vlan).distinct())).scalars().all()

    if not vlans:
        raise NotFound()

    response.headers["X-Total-Count"] = str(len(vlans))

    return vlans


@router.get("/{vlan_id}", response_model=list[Username])
async def get_vlans_name(
    vlan_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Get vlans.
    """

    users = (
        (
            await db.execute(
                select(User.username).where(
                    User.vlan == vlan_id,
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
