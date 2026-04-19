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
from cnaas_nac.filters.logs import AccountingFilter
from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.schemas.radacct import RadAcctLog, RadAcctLogFull

router = APIRouter(prefix="", tags=["logs"])


@router.get("/accounting", response_model=list[RadAcctLog])
async def get_accountings(
    accounting_filter: Annotated[AccountingFilter, FilterDepends(AccountingFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get accountings.
    """
    query = select(RadAcct)
    query = accounting_filter.filter(query) # type: ignore[assignment]
    query = accounting_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)
    query = apply_group_filter(query, RadAcct, current_user)

    count_query = select(func.count()).select_from(RadAcct)
    count_query = accounting_filter.filter(count_query) # type: ignore[assignment]
    count_query = apply_group_filter(count_query, RadAcct, current_user) # type: ignore[misc]

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.get("/accounting/{id}", response_model=RadAcctLogFull)
async def get_accounting(
    accounting_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Any:
    """
    Get accounting.
    """

    stmt = select(RadAcct).where(RadAcct.id == accounting_id)
    stmt = apply_group_filter(stmt, RadAcct, current_user)

    accounting = (await db.execute(stmt)).scalar_one_or_none()

    if not accounting:
        raise NotFound()

    return accounting


@router.delete("/accounting/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accounting(
    accounting_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete accounting.
    """

    stmt = select(RadAcct).where(RadAcct.id == accounting_id)
    stmt = apply_group_filter(stmt, RadAcct, current_user)

    accounting = (await db.execute(stmt)).scalar_one_or_none()

    if not accounting:
        raise NotFound()

    await db.delete(accounting)

    await db.commit()

    return None
