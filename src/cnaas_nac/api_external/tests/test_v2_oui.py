import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.oui import DeviceOui

pytestmark = pytest.mark.anyio


async def test_v2_oui_post(ext_client: AsyncClient) -> None:
    response = await ext_client.post(
        "/api/v2/oui",
        json={"oui": "12:34:56", "vlan": 3131},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert isinstance(response.json().get("id"), int)
    assert response.json().get("vlan") == 3131


async def test_v2_oui_post_fail(ext_client: AsyncClient) -> None:
    # Wrong oui
    response = await ext_client.post(
        "/api/v2/oui",
        json={"oui": "12:34:56:78:9a:bc", "vlan": 3131},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # No vlan
    response = await ext_client.post(
        "/api/v2/oui",
        json={"oui": "12:34:56"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Wrong vlans
    for vlan in [0, 4095, 111111]:
        response = await ext_client.post(
            "/api/v2/oui",
            json={"oui": "12:34:56", "vlan": vlan},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_v2_oui_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(DeviceOui(oui="aa:bb:cc", vlan=1234))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/oui",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 1
    assert "aa:bb:cc" in [a.get("oui") for a in res_json]
    assert int(response.headers.get("X-Total-Count")) >= 1


async def test_v2_oui_notfound(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/oui",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_oui_get_name(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(DeviceOui(oui="ee:dd:ff", vlan=2345, description="Some description"))
    await db.commit()
    response = await ext_client.get(
        "/api/v2/oui/ee:dd:ff",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)
    assert "ee:dd:ff" == res_json.get("oui")
    assert "Some description" == res_json.get("description")


async def test_v2_oui_name_notfound(ext_client: AsyncClient) -> None:
    for method in ["GET", "PUT", "DELETE"]:
        response = await ext_client.request(
            method,
            "/api/v2/oui/aa:bb:cc",
            json={"oui": "12:34:56", "vlan": 14},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_oui_put_name(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(DeviceOui(oui="ea:da:fa", vlan=3456, description="Some description"))
    await db.commit()
    response = await ext_client.put(
        "/api/v2/oui/ea:da:fa",
        json={"oui": "ea:da:fa", "vlan": 4001, "description": "New description"},
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)
    assert "ea:da:fa" == res_json.get("oui")
    assert 4001 == res_json.get("vlan")
    assert "New description" == res_json.get("description")


async def test_v2_oui_delete_name(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(DeviceOui(oui="eb:db:fb", vlan=1111))
    await db.commit()
    response = await ext_client.delete(
        "/api/v2/oui/eb:db:fb",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Entry is not found in db.
    assert (
        await db.execute(select(DeviceOui).where(DeviceOui.oui == "eb:db:fb"))
    ).scalar_one_or_none() is None
