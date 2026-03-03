from typing import Annotated, Any
from fastapi import Response

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.security import get_current_user
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.schemas.nas_port import NasPortResponse
from cnaas_nac.filters.nas_port import NasPortFilter

router = APIRouter(prefix="/nas_port", tags=["nas_port"])


@router.get("", response_model=list[NasPortResponse])
async def get_nas_ports(
    nas_port_filter: Annotated[NasPortFilter, FilterDepends(NasPortFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get nas ports.
    """
    query = select(NasPort)
    query = nas_port_filter.filter(query)
    query = nas_port_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(NasPort)
    count_query = nas_port_filter.filter(count_query)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()
