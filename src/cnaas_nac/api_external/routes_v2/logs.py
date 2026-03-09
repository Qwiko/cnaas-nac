from typing import Annotated, Any
from fastapi import Response

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.security import get_current_user
from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth
from cnaas_nac.schemas.logs import RadAcctLog, RadAcctLogFull, RadPostAuthLog
from cnaas_nac.filters.logs import AccountingLogFilter, RadPostLogFilter

router = APIRouter(prefix="", tags=["logs"])


@router.get("/accounting_log", response_model=list[RadAcctLog])
async def get_accounting_logs(
    acct_log_filter: Annotated[AccountingLogFilter, FilterDepends(AccountingLogFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get accounting logs.
    """
    query = select(RadAcct)
    query = acct_log_filter.filter(query)
    query = acct_log_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(RadAcct)
    count_query = acct_log_filter.filter(count_query)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.get("/accounting_log/{accounting_log_id}", response_model=RadAcctLogFull)
async def get_accounting_log(
    accounting_log_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Get accounting log.
    """

    accounting_log = (
        await db.execute(select(RadAcct).where(RadAcct.id == accounting_log_id))
    ).scalar_one_or_none()

    if not accounting_log:
        raise NotFound()

    return accounting_log


@router.get("/authentication_log", response_model=list[RadPostAuthLog])
async def get_authentication_logs(
    post_auth_log_filter: Annotated[RadPostLogFilter, FilterDepends(RadPostLogFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get authentication logs.
    """

    query = select(RadPostAuth)
    query = post_auth_log_filter.filter(query)
    query = post_auth_log_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(RadPostAuth)
    count_query = post_auth_log_filter.filter(count_query)

    response.headers["X-Total-Count"] = str(
        (await db.execute(count_query)).scalar_one()
    )

    return (await db.execute(query)).scalars().all()


@router.get(
    "/authentication_log/{authentication_log_id}", response_model=RadPostAuthLog
)
async def get_authentication_log(
    authentication_log_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Get accounting log.
    """

    authentication_log = (
        await db.execute(select(RadAcct).where(RadAcct.id == authentication_log_id))
    ).scalar_one_or_none()

    if not authentication_log:
        raise NotFound()

    return authentication_log
