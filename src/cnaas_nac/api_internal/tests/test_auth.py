import datetime
from fastapi import status
from pytest import MonkeyPatch
from sqlalchemy import select, update
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from cnaas_nac.core.settings import settings

from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.user import User
from cnaas_nac.api_internal.schemas import InternalAuth

pytestmark = pytest.mark.anyio


async def test_auth_unauthorized(int_client: AsyncClient) -> None:
    # Should be unauthorized everytime
    for _ in range(2):
        response = await int_client.post(
            "/api/v2/auth",
            json={
                "username": "12:34:56:78:9a:bc",
                "nas_identifier": "eos-a1",
                "nas_port_id": "Ethernet1",
                "calling_station_id": "00:00:00:00:00:00",
                "called_station_id": "00:00:00:00:00:00",
                "nas_ip_address": "10.0.0.1",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_auth_authorized(db: AsyncSession, int_client: AsyncClient) -> None:
    auth = InternalAuth(
        **{
            "username": "cb:a9:87:65:43:21",
            "nas_identifier": "eos-a1",
            "nas_port_id": "Ethernet2",
            "calling_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
        }
    )

    # 1 will create user in db, but as disabled.
    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Enable user & set user vlan
    await db.execute(
        update(User)
        .where(User.username == auth.username)
        .values(enabled=True, vlan=3013)
    )

    await db.commit()

    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("Tunnel-Medium-Type").get("value") == "IEEE-802"
    assert response.json().get("Tunnel-Type").get("value") == "VLAN"
    assert response.json().get("Tunnel-Private-Group-Id").get("value") == "3013"


async def test_auth_port_lock_wrong_port(
    db: AsyncSession, int_client: AsyncClient, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.RADIUS, "LOCK_VLANS", [3131])

    auth = InternalAuth(
        **{
            "username": "aa:bb:cc:dd:ee:ff",
            "nas_identifier": "eos-a1",
            "nas_port_id": "Ethernet1",
            "calling_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
        }
    )

    # 1 will create user in db, but as disabled.
    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Enable user & set user vlan
    await db.execute(
        update(User)
        .where(User.username == auth.username)
        .values(enabled=True, vlan=3131)
    )

    await db.commit()

    # First auth with correct port.
    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("Tunnel-Medium-Type").get("value") == "IEEE-802"
    assert response.json().get("Tunnel-Type").get("value") == "VLAN"
    assert response.json().get("Tunnel-Private-Group-Id").get("value") == "3131"

    # Connect using wrong port.
    # auth.nas_identifier = "eos-a2"
    # auth.called_station_id = "00:00:00:00:00:02"
    auth.nas_port_id = "Ethernet2"

    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_auth_port_update(
    db: AsyncSession, int_client: AsyncClient, monkeypatch: MonkeyPatch
) -> None:
    auth = InternalAuth(
        **{
            "username": "aa:bb:cc:dd:ee:ff",
            "nas_identifier": "",
            "nas_port_id": "Ethernet1",
            "calling_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
        }
    )

    # 1 will create user in db, but as disabled.
    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Enable user & set user vlan
    await db.execute(
        update(User)
        .where(User.username == auth.username)
        .values(enabled=True, vlan=3131)
    )

    # Update updated_at to something in the past.
    updated_at_time = datetime.datetime(
        2000, 1, 1, 1, 1, 1, 1, tzinfo=datetime.timezone.utc
    )
    await db.execute(
        update(NasPort)
        .where(
            NasPort.username == auth.username,
            NasPort.called_station_id == auth.called_station_id,
        )
        .values(updated_at=updated_at_time)
    )

    await db.commit()

    # First auth with correct port.
    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("Tunnel-Medium-Type").get("value") == "IEEE-802"
    assert response.json().get("Tunnel-Type").get("value") == "VLAN"
    assert response.json().get("Tunnel-Private-Group-Id").get("value") == "3131"

    # Connect using hostname info.
    auth.nas_identifier = "eos-a1"

    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK

    nasport = (
        await db.execute(
            select(NasPort).where(
                NasPort.username == auth.username,
                NasPort.nas_identifier == "eos-a1",
            )
        )
    ).scalar_one_or_none()

    assert nasport

    # Make sure last_seen updated
    assert updated_at_time != nasport.updated_at


async def test_auth_access_time(
    db: AsyncSession, int_client: AsyncClient, monkeypatch: MonkeyPatch
) -> None:

    auth = InternalAuth(
        **{
            "username": "aa:bb:cc:dd:ee:ff",
            "nas_identifier": "a1",
            "nas_port_id": "Ethernet1",
            "calling_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
        }
    )

    # Set access_start and access_stop to valid times.
    db.add(
        User(
            username=auth.username,
            access_start=datetime.datetime.now() - datetime.timedelta(hours=1),
            access_stop=datetime.datetime.now() + datetime.timedelta(hours=1),
            vlan=14,
            enabled=True,
        )
    )
    await db.commit()

    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )

    assert response.status_code == status.HTTP_200_OK

    # Update access_start to the future.
    await db.execute(
        update(User)
        .where(User.username == auth.username)
        .values(
            access_start=datetime.datetime.now() + datetime.timedelta(hours=1),
            access_stop=None,
        )
    )

    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Update access_stop to have already passed.
    await db.execute(
        update(User)
        .where(User.username == auth.username)
        .values(
            access_start=None,
            access_stop=datetime.datetime.now() - datetime.timedelta(hours=1),
        )
    )

    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
