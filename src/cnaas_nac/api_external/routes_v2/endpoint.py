from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi_filter import FilterDepends
from netutils.mac import is_valid_mac
from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.coa import CoA
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.rbac_filter import apply_group_filter
from cnaas_nac.core.security import User, get_current_user
from cnaas_nac.filters.endpoint import EndpointFilter
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.schemas.endpoint import EndpointCreate, EndpointResponse, EndpointUpdate

logger = get_logger()

router = APIRouter(prefix="/endpoint", tags=["endpoint"])


@router.get("", response_model=list[EndpointResponse])
async def get_endpoints(
    endpoint_filter: Annotated[EndpointFilter, FilterDepends(EndpointFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get endpoints.
    """

    query = select(Endpoint)
    query = endpoint_filter.filter(query)
    query = endpoint_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)
    query = apply_group_filter(query, Endpoint, current_user.group_ids)

    count_query = select(func.count()).select_from(Endpoint)
    count_query = endpoint_filter.filter(count_query)
    count_query = apply_group_filter(count_query, Endpoint, current_user.group_ids)

    total_count = (await db.execute(count_query)).scalar_one()

    response.headers["X-Total-Count"] = str(total_count)

    return (await db.execute(query)).scalars().all()


@router.post("", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
async def post_endpoint(
    input_endpoint: EndpointCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
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
        raise RequestValidationError(
            [{"loc": ["body", "username"], "msg": "Endpoint already exists."}]
        )

    endpoint = Endpoint(**input_endpoint.model_dump(), state=EndpointState.PENDING)

    db.add(endpoint)

    await db.commit()
    await db.refresh(endpoint)

    return endpoint


@router.get("/{id}", response_model=EndpointResponse)
async def read_username(
    endpoint_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Retrieve individual endpoint.
    """

    stmt = select(Endpoint).where(Endpoint.id == endpoint_id)
    stmt = apply_group_filter(stmt, Endpoint, current_user.group_ids)

    endpoint = (await db.execute(stmt)).scalar_one_or_none()

    if not endpoint:
        raise NotFound()

    return endpoint


@router.put("/{id}", response_model=EndpointResponse)
async def put_user(
    endpoint_id: Annotated[int, Path(alias="id")],
    input_endpoint: EndpointUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Put user.
    """

    stmt = select(Endpoint).where(Endpoint.id == endpoint_id)
    stmt = apply_group_filter(stmt, Endpoint, current_user.group_ids)

    existing_endpoint = (await db.execute(stmt)).scalar_one_or_none()

    if not existing_endpoint:
        raise NotFound()

    # EAP users cannot be set to a Endpoint group.

    if not is_valid_mac(existing_endpoint.username) and input_endpoint.group_id:
        raise RequestValidationError(
            [
                {
                    "loc": ["body", "group_id"],
                    "msg": "EAP users cannot be set to an endpoint group.",
                }
            ]
        )

    changed_attributes = []

    for k, v in input_endpoint.model_dump().items():
        if getattr(existing_endpoint, k) != v:
            changed_attributes.append(k)
            setattr(existing_endpoint, k, v)

    # Only set to pending when changing group_id.
    if inspect(existing_endpoint).modified and "group_id" in changed_attributes:
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

    if recent_nasport and "group_id" in changed_attributes:
        coa = CoA(recent_nasport)

        background_tasks.add_task(coa.send_packet)

    return existing_endpoint


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    endpoint_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> None:
    """
    Delete endpoint.
    """

    stmt = select(Endpoint).where(Endpoint.id == endpoint_id)
    stmt = apply_group_filter(stmt, Endpoint, current_user.group_ids)

    endpoint = (await db.execute(stmt)).scalar_one_or_none()

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
