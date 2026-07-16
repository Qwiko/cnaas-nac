import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.radiusadminevent import (
    RadiusAdminEvent,
    RadiusCommand,
    RadiusDebugLog,
)

pytestmark = pytest.mark.anyio


async def test_v2_debug_none(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/debug",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_debug(db: AsyncSession, ext_client: AsyncClient) -> None:
    rae = RadiusAdminEvent(
        command=RadiusCommand.DEBUG_START, payload={"nas_identifier": "eos-a1"}
    )
    db.add(rae)
    await db.commit()
    response = await ext_client.get(
        "/api/v2/debug",
    )

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)


async def test_v2_debug_post(db: AsyncSession, ext_client: AsyncClient) -> None:
    data = {"nas_identifier": "eos-a1"}
    response = await ext_client.post("/api/v2/debug", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    assert isinstance(response.json(), dict)

    db_event = (
        await db.execute(
            select(RadiusAdminEvent).where(
                RadiusAdminEvent.command == RadiusCommand.DEBUG_START
            )
        )
    ).scalar_one_or_none()

    assert db_event
    assert db_event.payload == data


async def test_v2_debug_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    response = await ext_client.delete("/api/v2/debug")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db_event = (
        await db.execute(
            select(RadiusAdminEvent).where(
                RadiusAdminEvent.command == RadiusCommand.DEBUG_STOP
            )
        )
    ).scalar_one_or_none()

    assert db_event


async def test_v2_debug_logs_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Add some junk log data
    log = RadiusDebugLog(node_name="pytest", log_line="Some log line")
    db.add(log)
    await db.commit()

    response = await ext_client.delete("/api/v2/debug/logs")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db_event = (
        await db.execute(
            select(RadiusAdminEvent).where(
                RadiusAdminEvent.command == RadiusCommand.DEBUG_CLEAR
            )
        )
    ).scalar_one_or_none()

    assert db_event

    db_logs = (await db.execute(select(RadiusDebugLog))).scalars().all()

    assert len(db_logs) == 0
