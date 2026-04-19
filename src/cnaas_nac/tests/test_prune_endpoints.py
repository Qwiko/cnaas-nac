from datetime import datetime, timedelta
from typing import AsyncIterator, Callable
from unittest.mock import patch

import pytest
from fastapi.concurrency import asynccontextmanager
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.scheduled_tasks.prune_endpoints import (
    prune_eap_authorized_endpoints,
    prune_eap_rejected_endpoints,
    prune_mab_authorized_endpoints,
    prune_mab_discovered_endpoints,
    prune_mab_pending_endpoints,
    prune_mab_rejected_endpoints,
)
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.radpostauth import RadPostAuth

pytestmark = pytest.mark.anyio


async def call_prune_func(db: AsyncSession, prune_func: Callable) -> None:
    @asynccontextmanager
    async def override_session_factory() -> AsyncIterator[AsyncSession]:
        yield db

    with patch(
        "cnaas_nac.core.scheduled_tasks.prune_endpoints.async_session_factory",
        new=override_session_factory,
    ):
        await prune_func()


async def create_endpoints(
    db: AsyncSession,
    endpoint_state: EndpointState,
    start: int,
    stop: int,
    prune_func: Callable,
    is_mac: bool = True,
) -> tuple[int, int]:
    now = datetime.now()
    for i in range(start, stop):
        mac = f"AA:BB:{i * 1 % 256:02X}:{(i * 2) % 256:02X}:{(i * 3) % 256:02X}:{(i * 4) % 256:02X}".lower()

        if is_mac:
            username = mac
        else:
            username = f"some_user_{i}"
        auth_date = now - timedelta(days=i)

        endpoint = Endpoint(
            username=username,
            calling_station_id=mac,
            state=endpoint_state,
            created_at=auth_date,
            updated_at=auth_date,
        )
        rad_post = RadPostAuth(
            username=username,
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

    await call_prune_func(db, prune_func)

    post_count = (
        await db.execute(select(func.count()).select_from(RadPostAuth))
    ).scalar_one()

    return pre_count, post_count


async def test_prune_mab_discovered_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.DISCOVERED, 0, 60, prune_mab_discovered_endpoints
    )

    assert pre_count - post_count == 30


async def test_prune_mab_rejected_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.REJECTED, 0, 60, prune_mab_rejected_endpoints
    )

    assert pre_count - post_count == 30


async def test_prune_mab_pending_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.PENDING, 0, 60, prune_mab_pending_endpoints
    )

    assert pre_count - post_count == 30


async def test_prune_mab_authorized_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.AUTHORIZED, 0, 91, prune_mab_authorized_endpoints
    )

    assert pre_count - post_count == 1


async def test_prune_eap_rejected_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.REJECTED, 0, 60, prune_eap_rejected_endpoints, False
    )

    assert pre_count - post_count == 30


async def test_prune_eap_authorized_endpoints(db: AsyncSession) -> None:
    pre_count, post_count = await create_endpoints(
        db, EndpointState.AUTHORIZED, 0, 91, prune_eap_authorized_endpoints, False
    )

    assert pre_count - post_count == 1


async def test_prune_endpoint_with_later_updated_at(db: AsyncSession) -> None:
    # Create an endpoint that should not be pruned because it has a later updated_at timestamp
    mac = "aa:bb:cc:dd:ee:ff"

    auth_date = datetime.now() - timedelta(days=100)

    endpoint = Endpoint(
        username=mac,
        calling_station_id=mac,
        state=EndpointState.AUTHORIZED,
        updated_at=datetime.now(),
    )
    rad_post = RadPostAuth(
        username=mac,
        calling_station_id=mac,
        nas_ip_address="127.0.0.1",
        auth_date=auth_date,
    )
    db.add(endpoint)
    db.add(rad_post)
    await db.commit()

    await call_prune_func(db, prune_mab_authorized_endpoints)

    # Verify that the endpoint was not pruned
    result = await db.execute(
        select(func.count()).select_from(RadPostAuth).where(RadPostAuth.username == mac)
    )
    count = result.scalar_one()
    assert count == 1
