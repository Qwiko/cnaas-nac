from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi_filter import FilterDepends
from sqlalchemy import func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import INET

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.security import get_current_user
from cnaas_nac.filters.nas import NasFilter
from cnaas_nac.models.nas import Nas
from cnaas_nac.schemas.nas import NasCreateUpdate, NasResponse, NasOne

router = APIRouter(prefix="/radius_client", tags=["radius_client"])


@router.get("", response_model=list[NasResponse])
async def get_radius_client(
    nas_filter: Annotated[NasFilter, FilterDepends(NasFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get radius clients.
    """
    query = select(Nas)
    query = nas_filter.filter(query)
    query = nas_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(Nas)
    count_query = nas_filter.filter(count_query)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.post("", response_model=NasOne, status_code=status.HTTP_201_CREATED)
async def post_radius_client(
    input_radius_client: NasCreateUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Create new radius client
    """

    existing_radius_client_name = (
        await db.execute(
            select(Nas).where(
                Nas.name == input_radius_client.name,
            )
        )
    ).scalar_one_or_none()

    if existing_radius_client_name:
        raise RequestValidationError(
            [{"loc": ["body", "name"], "msg": "Another already exists."}]
        )

    existing_radius_client_network = (
        await db.execute(
            select(Nas).where(
                literal(input_radius_client.network).cast(INET).op("<<=")(Nas.network)
            )
        )
    ).scalar_one_or_none()

    if existing_radius_client_network:
        raise RequestValidationError(
            [{"loc": ["body", "network"], "msg": "This network is already used."}]
        )

    nas = Nas(**input_radius_client.model_dump())

    db.add(nas)

    await db.commit()
    await db.refresh(nas)

    return nas


@router.get("/{id}", response_model=NasOne)
async def read_radius_client(
    nas_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Retrieve individual radius client.
    """

    nas = (await db.execute(select(Nas).where(Nas.id == nas_id))).scalar_one_or_none()

    if not nas:
        raise NotFound()

    return nas


@router.put("/{id}", response_model=NasOne)
async def put_radius_client(
    nas_id: Annotated[int, Path(alias="id")],
    input_nas: NasCreateUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Put radius client.
    """

    existing_nas = (
        await db.execute(select(Nas).where(Nas.id == nas_id))
    ).scalar_one_or_none()

    if not existing_nas:
        raise NotFound()

    for k, v in input_nas.model_dump().items():
        if getattr(existing_nas, k) != v:
            setattr(existing_nas, k, v)

    await db.commit()
    await db.refresh(existing_nas)

    return existing_nas


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_radius_client(
    nas_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """
    Delete nas.
    """

    nas = (await db.execute(select(Nas).where(Nas.id == nas_id))).scalar_one_or_none()

    if not nas:
        raise NotFound()

    await db.delete(nas)

    await db.commit()

    return None
