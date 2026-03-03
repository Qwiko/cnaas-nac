from typing import Annotated, Any
from fastapi import HTTPException, status, Response

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.security import get_current_user
from cnaas_nac.filters.endpoint_group import EndpointGroupFilter
from cnaas_nac.models.endpoint import EndpointGroup
from cnaas_nac.schemas.endpoint_group import EndpointGroupBase, EndpointGroupResponse

router = APIRouter(prefix="/endpoint_group", tags=["endpoint"])


@router.get("", response_model=list[EndpointGroupResponse])
async def get_endpoint_groups(
    endpoint_group_filter: Annotated[
        EndpointGroupFilter, FilterDepends(EndpointGroupFilter)
    ],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get endpoint groups.
    """

    query = select(EndpointGroup)
    query = endpoint_group_filter.filter(query)
    query = endpoint_group_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(EndpointGroup)
    count_query = endpoint_group_filter.filter(count_query)

    total_count = (await db.execute(count_query)).scalar_one()

    response.headers["X-Total-Count"] = str(total_count)

    if total_count == 0:
        response.status_code = status.HTTP_404_NOT_FOUND

    return (await db.execute(query)).scalars().all()


@router.post(
    "", response_model=EndpointGroupResponse, status_code=status.HTTP_201_CREATED
)
async def post_endpoint_group(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    input_group: EndpointGroupBase,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Post endpoint groups.
    """
    existing_group = (
        await db.execute(
            select(EndpointGroup).where(EndpointGroup.name == input_group.name)
        )
    ).scalar_one_or_none()
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint group already exists.",
        )

    group = EndpointGroup(**input_group.model_dump())

    db.add(group)
    await db.commit()

    return group


@router.get("/{group_id}", response_model=EndpointGroupResponse)
async def get_endpoint_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Get group.
    """

    endpoint_group = (
        await db.execute(select(EndpointGroup).where(EndpointGroup.id == group_id))
    ).scalar_one_or_none()

    if not endpoint_group:
        raise NotFound()

    return endpoint_group


@router.put("/{group_id}", response_model=EndpointGroupResponse)
async def put_endpoint_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    input_group: EndpointGroupBase,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Put group.
    """

    existing_group = (
        await db.execute(select(EndpointGroup).where(EndpointGroup.id == group_id))
    ).scalar_one_or_none()

    if not existing_group:
        raise NotFound()

    for k, v in input_group.model_dump().items():
        if getattr(existing_group, k) != v:
            setattr(existing_group, k, v)

    await db.commit()

    return existing_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """
    Delete group.
    """

    endpoint_group = (
        await db.execute(select(EndpointGroup).where(EndpointGroup.id == group_id))
    ).scalar_one_or_none()

    if not endpoint_group:
        raise NotFound()

    await db.delete(endpoint_group)

    await db.commit()

    return None
