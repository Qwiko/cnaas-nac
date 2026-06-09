from datetime import datetime, timedelta
from typing import AsyncIterator

import pytest
from fastapi.concurrency import asynccontextmanager
from pytest import LogCaptureFixture
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.coa import CoA
from cnaas_nac.core.logging import get_logger
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.nas import Nas
from cnaas_nac.models.nas_port import NasPort

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

    logger = get_logger()
    logger.propagate = True

    with caplog.at_level("INFO", logger=logger.name):
        coa = await CoA.create(endpoint)

    assert coa is None

    assert (
        "Another endpoint have connected on this port more recently, will not send CoA packet."
        in caplog.text
    )


async def test_coa_create_no_nasport(
    db: AsyncSession, caplog: LogCaptureFixture
) -> None:
    # Add NasPort
    endpoint = Endpoint(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        state=EndpointState.AUTHORIZED,
    )

    db.add(endpoint)

    await db.commit()

    logger = get_logger()
    logger.propagate = True

    with caplog.at_level("INFO", logger=logger.name):
        coa = await CoA.create(endpoint)

    assert coa is None

    assert "No NAS port found for endpoint" in caplog.text


async def test_coa_create_no_nas_ip(
    db: AsyncSession, caplog: LogCaptureFixture
) -> None:
    # Add NasPort
    endpoint = Endpoint(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        state=EndpointState.AUTHORIZED,
    )

    endpoint_nas_port = NasPort(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        nas_identifier="nas1",
        nas_ip_address="",
        called_station_id="11:01:02:03:04:05",
        nas_port_id="Ethernet1",
    )
    db.add(endpoint)
    db.add(endpoint_nas_port)

    await db.commit()

    logger = get_logger()
    logger.propagate = True

    with caplog.at_level("INFO", logger=logger.name):
        coa = await CoA.create(endpoint)

    assert coa is None

    assert "NAS port must have NAS IP address, cannot send CoA packet." in caplog.text


async def test_coa_create_no_nas(db: AsyncSession, caplog: LogCaptureFixture) -> None:
    # Add NasPort
    endpoint = Endpoint(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        state=EndpointState.AUTHORIZED,
    )

    endpoint_nas_port = NasPort(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        nas_identifier="nas1",
        nas_ip_address="10.0.0.1",
        called_station_id="11:01:02:03:04:05",
        nas_port_id="Ethernet1",
    )
    db.add(endpoint)
    db.add(endpoint_nas_port)

    await db.commit()

    logger = get_logger()
    logger.propagate = True

    with caplog.at_level("INFO", logger=logger.name):
        coa = await CoA.create(endpoint)

    assert coa is None

    assert "NAS not found for the given IP address" in caplog.text


async def test_coa_create_success(db: AsyncSession) -> None:
    # Add NasPort
    endpoint = Endpoint(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        state=EndpointState.AUTHORIZED,
    )

    endpoint_nas_port = NasPort(
        username="test@example.com",
        calling_station_id="01:01:02:03:04:05",
        nas_identifier="nas1",
        nas_ip_address="10.0.0.1",
        called_station_id="11:01:02:03:04:05",
        nas_port_id="Ethernet1",
    )

    nas = Nas(
        name="nas1",
        network="10.0.0.0/24",
        secret="testing123",
        server="default",
        coa_enabled=True,
    )

    db.add(endpoint)
    db.add(endpoint_nas_port)
    db.add(nas)

    await db.commit()

    coa = await CoA.create(endpoint)

    assert coa is not None
    assert isinstance(coa, CoA)
