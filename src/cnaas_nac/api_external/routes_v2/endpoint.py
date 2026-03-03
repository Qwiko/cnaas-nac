from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi_filter import FilterDepends
from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.coa import CoA
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.filters.endpoint import EndpointFilter
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.schemas.endpoint import EndpointCreate, EndpointUpdate, EndpointResponse

logger = get_logger()

router = APIRouter(prefix="/endpoint", tags=["endpoint"])


@router.get("", response_model=list[EndpointResponse])
async def get_endpoints(
    endpoint_filter: Annotated[EndpointFilter, FilterDepends(EndpointFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Get endpoints.
    """

    query = select(Endpoint)
    query = endpoint_filter.filter(query)
    query = endpoint_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(Endpoint)
    count_query = endpoint_filter.filter(count_query)

    total_count = (await db.execute(count_query)).scalar_one()

    response.headers["X-Total-Count"] = str(total_count)

    if total_count == 0:
        response.status_code = status.HTTP_404_NOT_FOUND

    return (await db.execute(query)).scalars().all()


@router.post("", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
async def post_endpoint(
    input_endpoint: EndpointCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Create new MAB endpoint
    Only allowed to create MAB endpoints. EAP users are managed through policies.
    """

    existing_endpoint = (
        await db.execute(
            select(Endpoint).where(
                Endpoint.username == input_endpoint.username,
                Endpoint.calling_station_id == input_endpoint.calling_station_id,
            )
        )
    ).scalar_one_or_none()
    if existing_endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Endpoint already exists."
        )

    endpoint = Endpoint(**input_endpoint.model_dump(), state=EndpointState.PENDING)

    db.add(endpoint)

    await db.commit()
    return endpoint


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def read_username(
    endpoint_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    response: Response,
) -> Any:
    """
    Retrieve individual endpoint.
    """

    endpoint = (
        await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    ).scalar_one_or_none()

    if not endpoint:
        raise NotFound()

    return endpoint


@router.put("/{endpoint_id}", response_model=EndpointResponse)
async def put_user(
    endpoint_id: int,
    input_endpoint: EndpointUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Put user.
    """

    existing_endpoint = (
        await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    ).scalar_one_or_none()
    if not existing_endpoint:
        raise NotFound()

    for k, v in input_endpoint.model_dump().items():
        if getattr(existing_endpoint, k) != v:
            setattr(existing_endpoint, k, v)

    if inspect(existing_endpoint).modified:
        existing_endpoint.state = EndpointState.PENDING
    else:
        existing_endpoint.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(existing_endpoint)

    recent_nasport = (
        (
            await db.execute(
                select(NasPort)
                .where(
                    NasPort.username == existing_endpoint.username,
                    NasPort.calling_station_id == existing_endpoint.calling_station_id,
                )
                .order_by(NasPort.updated_at.desc())
            )
        )
        .scalars()
        .first()
    )

    # TODO: Check if another endpoint have connected on this port after this endpoint.
    # Then we should not bounce the port and assume the endpoint is already disconnected.

    if recent_nasport:
        coa = CoA(recent_nasport)

        background_tasks.add_task(coa.send_packet)

    return existing_endpoint


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    endpoint_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks,
) -> None:
    """
    Delete endpoint.
    """

    endpoint = (
        await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    ).scalar_one_or_none()

    if not endpoint:
        raise NotFound()

    recent_nasport = (
        (
            await db.execute(
                select(NasPort)
                .where(
                    NasPort.username == endpoint.username,
                    NasPort.calling_station_id == endpoint.calling_station_id,
                )
                .order_by(NasPort.updated_at.desc())
            )
        )
        .scalars()
        .first()
    )

    # TODO: Check if another endpoint have connected on this port after this endpoint.
    # Then we should not bounce the port and assume the endpoint is already disconnected.

    if recent_nasport:
        # Move this object to outside the session.
        db.expunge(recent_nasport)
        coa = CoA(recent_nasport)

        background_tasks.add_task(coa.send_packet)

    await db.delete(endpoint)

    await db.commit()

    return None
