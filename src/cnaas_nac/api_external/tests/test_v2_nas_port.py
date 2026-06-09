import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.nas_port import NasPort

pytestmark = pytest.mark.anyio


async def test_v2_nas_port_get_none(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Delete all entries from the db.
    await db.execute(delete(NasPort))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/nas_port",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_nas_port_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    endpoint = Endpoint(
        username="00:00:00:00:00:01",
        calling_station_id="00:00:00:00:00:01",
        state=EndpointState.AUTHORIZED,
    )

    nas_port = NasPort(
        username="00:00:00:00:00:01",
        calling_station_id="00:00:00:00:00:01",
        nas_identifier="nas1",
        nas_port_id="Ethernet1",
        nas_ip_address="10.0.0.1",
        called_station_id="11:11:11:11:11:11",
    )
    db.add(endpoint)
    db.add(nas_port)
    await db.commit()

    response = await ext_client.get(
        "/api/v2/nas_port",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)

    assert "00:00:00:00:00:01" in [a.get("username") for a in res_json]


async def test_v2_nas_port_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    endpoint = Endpoint(
        username="00:00:00:00:00:01",
        calling_station_id="00:00:00:00:00:01",
        state=EndpointState.AUTHORIZED,
    )

    nas_port = NasPort(
        username="00:00:00:00:00:01",
        calling_station_id="00:00:00:00:00:01",
        nas_identifier="nas1",
        nas_port_id="Ethernet1",
        nas_ip_address="10.0.0.1",
        called_station_id="11:11:11:11:11:11",
    )

    db.add(endpoint)
    db.add(nas_port)

    await db.commit()

    response = await ext_client.delete(
        f"/api/v2/nas_port/{nas_port.id}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_v2_nas_port_delete_not_found(ext_client: AsyncClient) -> None:
    response = await ext_client.delete(
        "/api/v2/nas_port/999999",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
