from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.security import get_current_user
from cnaas_nac.models.policy import PolicyReply
from cnaas_nac.schemas.vlan import VlanResponse

router = APIRouter(prefix="/vlan", tags=["vlan"])


@router.get("", response_model=list[VlanResponse])
async def get_vlans(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
    current_user=Depends(get_current_user),
) -> Any:
    """
    Get vlans.
    """

    vlans = (
        (
            await db.execute(
                select(PolicyReply.value)
                .where(PolicyReply.attribute == "Tunnel-Private-Group-Id")
                .distinct()
            )
        )
        .scalars()
        .all()
    )

    response.headers["X-Total-Count"] = str(len(vlans))

    return [{"vlan": int(vlan)} for vlan in vlans]


@router.get("/{vlan_id}", response_model=VlanResponse)
async def get_vlans_id(
    vlan_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user=Depends(get_current_user),
) -> Any:
    """
    Get vlan.
    """

    vlan = (
        await db.execute(
            select(PolicyReply.value)
            .where(PolicyReply.attribute == "Tunnel-Private-Group-Id")
            .distinct()
        )
    ).scalar_one_or_none()

    if not vlan:
        raise NotFound()

    return {"vlan": int(vlan)}
