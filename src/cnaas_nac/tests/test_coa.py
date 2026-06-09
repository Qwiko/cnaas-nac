from typing import AsyncIterator
from datetime import datetime, timedelta
import pytest
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from pytest import LogCaptureFixture
from cnaas_nac.core.coa import CoA
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.core.logging import get_logger

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def override_sessionmaker(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    @asynccontextmanager
    async def override_session_factory() -> AsyncIterator[AsyncSession]:
        yield db

    monkeypatch.setattr(
        "cnaas_nac.core.coa.async_session_factory",
        override_session_factory,
    )


async def test_coa_create_more_recent_nasport(
    db: AsyncSession, caplog: LogCaptureFixture
) -> None:
    # Add NasPort
    endpoint = Endpoint(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        state=EndpointState.AUTHORIZED,
    )

    now = datetime.now()

    endpoint_nas_port = NasPort(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        nas_identifier="nas1",
        nas_ip_address="10.0.0.1",
        called_station_id="11:01:02:03:04:05",
        nas_port_id="Ethernet1",
        updated_at=now,
    )
    recent_nas_port = NasPort(
        username="otheruser@example.com",
        calling_station_id="02:01:02:03:04:05",
        nas_identifier="nas1",
        nas_ip_address="10.0.0.1",
        called_station_id="11:01:02:03:04:05",
        nas_port_id="Ethernet1",
        updated_at=now + timedelta(hours=1),
    )
    db.add(endpoint)
    db.add(endpoint_nas_port)
    db.add(recent_nas_port)

    await db.commit()
    await db.refresh(endpoint)
    await db.refresh(endpoint_nas_port)
    await db.refresh(recent_nas_port)

    logger = get_logger()
    logger.propagate = True

    with caplog.at_level("INFO", logger=logger.name):
        coa = await CoA.create(endpoint)

    assert coa is None

    assert (
        "Another endpoint have connected on this port more recently, will not send CoA packet."
        in caplog.text
    )
