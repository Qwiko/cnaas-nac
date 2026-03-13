from typing import Annotated, Any
from fastapi import Path, Response, status

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.security import get_current_user
from cnaas_nac.models.radpostauth import RadPostAuth
from cnaas_nac.schemas.radportauth import RadPostAuthLog
from cnaas_nac.filters.logs import AuthenticationFilter

router = APIRouter(prefix="", tags=["logs"])


@router.get("/authentication", response_model=list[RadPostAuthLog])
async def get_authentications(
    authentication_filter: Annotated[
        AuthenticationFilter, FilterDepends(AuthenticationFilter)
    ],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get authentications.
    """

    query = select(RadPostAuth)
    query = authentication_filter.filter(query)
    query = authentication_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(RadPostAuth)
    count_query = authentication_filter.filter(count_query)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.get("/authentication/{id}", response_model=RadPostAuthLog)
async def get_authentication(
    authentication_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Get authentication.
    """

    authentication = (
        await db.execute(select(RadPostAuth).where(RadPostAuth.id == authentication_id))
    ).scalar_one_or_none()

    if not authentication:
        raise NotFound()

    return authentication


@router.delete("/authentication/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_authentication(
    authentication_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """
    Delete authentication.
    """

    authentication = (
        await db.execute(select(RadPostAuth).where(RadPostAuth.id == authentication_id))
    ).scalar_one_or_none()

    if not authentication:
        raise NotFound()

    await db.delete(authentication)

    await db.commit()

    return None
