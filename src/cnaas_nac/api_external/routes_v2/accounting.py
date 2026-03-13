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
from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.schemas.radacct import RadAcctLog, RadAcctLogFull
from cnaas_nac.filters.logs import AccountingFilter

router = APIRouter(prefix="", tags=["logs"])


@router.get("/accounting", response_model=list[RadAcctLog])
async def get_accountings(
    accounting_filter: Annotated[AccountingFilter, FilterDepends(AccountingFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get accountings.
    """
    query = select(RadAcct)
    query = accounting_filter.filter(query)
    query = accounting_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(RadAcct)
    count_query = accounting_filter.filter(count_query)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.get("/accounting/{id}", response_model=RadAcctLogFull)
async def get_accounting(
    accounting_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Get accounting.
    """

    accounting = (
        await db.execute(select(RadAcct).where(RadAcct.id == accounting_id))
    ).scalar_one_or_none()

    if not accounting:
        raise NotFound()

    return accounting


@router.delete("/accounting/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accounting(
    accounting_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """
    Delete accounting.
    """

    accounting = (
        await db.execute(select(RadAcct).where(RadAcct.id == accounting_id))
    ).scalar_one_or_none()

    if not accounting:
        raise NotFound()

    await db.delete(accounting)

    await db.commit()

    return None
