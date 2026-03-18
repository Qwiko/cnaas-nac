from typing import Annotated, Any
from fastapi import Path, Response, status

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.rbac_filter import apply_group_filter
from cnaas_nac.core.security import User, get_current_user
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
    current_user: Annotated[User, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get authentications.
    """

    query = select(RadPostAuth)
    query = authentication_filter.filter(query)
    query = authentication_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)
    query = apply_group_filter(query, RadPostAuth, current_user.group_ids)

    count_query = select(func.count()).select_from(RadPostAuth)
    count_query = authentication_filter.filter(count_query)
    count_query = apply_group_filter(count_query, RadPostAuth, current_user.group_ids)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.get("/authentication/{id}", response_model=RadPostAuthLog)
async def get_authentication(
    authentication_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Any:
    """
    Get authentication.
    """

    stmt = select(RadPostAuth).where(RadPostAuth.id == authentication_id)
    stmt = apply_group_filter(stmt, RadPostAuth, current_user.group_ids)

    authentication = (await db.execute(stmt)).scalar_one_or_none()

    if not authentication:
        raise NotFound()

    return authentication


@router.delete("/authentication/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_authentication(
    authentication_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete authentication.
    """

    stmt = select(RadPostAuth).where(RadPostAuth.id == authentication_id)
    stmt = apply_group_filter(stmt, RadPostAuth, current_user.group_ids)

    authentication = (await db.execute(stmt)).scalar_one_or_none()

    if not authentication:
        raise NotFound()

    await db.delete(authentication)

    await db.commit()

    return None
