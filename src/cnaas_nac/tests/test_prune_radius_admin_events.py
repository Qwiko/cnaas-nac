from datetime import datetime, timedelta
from typing import AsyncIterator, Callable
from unittest.mock import patch

from fastapi.concurrency import asynccontextmanager
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.scheduled_tasks.prune_radius_admin_events import (
    prune_radius_admin_events,
)
from cnaas_nac.models.radiusadminevent import RadiusAdminEvent, RadiusCommand

pytestmark = pytest.mark.anyio


async def create_radius_admin_events(
    db: AsyncSession,
    start: int,
    stop: int,
    prune_func: Callable,
) -> tuple[int, int]:
    now = datetime.now()
    for i in range(start, stop):
        auth_date = now - timedelta(days=i)

        rad_admin_event = RadiusAdminEvent(
            command=RadiusCommand.CLEAR_CLIENT,
            payload={"network": f"192.168.{i}.0/24"},
            created_at=auth_date,
        )
        db.add(rad_admin_event)

    await db.commit()

    pre_count = (
        await db.execute(select(func.count()).select_from(RadiusAdminEvent))
    ).scalar_one()

    @asynccontextmanager
    async def override_session_factory() -> AsyncIterator[AsyncSession]:
        yield db

    with patch(
        "cnaas_nac.core.scheduled_tasks.prune_radius_admin_events.async_session_factory",
        new=override_session_factory,
    ):
        await prune_func()

    post_count = (
        await db.execute(select(func.count()).select_from(RadiusAdminEvent))
    ).scalar_one()

    return pre_count, post_count


async def test_prune_radius_admin_events(db: AsyncSession) -> None:
    pre_count, post_count = await create_radius_admin_events(
        db, 0, 10, prune_radius_admin_events
    )

    # Deleted 3 events because the retention period is set to 7 days in the settings
    assert pre_count - post_count == 3
