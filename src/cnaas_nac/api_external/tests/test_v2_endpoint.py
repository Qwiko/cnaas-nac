from typing import AsyncIterator
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.concurrency import asynccontextmanager
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.endpoint import Endpoint, EndpointGroup, EndpointState
from cnaas_nac.models.nas import Nas
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.radpostauth import RadPostAuth
from cnaas_nac.core.coa import CoA

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


async def test_v2_endpoint_get_none(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Delete all entries from the db.
    await db.execute(delete(Endpoint))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/endpoint",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_endpoint_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    mac = "00:00:00:00:00:00"
    db.add(Endpoint(username=mac, calling_station_id=mac, state=EndpointState.PENDING))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/endpoint",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 1
    assert mac in [a.get("username") for a in res_json]
    assert int(response.headers.get("X-Total-Count")) >= 1


async def test_v2_endpoint_get_name(db: AsyncSession, ext_client: AsyncClient) -> None:
    mac = "00:00:00:00:00:01"

    # Create entry in db
    endpoint = Endpoint(
        username=mac, calling_station_id=mac, state=EndpointState.PENDING
    )
    db.add(endpoint)
    await db.commit()

    response = await ext_client.get(
        f"/api/v2/endpoint/{endpoint.id}",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)

    assert mac == res_json.get("username")


async def test_v2_endpoint_get_name_different_format(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    mac = "00:00:00:00:00:01"
    other_format_mac = "0000.0000.0001"

    # Create entry in db
    endpoint = Endpoint(
        username=mac, calling_station_id=mac, state=EndpointState.PENDING
    )
    db.add(endpoint)
    await db.commit()

    response = await ext_client.get(
        f"/api/v2/endpoint?calling_station_id={other_format_mac}",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) == 1

    # Translated mac is saved and returned
    assert mac == res_json[0].get("username")


async def test_v2_endpoint_get_id_not_found(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/endpoint/9999999",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_endpoint_post(db: AsyncSession, ext_client: AsyncClient) -> None:
    response = await ext_client.post(
        "/api/v2/endpoint",
        json={"username": "00:00:0a:11:11:11"},
    )

    res_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert isinstance(res_json, dict)
    assert "00:00:0a:11:11:11" == res_json.get("username")

    # It exists in db
    db_user = (
        await db.execute(
            select(Endpoint).where(Endpoint.username == "00:00:0a:11:11:11")
        )
    ).scalar_one_or_none()

    assert db_user


async def test_v2_endpoint_delete_name_not_found(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.delete(
        "/api/v2/endpoint/999999",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_endpoint_delete_name(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    local_username = "a1:3f:00:00:00:11"
    # Create entries in db
    endpoint = Endpoint(
        username=local_username,
        calling_station_id=local_username,
        state=EndpointState.PENDING,
    )
    db.add(endpoint)
    db.add(
        NasPort(
            username=local_username,
            nas_ip_address="192.168.1.1",
            nas_identifier="a1",
            nas_port_id="Ethernet1",
            calling_station_id=local_username,
            called_station_id="00:00:00:00:00:00",
        )
    )
    db.add(
        Nas(
            name="test", network="192.168.1.0/24", secret="testing123", coa_enabled=True
        )
    )
    db.add(
        RadPostAuth(
            username=local_username,
            calling_station_id=local_username,
            nas_ip_address="192.168.1.1",
        )
    )

    await db.commit()

    with patch.object(CoA, "send_coa_packet", autospec=True) as mock_send:
        response = await ext_client.delete(
            f"/api/v2/endpoint/{endpoint.id}",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    mock_send.assert_called_once()

    # All relations should be deleted
    assert not (
        await db.execute(select(Endpoint).where(Endpoint.username == local_username))
    ).scalar_one_or_none()

    assert not (
        await db.execute(select(NasPort).where(NasPort.username == local_username))
    ).scalar_one_or_none()

    assert not (
        await db.execute(
            select(RadPostAuth).where(RadPostAuth.username == local_username)
        )
    ).scalar_one_or_none()


async def test_v2_endpoint_post_existing_user(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    mac = "bc:fe:00:00:00:01"
    # Create entry in db
    db.add(Endpoint(username=mac, calling_station_id=mac, state=EndpointState.PENDING))
    await db.commit()

    response = await ext_client.post(
        "/api/v2/endpoint",
        json={"username": mac},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_v2_endpoint_put_name_not_found(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.put("/api/v2/endpoint/12391082", json={})

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_endpoint_put_name(
    db: AsyncSession,
    ext_client: AsyncClient,
) -> None:
    mac = "00:00:00:00:bc:11"
    # Create entry in db
    endpoint = Endpoint(
        username=mac, calling_station_id=mac, state=EndpointState.PENDING
    )
    db.add(endpoint)
    await db.commit()

    response = await ext_client.put(f"/api/v2/endpoint/{endpoint.id}", json={})

    assert response.status_code == status.HTTP_200_OK
    db_user = (
        await db.execute(
            select(Endpoint).where(Endpoint.username == "00:00:00:00:bc:11")
        )
    ).scalar_one_or_none()

    assert db_user


async def test_v2_endpoint_put_name_issue_coa(
    db: AsyncSession,
    ext_client: AsyncClient,
) -> None:
    """Make sure coa.send_packet runs"""
    mac = "00:00:00:aa:dd:11"
    # Create entry in db
    endpoint = Endpoint(
        username=mac, calling_station_id=mac, state=EndpointState.PENDING
    )
    db.add(endpoint)
    db.add(
        NasPort(
            username=mac,
            nas_ip_address="192.168.1.1",
            nas_identifier="a1",
            nas_port_id="Ethernet1",
            calling_station_id=mac,
            called_station_id="00:00:00:00:00:00",
        )
    )
    db.add(
        Nas(
            name="test", network="192.168.1.0/24", secret="testing123", coa_enabled=True
        )
    )
    db.add(EndpointGroup(id=999999, name="Test"))
    await db.commit()

    with patch.object(CoA, "send_coa_packet", autospec=True) as mock_send:
        response = await ext_client.put(
            f"/api/v2/endpoint/{endpoint.id}", json={"group_id": 999999}
        )

        assert response.status_code == status.HTTP_200_OK

    mock_send.assert_called_once()


async def test_v2_endpoint_delete_name_issue_coa(
    db: AsyncSession,
    ext_client: AsyncClient,
) -> None:
    """Make sure coa.send_packet runs"""
    mac = "00:00:ee:aa:dd:11"
    # Create entry in db
    endpoint = Endpoint(
        username=mac, calling_station_id=mac, state=EndpointState.PENDING
    )
    db.add(endpoint)
    db.add(
        NasPort(
            username=mac,
            nas_ip_address="192.168.1.1",
            nas_identifier="a1",
            nas_port_id="Ethernet1",
            calling_station_id=mac,
            called_station_id="00:00:00:00:00:00",
        )
    )
    db.add(
        Nas(
            name="test", network="192.168.1.0/24", secret="testing123", coa_enabled=True
        )
    )
    await db.commit()

    with patch.object(CoA, "send_coa_packet", autospec=True) as mock_send:
        response = await ext_client.delete(f"/api/v2/endpoint/{endpoint.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    mock_send.assert_called_once()
