import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.nas import Nas
from cnaas_nac.models.radiusadminevent import RadiusAdminEvent, RadiusCommand
pytestmark = pytest.mark.anyio


async def test_v2_radius_client_post(ext_client: AsyncClient) -> None:
    response = await ext_client.post(
        "/api/v2/radius_client",
        json={"name": "TestClient", "network": "10.10.10.0/24", "secret": "testing123"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert isinstance(response.json().get("id"), int)
    assert response.json().get("name") == "TestClient"


async def test_v2_radius_client_post_fail(ext_client: AsyncClient) -> None:
    # No data
    response = await ext_client.post(
        "/api/v2/radius_client",
        json={},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Must not include whitespace
    response = await ext_client.post(
        "/api/v2/radius_client",
        json={"name": "Some name"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_v2_radius_client_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(Nas(name="SomeClient", network="10.0.0.0/24", secret="testing123"))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/radius_client",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 1
    assert "SomeClient" in [a.get("name") for a in res_json]
    assert int(response.headers.get("X-Total-Count")) >= 1


async def test_v2_radius_client_notfound(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    await db.execute(delete(Nas))

    response = await ext_client.get(
        "/api/v2/radius_client",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) == 0
    assert res_json == []
    assert int(response.headers.get("X-Total-Count")) == 0


async def test_v2_radius_client_get_name(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    # Create entry in db
    nas = Nas(name="SomeTestClient", network="10.0.0.0/24", secret="testing123")

    db.add(nas)
    await db.commit()
    await db.refresh(nas)
    response = await ext_client.get(
        f"/api/v2/radius_client/{nas.id}",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)
    assert "SomeTestClient" == res_json.get("name")


async def test_v2_radius_client_name_notfound(ext_client: AsyncClient) -> None:
    for method in ["GET", "PUT", "DELETE"]:
        response = await ext_client.request(
            method,
            "/api/v2/radius_client/999999",
            json={"name": "group_11", "network": "10.0.0.0/24", "secret": "testing123"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_radius_client_put_name(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    # Create entry in db
    nas = Nas(name="TestClient1", network="10.0.0.0/24", secret="testing111")
    db.add(nas)
    await db.commit()
    await db.refresh(nas)
    response = await ext_client.put(
        f"/api/v2/radius_client/{nas.id}",
        json={"name": "TestClient2", "network": "10.0.0.0/24", "secret": "testing123"},
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)
    assert "TestClient2" == res_json.get("name")

    # When the secret has changed we need to add a radius admin event to clear the client from the radius server
    assert (
        await db.execute(select(RadiusAdminEvent).where(RadiusAdminEvent.command == RadiusCommand.CLEAR_CLIENT), RadiusAdminEvent.payload["network"].astext == "10.0.0.0/24")
    ).scalar_one_or_none() is not None


async def test_v2_radius_client_delete_name(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    # Create entry in db
    nas = Nas(name="TestClient", network="10.0.0.0/24", secret="testing123")
    db.add(nas)
    await db.commit()
    await db.refresh(nas)
    response = await ext_client.delete(
        f"/api/v2/radius_client/{nas.id}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Entry is not found in db.
    assert (
        await db.execute(select(Nas).where(Nas.name == "TestClient"))
    ).scalar_one_or_none() is None

    # New radius event is created to clear the client from the radius server.
    assert (
        await db.execute(select(RadiusAdminEvent).where(RadiusAdminEvent.command == RadiusCommand.CLEAR_CLIENT), RadiusAdminEvent.payload["network"].astext == "10.0.0.0/24")
    ).scalar_one_or_none() is not None
