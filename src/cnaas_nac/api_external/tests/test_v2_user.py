from unittest.mock import patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.user import User
from cnaas_nac.models.radpostauth import RadPostAuth

pytestmark = pytest.mark.anyio


async def test_v2_user_get_none(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Delete all entries from the db.

    await db.execute(delete(User))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/user",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_user_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(User(username="00:00:00:00:00:00", enabled=True, vlan=14))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/user",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 1
    assert "00:00:00:00:00:00" in [a.get("username") for a in res_json]
    assert int(response.headers.get("X-Total-Count")) >= 1


async def test_v2_user_get_name(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Create entry in db
    db.add(User(username="00:00:00:00:00:01", enabled=True, vlan=14))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/user/00:00:00:00:00:01",
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, dict)

    assert "00:00:00:00:00:01" == res_json.get("username")


async def test_v2_user_get_name_not_found(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.get(
        "/api/v2/user/12:34:56:89:ab:01",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_user_post(db: AsyncSession, ext_client: AsyncClient) -> None:
    response = await ext_client.post(
        "/api/v2/user",
        json={"username": "00:00:0a:11:11:11", "enabled": True, "vlan": 14},
    )

    res_json = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert isinstance(res_json, dict)
    assert "00:00:0a:11:11:11" == res_json.get("username")

    # It exists in db
    db_user = (
        await db.execute(select(User).where(User.username == "00:00:0a:11:11:11"))
    ).scalar_one_or_none()

    assert db_user
    assert db_user.enabled
    assert db_user.vlan == 14


async def test_v2_user_delete_name_not_found(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.delete(
        "/api/v2/user/12:34:56:89:ab:01",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_user_delete_name(db: AsyncSession, ext_client: AsyncClient) -> None:
    local_username = "a1:3f:00:00:00:11"
    # Create entries in db
    db.add(User(username=local_username, enabled=True, vlan=14))
    db.add(
        NasPort(
            username=local_username,
            nas_ip_address="192.168.1.1",
            nas_identifier="a1",
            nas_port_id="Ethernet1",
            calling_station_id="00:00:00:00:00:00",
            called_station_id=local_username,
        )
    )
    db.add(RadPostAuth(username=local_username))

    await db.commit()

    with patch("cnaas_nac.core.coa.CoA.send_packet", autospec=True) as mock_send:
        response = await ext_client.delete(
            f"/api/v2/user/{local_username}",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_send.assert_called_once()

    # All relations should be deleted
    assert not (
        await db.execute(select(User).where(User.username == local_username))
    ).scalar_one_or_none()

    assert not (
        await db.execute(select(NasPort).where(NasPort.username == local_username))
    ).scalar_one_or_none()

    assert not (
        await db.execute(
            select(RadPostAuth).where(RadPostAuth.username == local_username)
        )
    ).scalar_one_or_none()


async def test_v2_user_post_existing_user(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    # Create entry in db
    db.add(User(username="bc:fe:00:00:00:01", enabled=True, vlan=14))
    await db.commit()

    response = await ext_client.post(
        "/api/v2/user",
        json={"username": "bc:fe:00:00:00:01", "enabled": True, "vlan": 14},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_v2_user_put_name_not_found(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.put(
        "/api/v2/user/12:34:56:89:ab:01", json={"enabled": True, "vlan": 14}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_user_put_name(
    db: AsyncSession,
    ext_client: AsyncClient,
) -> None:
    # Create entry in db
    db.add(User(username="00:00:00:00:bc:11", enabled=True, vlan=14))
    await db.commit()

    response = await ext_client.put(
        "/api/v2/user/00:00:00:00:bc:11", json={"enabled": False, "vlan": 13}
    )

    assert response.status_code == status.HTTP_200_OK
    db_user = (
        await db.execute(select(User).where(User.username == "00:00:00:00:bc:11"))
    ).scalar_one_or_none()

    assert db_user
    assert db_user.enabled is False
    assert db_user.vlan == 13


async def test_v2_user_put_name_issue_coa(
    db: AsyncSession,
    ext_client: AsyncClient,
) -> None:
    """Make sure coa.send_packet runs"""
    # Create entry in db
    db.add(User(username="00:00:00:aa:dd:11", enabled=True, vlan=14))
    db.add(
        NasPort(
            username="00:00:00:aa:dd:11",
            nas_ip_address="192.168.1.1",
            nas_identifier="a1",
            nas_port_id="Ethernet1",
            calling_station_id="00:00:00:00:00:00",
            called_station_id="00:00:00:aa:dd:11",
        )
    )
    await db.commit()

    with patch("cnaas_nac.core.coa.CoA.send_packet", autospec=True) as mock_send:
        response = await ext_client.put(
            "/api/v2/user/00:00:00:aa:dd:11", json={"enabled": False, "vlan": 13}
        )

        assert response.status_code == status.HTTP_200_OK

        mock_send.assert_called_once()


async def test_v2_user_delete_name_issue_coa(
    db: AsyncSession,
    ext_client: AsyncClient,
) -> None:
    """Make sure coa.send_packet runs"""
    # Create entry in db
    db.add(User(username="00:00:ee:aa:dd:11", enabled=True, vlan=14))
    db.add(
        NasPort(
            username="00:00:ee:aa:dd:11",
            nas_ip_address="192.168.1.1",
            nas_identifier="a1",
            nas_port_id="Ethernet1",
            calling_station_id="00:00:00:00:00:00",
            called_station_id="00:00:ee:aa:dd:11",
        )
    )
    await db.commit()

    with patch("cnaas_nac.core.coa.CoA.send_packet", autospec=True) as mock_send:
        response = await ext_client.delete("/api/v2/user/00:00:ee:aa:dd:11")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_send.assert_called_once()
