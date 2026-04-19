import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.endpoint import Endpoint, EndpointGroup, EndpointState
from cnaas_nac.models.policy import (
    Policy,
    MatchLogic,
    ConditionOperator,
    PolicyCondition,
    PolicyReply,
    ReplyOperator,
)
from cnaas_nac.models.radpostauth import RadPostAuth

pytestmark = pytest.mark.anyio


async def test_auth_endpoint_group(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    await db.execute(delete(RadPostAuth))
    await db.execute(delete(PolicyCondition))
    await db.execute(delete(PolicyReply))
    await db.execute(delete(Policy))
    await db.execute(delete(Endpoint))
    await db.execute(delete(EndpointGroup))

    mac = "aa:bb:cc:dd:ee:ff"

    # Add Endpoint group
    group = EndpointGroup(name="Vlan55")

    endpoint = Endpoint(
        username=mac, calling_station_id=mac, state=EndpointState.PENDING, group=group
    )

    db.add(group)
    db.add(endpoint)
    await db.commit()

    policy = Policy(name="test_group", match_logic=MatchLogic.AND, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "group_id",
                "operator": ConditionOperator.EQUALS,
                "value": group.id,
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
        "calling_station_id": mac,
        "called_station_id": "00:00:00:00:00:01",
        "nas_ip_address": "10.0.0.2",
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


async def test_auth_many_endpoint_groups(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    await db.execute(delete(RadPostAuth))
    await db.execute(delete(PolicyCondition))
    await db.execute(delete(PolicyReply))
    await db.execute(delete(Policy))
    await db.execute(delete(Endpoint))
    await db.execute(delete(EndpointGroup))

    # Add alot of groups and policies
    for i in range(50, 100):
        group = EndpointGroup(name=f"Vlan{i}", id=i)

        db.add(group)

        policy = Policy(
            name=f"test_group_{i}",
            match_logic=MatchLogic.AND,
            enabled=True,
            priority=10 if i != 55 else None,
        )

        policy.conditions = [
            PolicyCondition(**d)
            for d in [
                {
                    "attribute": "group_id",
                    "operator": ConditionOperator.EQUALS,
                    "value": i,
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
                    "value": str(i),
                },
            ]
        ]

        db.add(policy)

    mac = "aa:bb:cc:dd:ee:ff"

    endpoint = Endpoint(
        username=mac, calling_station_id=mac, state=EndpointState.PENDING, group_id=55
    )
    db.add(endpoint)
    await db.commit()

    auth_json = {
        "username": mac,
        "nas_identifier": "a1",
        "nas_port_id": "Ethernet1",
        "nas_port_type": "Ethernet",
        "calling_station_id": mac,
        "called_station_id": "00:00:00:00:00:01",
        "nas_ip_address": "10.0.0.2",
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
