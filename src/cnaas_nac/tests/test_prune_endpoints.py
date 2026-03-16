from datetime import datetime, timedelta
from typing import Callable
from unittest.mock import patch

from fastapi.concurrency import asynccontextmanager
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.core.scheduled_tasks.prune_endpoints import (
    prune_discovered_endpoints,
    prune_rejected_endpoints,
    prune_pending_endpoints,
    prune_authorized_endpoints,
)
from cnaas_nac.models.radpostauth import RadPostAuth

pytestmark = pytest.mark.anyio


async def create_endpoints(
    db: AsyncSession,
    endpoint_state: EndpointState,
    start: int,
    stop: int,
    prune_func: Callable,
) -> tuple[int, int]:
    now = datetime.now()
    for i in range(start, stop):
        mac = f"AA:BB:{i * 1 % 256:02X}:{(i * 2) % 256:02X}:{(i * 3) % 256:02X}:{(i * 4) % 256:02X}".lower()

        auth_date = now - timedelta(days=i)

        endpoint = Endpoint(username=mac, calling_station_id=mac, state=endpoint_state)
        rad_post = RadPostAuth(
            username=mac,
            calling_station_id=mac,
            nas_ip_address="127.0.0.1",
            auth_date=auth_date,
        )
        db.add(endpoint)
        db.add(rad_post)

    await db.commit()

    pre_count = (
        await db.execute(select(func.count()).select_from(RadPostAuth))
    ).scalar_one()

    @asynccontextmanager
    async def override_session_factory():
        yield db

    with patch(
        "cnaas_nac.core.scheduled_tasks.prune_endpoints.async_session_factory",
        new=override_session_factory,
    ):
        await prune_func()

    post_count = (
        await db.execute(select(func.count()).select_from(RadPostAuth))
    ).scalar_one()

    return pre_count, post_count


async def test_prune_discovered_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.DISCOVERED, 0, 60, prune_discovered_endpoints
    )

    assert pre_count - post_count == 30


async def test_prune_rejected_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.REJECTED, 0, 60, prune_rejected_endpoints
    )

    assert pre_count - post_count == 30


async def test_prune_pending_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.PENDING, 0, 60, prune_pending_endpoints
    )

    assert pre_count - post_count == 30


async def test_prune_authorized_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.AUTHORIZED, 0, 60, prune_authorized_endpoints
    )

    assert pre_count - post_count == 30
