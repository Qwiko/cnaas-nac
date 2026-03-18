from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Response, status
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.rbac_filter import apply_group_filter
from cnaas_nac.core.security import User, get_current_user
from cnaas_nac.filters.nas_port import NasPortFilter
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.schemas.nas_port import NasPortResponse

router = APIRouter(prefix="/nas_port", tags=["nas_port"])


@router.get("", response_model=list[NasPortResponse])
async def get_nas_ports(
    nas_port_filter: Annotated[NasPortFilter, FilterDepends(NasPortFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get nas ports.
    """
    query = select(NasPort)
    query = nas_port_filter.filter(query)
    query = nas_port_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)
    query = apply_group_filter(query, NasPort, current_user.group_ids)

    count_query = select(func.count()).select_from(NasPort)
    count_query = nas_port_filter.filter(count_query)
    count_query = apply_group_filter(count_query, NasPort, current_user.group_ids)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nas_port(
    nas_port_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete nas_port.
    """

    stmt = select(NasPort).where(NasPort.id == nas_port_id)
    stmt = apply_group_filter(stmt, NasPort, current_user.group_ids)

    nas_port = (await db.execute(stmt)).scalar_one_or_none()

    if not nas_port:
        raise NotFound()

    await db.delete(nas_port)

    await db.commit()

    return None
