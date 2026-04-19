import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.policy import (
    Policy,
    MatchLogic,
    ConditionOperator,
    PolicyCondition,
    PolicyReply,
    ReplyOperator,
)

pytestmark = pytest.mark.anyio


async def test_auth_endpoint_nasport(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    """Discovered MAC moves between ports."""
    policy = Policy(name="test_group", match_logic=MatchLogic.AND, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "calling_station_id",
                "operator": ConditionOperator.EQUALS,
                "value": "aa:bb:cc:dd:ee:ff",
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
        "username": "aa:bb:cc:dd:ee:ff",
        "nas_identifier": "a1",
        "nas_port_id": "Ethernet1",
        "nas_port_type": "Ethernet",
        "calling_station_id": "aa:bb:cc:dd:ee:ff",
        "called_station_id": "00:00:00:00:00:01",
        "nas_ip_address": "10.0.0.2",
    }

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )

    assert response.status_code == status.HTTP_200_OK

    auth_json["nas_port_id"] = "Ethernet2"

    response = await int_client.post(
        "/api/v2/auth",
        json=auth_json,
    )

    assert response.status_code == status.HTTP_200_OK
