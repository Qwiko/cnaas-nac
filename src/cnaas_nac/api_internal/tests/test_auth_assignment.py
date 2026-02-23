import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.api_internal.schemas import InternalAuth
from cnaas_nac.models.assignment_rule import (
    AssignmentRule,
    MatchLogic,
    Operator,
    RuleCondition,
)

pytestmark = pytest.mark.anyio


async def test_auth_assignment(
    db: AsyncSession,
    int_client: AsyncClient,
) -> None:
    # Add Assignement Rule

    ar = AssignmentRule(
        name="Test_AR", target_vlan=213, match_logic=MatchLogic.ALL, is_active=True
    )

    ar.conditions = [
        RuleCondition(**d)
        for d in [
            {
                "attribute": "calling_station_id",
                "operator": Operator.STARTS_WITH,
                "target_value": "aa:bb:cc",
            }
        ]
    ]
    db.add(ar)
    await db.commit()

    auth = InternalAuth(
        **{
            "username": "aa:bb:cc:dd:ee:ff",
            "nas_identifier": "a1",
            "nas_port_id": "Ethernet1",
            "calling_station_id": "AA-BB-CC-DD-EE-FF",  # type: ignore[arg-type]
            "called_station_id": "00:00:00:00:00:01",  # type: ignore[arg-type]
            "nas_ip_address": "10.0.0.2",  # type: ignore[arg-type]
        }
    )

    response = await int_client.post(
        "/api/v2/auth",
        json=auth.model_dump(),
    )
    ret_json = response.json()
    assert response.status_code == status.HTTP_200_OK

    assert ret_json.get("Tunnel-Medium-Type").get("value") == "IEEE-802"
    assert ret_json.get("Tunnel-Type").get("value") == "VLAN"
    assert ret_json.get("Tunnel-Private-Group-Id").get("value") == "213"
