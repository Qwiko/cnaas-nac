import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.policy import (
    Policy,
    MatchLogic,
    ConditionOperator,
    PolicyCondition,
    PolicyReply,
    PortLocking,
    PortType,
    ReplyOperator,
)

pytestmark = pytest.mark.anyio


async def test_auth_policy(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    # Add Policy

    policy = Policy(name="test_policy", match_logic=MatchLogic.AND, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "calling_station_id",
                "operator": ConditionOperator.STARTS_WITH,
                "value": "aa:bb:cc",
            }
        ]
    ]

    policy.replies = [
        PolicyReply(**d)
        for d in [
            {
                "attribute": "Tunnel-Medium-Type",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "IEEE-802",
            },
            {
                "attribute": "Tunnel-Type",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "VLAN",
            },
            {
                "attribute": "Tunnel-Private-Group-Id",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "213",
            },
        ]
    ]

    db.add(policy)
    await db.commit()

    auth_json = {
        "username": "aa:bb:cc:dd:ee:ff",
        "nas_identifier": "a1",
        "nas_port_id": "Ethernet1",
        "nas_port_type": "Ethernet",
        "calling_station_id": "aa:bb:cc:dd:ee:ff",  # type: ignore[arg-type]
        "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
        "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
    }

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    ret_json = response.json()
    assert response.status_code == status.HTTP_200_OK

    assert ret_json.get("Tunnel-Medium-Type").get("value") == "IEEE-802"
    assert ret_json.get("Tunnel-Type").get("value") == "VLAN"
    assert ret_json.get("Tunnel-Private-Group-Id").get("value") == "213"


async def test_auth_policy_discovered(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    auth_json = {
        "username": "bb:bb:cc:dd:ee:ff",
        "nas_identifier": "a1",
        "nas_port_id": "Ethernet1",
        "nas_port_type": "Ethernet",
        "calling_station_id": "bb:bb:cc:dd:ee:ff",  # type: ignore[arg-type]
        "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
        "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
    }

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Should have been created as DISCOVERED.
    # And then stays discovered
    db_endpoint = (
        await db.execute(
            select(Endpoint).where(
                Endpoint.username == "bb:bb:cc:dd:ee:ff",
                Endpoint.calling_station_id == "bb:bb:cc:dd:ee:ff",
            )
        )
    ).scalar_one_or_none()

    assert db_endpoint
    assert db_endpoint.state == EndpointState.DISCOVERED


async def test_auth_policy_authorized_to_rejected(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    db.add(
        Endpoint(
            username="bb:bb:cc:dd:ee:ff",
            calling_station_id="bb:bb:cc:dd:ee:ff",
            state=EndpointState.AUTHORIZED,
        )
    )
    await db.commit()

    auth_json = {
        "username": "bb:bb:cc:dd:ee:ff",
        "nas_identifier": "a1",
        "nas_port_id": "Ethernet1",
        "nas_port_type": "Ethernet",
        "calling_station_id": "bb:bb:cc:dd:ee:ff",  # type: ignore[arg-type]
        "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
        "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
    }

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Should have been set to REJECTED.
    # And then stays discovered
    db_endpoint = (
        await db.execute(
            select(Endpoint).where(
                Endpoint.username == "bb:bb:cc:dd:ee:ff",
                Endpoint.calling_station_id == "bb:bb:cc:dd:ee:ff",
            )
        )
    ).scalar_one_or_none()

    assert db_endpoint
    assert db_endpoint.state == EndpointState.REJECTED


async def test_auth_port_lock_wrong_port(
    db: AsyncSession, int_client: AsyncClient
) -> None:
    policy = Policy(
        name="test_policy_switchport",
        match_logic=MatchLogic.AND,
        enabled=True,
        port_locking=PortLocking.SWITCH_PORT,
    )

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "calling_station_id",
                "operator": ConditionOperator.STARTS_WITH,
                "value": "aa:bb:cc",
            }
        ]
    ]

    policy.replies = [
        PolicyReply(**d)
        for d in [
            {
                "attribute": "Tunnel-Medium-Type",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "IEEE-802",
            },
            {
                "attribute": "Tunnel-Type",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "VLAN",
            },
            {
                "attribute": "Tunnel-Private-Group-Id",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "213",
            },
        ]
    ]

    db.add(policy)
    await db.commit()

    auth_json = {
        "username": "aa:bb:cc:dd:ee:ff",
        "nas_identifier": "eos-a1",
        "nas_port_id": "Ethernet1",
        "nas_port_type": "Ethernet",
        "calling_station_id": "aa:bb:cc:dd:ee:ff",  # type: ignore[arg-type]
        "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
        "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
    }

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # First auth with correct port.
    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("Tunnel-Medium-Type").get("value") == "IEEE-802"
    assert response.json().get("Tunnel-Type").get("value") == "VLAN"
    assert response.json().get("Tunnel-Private-Group-Id").get("value") == "213"

    # Switch name changed, called_station_id same -> Accepted
    # NasPort should update with this info
    auth_json["nas_identifier"] = "eos-a2"

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    assert response.status_code == status.HTTP_200_OK

    # called_station_id name, switch name changed, same -> Accepted
    # NasPort should update with this info
    auth_json["called_station_id"] = "00:00:00:00:00:02"

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    assert response.status_code == status.HTTP_200_OK

    db_nas_port = (
        await db.execute(select(NasPort).where(NasPort.username == "aa:bb:cc:dd:ee:ff"))
    ).scalar_one_or_none()

    assert db_nas_port
    assert db_nas_port.nas_identifier == "eos-a2"
    assert db_nas_port.called_station_id == "00:00:00:00:00:02"

    # Another port should be rejected
    auth_json["nas_port_id"] = "Ethernet2"

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_auth_port_type(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    mac = "aa:bb:cc:dd:ee:ff"

    policy = Policy(
        name="test_group_port_type",
        match_logic=MatchLogic.AND,
        enabled=True,
        port_type=PortType.WIRED,
    )

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "calling_station_id",
                "operator": ConditionOperator.STARTS_WITH,
                "value": "aa:bb:cc",
            }
        ]
    ]

    policy.replies = [
        PolicyReply(**d)
        for d in [
            {
                "attribute": "Tunnel-Medium-Type",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "IEEE-802",
            },
            {
                "attribute": "Tunnel-Type",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "VLAN",
            },
            {
                "attribute": "Tunnel-Private-Group-Id",
                "operator": ReplyOperator.SET_EQUALS,
                "value": "55",
            },
        ]
    ]

    db.add(policy)
    await db.commit()

    auth_json = {
        "username": mac,
        "nas_identifier": "a1",
        "nas_port_id": "Ethernet1",
        "nas_port_type": "Ethernet",
        "calling_station_id": mac,  # type: ignore[arg-type]
        "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
        "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
    }

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    ret_json = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert ret_json.get("Tunnel-Medium-Type").get("value") == "IEEE-802"
    assert ret_json.get("Tunnel-Type").get("value") == "VLAN"
    assert ret_json.get("Tunnel-Private-Group-Id").get("value") == "55"

    auth_json["nas_port_type"] = "Wireless-802.11"

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )
    ret_json = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
