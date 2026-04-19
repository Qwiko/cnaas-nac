from datetime import datetime, timedelta
from typing import AsyncIterator, Callable
from unittest.mock import patch

import pytest
from fastapi.concurrency import asynccontextmanager
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.scheduled_tasks.prune_radacct import prune_radacct
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.radacct import RadAcct

pytestmark = pytest.mark.anyio


async def create_radacct(
    db: AsyncSession,
    start: int,
    stop: int,
    prune_func: Callable,
) -> tuple[int, int]:
    now = datetime.now()
    for i in range(start, stop):
        mac = f"AA:BB:{i * 1 % 256:02X}:{(i * 2) % 256:02X}:{(i * 3) % 256:02X}:{(i * 4) % 256:02X}".lower()

        auth_date = now - timedelta(days=i)
        endpoint = Endpoint(
            username=mac, calling_station_id=mac, state=EndpointState.DISCOVERED
        )
        rad_post = RadAcct(
            username=mac,
            calling_station_id=mac,
            nas_ip_address="127.0.0.1",
            acct_session_id=str(i),
            acct_unique_id=str(i),
            acct_stop_time=auth_date,
        )
        db.add(endpoint)
        db.add(rad_post)

    await db.commit()

    pre_count = (
        await db.execute(select(func.count()).select_from(RadAcct))
    ).scalar_one()

    @asynccontextmanager
    async def override_session_factory() -> AsyncIterator[AsyncSession]:
        yield db

    with patch(
        "cnaas_nac.core.scheduled_tasks.prune_radacct.async_session_factory",
        new=override_session_factory,
    ):
        await prune_func()

    post_count = (
        await db.execute(select(func.count()).select_from(RadAcct))
    ).scalar_one()

    return pre_count, post_count


async def test_prune_radacct(db: AsyncSession) -> None:
    pre_count, post_count = await create_radacct(db, 0, 91, prune_radacct)

    assert pre_count - post_count == 1


async def test_prune_radacct_without_endpoint(db: AsyncSession) -> None:
    """
    RadAcct without an associated endpoint should be deleted instantly.
    In cases where an ongoing session is terminated when deleting an endpoint
    An accounting stop will come in after the endpoint have been deleted and will be floating in the db if we dont prune it.
    """
    mac1 = "00:00:00:00:00:00"
    mac2 = "00:00:00:00:00:01"
    auth_date = datetime.now()
    endpoint = Endpoint(
        username=mac1, calling_station_id=mac1, state=EndpointState.DISCOVERED
    )
    rad_post1 = RadAcct(
        username=mac1,
        calling_station_id=mac1,
        nas_ip_address="127.0.0.1",
        acct_session_id="1",
        acct_unique_id="1",
        acct_stop_time=auth_date,
    )
    rad_post2 = RadAcct(
        username=mac2,
        calling_station_id=mac2,
        nas_ip_address="127.0.0.1",
        acct_session_id="2",
        acct_unique_id="2",
        acct_stop_time=auth_date,
    )
    db.add(endpoint)
    db.add(rad_post1)
    db.add(rad_post2)

    await db.commit()

    pre_count = (
        await db.execute(select(func.count()).select_from(RadAcct))
    ).scalar_one()

    @asynccontextmanager
    async def override_session_factory() -> AsyncIterator[AsyncSession]:
        yield db

    with patch(
        "cnaas_nac.core.scheduled_tasks.prune_radacct.async_session_factory",
        new=override_session_factory,
    ):
        await prune_radacct()

    post_count = (
        await db.execute(select(func.count()).select_from(RadAcct))
    ).scalar_one()

    assert pre_count == 2
    assert post_count == 1
    assert pre_count - post_count == 1
