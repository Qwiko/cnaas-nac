from datetime import datetime, timezone

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.radpostauth import RadPostAuth

pytestmark = pytest.mark.anyio


async def test_v2_authentication_not_found(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/authentication",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_authentication_list(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    db.add(
        RadPostAuth(
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            auth_date=datetime.now(timezone.utc),
            username="00:00:00:00:00:00",
            calling_station_id="00:00:00:00:00:00",
            reply="Access-Accept",
            request_json="{}",
            reply_json="{}",
        )
    )

    await db.commit()

    response = await ext_client.get(
        "/api/v2/authentication",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["username"] == "00:00:00:00:00:00"


async def test_v2_authentication_list_filter(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    db.add(
        RadPostAuth(
            id=99999,
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            auth_date=datetime.now(timezone.utc),
            username="00:00:00:00:00:01",
            calling_station_id="00:00:00:00:00:01",
            reply="Access-Accept",
            request_json="{}",
            reply_json="{}",
        )
    )
    db.add(
        RadPostAuth(
            id=100000,
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet2",
            auth_date=datetime.now(timezone.utc),
            username="00:00:00:00:00:02",
            calling_station_id="00:00:00:00:00:02",
            reply="Access-Reject",
            request_json="{}",
            reply_json="{}",
        )
    )

    await db.commit()

    response = await ext_client.get(
        "/api/v2/authentication?nas_port_id=Ethernet2",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["username"] == "00:00:00:00:00:02"
    assert data[0]["reply"] == "Access-Reject"


async def test_v2_authentication_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    db.add(
        RadPostAuth(
            id=99999,
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            auth_date=datetime.now(timezone.utc),
            reply="Access-Accept",
            username="00:00:00:00:00:01",
            calling_station_id="00:00:00:00:00:01",
        )
    )

    await db.commit()

    response = await ext_client.get(
        "/api/v2/authentication/99999",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert data["username"] == "00:00:00:00:00:01"


async def test_v2_authentication_get_not_found(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/authentication/88888",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_authentication_delete(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    db.add(
        RadPostAuth(
            id=77777,
            nas_ip_address="192.168.0.1",
            nas_port_id="Ethernet1",
            auth_date=datetime.now(timezone.utc),
            username="00:00:00:00:00:01",
            calling_station_id="00:00:00:00:00:01",
        )
    )

    await db.commit()

    response = await ext_client.delete(
        "/api/v2/authentication/77777",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert (
        await db.execute(select(RadPostAuth).where(RadPostAuth.id == 77777))
    ).scalar_one_or_none() is None
