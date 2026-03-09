import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.endpoint import EndpointGroup


pytestmark = pytest.mark.anyio


async def test_v2_endpoint_group_post(ext_client: AsyncClient) -> None:
    response = await ext_client.post(
        "/api/v2/endpoint_group",
        json={"name": "Vlan144"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert isinstance(response.json().get("id"), int)
    assert response.json().get("name") == "Vlan144"


async def test_v2_endpoint_group_post_fail(ext_client: AsyncClient) -> None:
    # No data
    response = await ext_client.post(
        "/api/v2/endpoint_group",
        json={},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_v2_endpoint_group_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(EndpointGroup(name="SomeGroup"))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/endpoint_group",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 1
    assert "SomeGroup" in [a.get("name") for a in res_json]
    assert int(response.headers.get("X-Total-Count")) >= 1


async def test_v2_endpoint_group_notfound(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    await db.execute(delete(EndpointGroup))
    response = await ext_client.get(
        "/api/v2/endpoint_group",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) == 0
    assert res_json == []
    assert int(response.headers.get("X-Total-Count")) == 0


async def test_v2_endpoint_group_get_name(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    # Create entry in db
    group = EndpointGroup(name="group1")

    db.add(group)
    await db.commit()
    await db.refresh(group)
    response = await ext_client.get(
        f"/api/v2/endpoint_group/{group.id}",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)
    assert "group1" == res_json.get("name")


async def test_v2_endpoint_group_name_notfound(ext_client: AsyncClient) -> None:
    for method in ["GET", "PUT", "DELETE"]:
        response = await ext_client.request(
            method,
            "/api/v2/endpoint_group/999999",
            json={"name": "group_11"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_endpoint_group_put_name(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    # Create entry in db
    group = EndpointGroup(name="group0")
    db.add(group)
    await db.commit()
    await db.refresh(group)
    response = await ext_client.put(
        f"/api/v2/endpoint_group/{group.id}",
        json={"name": "group2"},
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)
    assert "group2" == res_json.get("name")


async def test_v2_endpoint_group_delete_name(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    # Create entry in db
    group = EndpointGroup(name="group01")
    db.add(group)
    await db.commit()
    await db.refresh(group)
    response = await ext_client.delete(
        f"/api/v2/endpoint_group/{group.id}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Entry is not found in db.
    assert (
        await db.execute(select(EndpointGroup).where(EndpointGroup.name == "group01"))
    ).scalar_one_or_none() is None
