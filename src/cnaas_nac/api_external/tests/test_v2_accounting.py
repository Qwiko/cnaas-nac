from datetime import datetime, timezone

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.radacct import RadAcct

pytestmark = pytest.mark.anyio


async def test_v2_accounting_not_found(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/accounting",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_accounting_list(db: AsyncSession, ext_client: AsyncClient) -> None:
    db.add(
        RadAcct(
            acct_session_id="00000001",
            acct_unique_id="00000001",
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            acct_start_time=datetime.now(timezone.utc),
            username="00:00:00:00:00:00",
            calling_station_id="00:00:00:00:00:00",
        )
    )

    await db.commit()

    response = await ext_client.get(
        "/api/v2/accounting",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["username"] == "00:00:00:00:00:00"


async def test_v2_accounting_list_filter(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    db.add(
        RadAcct(
            id=99999,
            acct_session_id="00000001",
            acct_unique_id="00000001",
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            acct_start_time=datetime.now(timezone.utc),
            username="00:00:00:00:00:01",
            calling_station_id="00:00:00:00:00:01",
        )
    )
    db.add(
        RadAcct(
            id=100000,
            acct_session_id="00000002",
            acct_unique_id="00000002",
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet2",
            acct_start_time=datetime.now(timezone.utc),
            username="00:00:00:00:00:02",
            calling_station_id="00:00:00:00:00:02",
        )
    )

    await db.commit()

    response = await ext_client.get(
        "/api/v2/accounting?nas_port_id=Ethernet2",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["username"] == "00:00:00:00:00:02"


async def test_v2_accounting_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    db.add(
        RadAcct(
            id=99999,
            acct_session_id="00000001",
            acct_unique_id="00000001",
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            acct_start_time=datetime.now(timezone.utc),
            username="00:00:00:00:00:01",
            calling_station_id="00:00:00:00:00:01",
        )
    )

    await db.commit()

    response = await ext_client.get(
        "/api/v2/accounting/99999",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert data["username"] == "00:00:00:00:00:01"


async def test_v2_accounting_get_not_found(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.get(
        "/api/v2/accounting/88888",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_accounting_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    db.add(
        RadAcct(
            id=77777,
            acct_session_id="00000001",
            acct_unique_id="00000001",
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            acct_start_time=datetime.now(timezone.utc),
            username="00:00:00:00:00:01",
            calling_station_id="00:00:00:00:00:01",
        )
    )

    await db.commit()

    response = await ext_client.delete(
        "/api/v2/accounting/77777",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert (
        await db.execute(select(RadAcct).where(RadAcct.id == 77777))
    ).scalar_one_or_none() is None
