import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.assignment_rule import (
    AssignmentRule,
    RuleCondition,
    MatchLogic,
    Operator,
)

from cnaas_nac.core.rule_engine import evaluate_rule

pytestmark = pytest.mark.anyio


async def test_assignment_rule_and(db: AsyncSession) -> None:
    # Add AssignmentRule
    ar = AssignmentRule(
        name="Test_AR", target_vlan=213, match_logic=MatchLogic.ALL, is_active=True
    )

    ar.conditions = [
        RuleCondition(**d)
        for d in [
            {
                "attribute": "username",
                "operator": Operator.ENDS_WITH,
                "target_value": "@example.com",
            },
            {
                "attribute": "called_station_id",
                "operator": Operator.STARTS_WITH,
                "target_value": "00:01:02",
            },
        ]
    ]
    db.add(ar)
    await db.commit()
    await db.refresh(ar, attribute_names=["conditions"])

    assert evaluate_rule(
        ar, {"username": "test@example.com", "called_station_id": "00:01:02"}
    )
    assert not evaluate_rule(
        ar, {"username": "test@example.com", "called_station_id": "00:01:03"}
    )
    assert not evaluate_rule(ar, {"username": "test@other_domain.com"})


async def test_assignment_rule_or(db: AsyncSession) -> None:
    # Add AssignmentRule
    ar = AssignmentRule(
        name="Test_AR", target_vlan=213, match_logic=MatchLogic.ANY, is_active=True
    )

    ar.conditions = [
        RuleCondition(**d)
        for d in [
            {
                "attribute": "username",
                "operator": Operator.ENDS_WITH,
                "target_value": "@example.com",
            },
            {
                "attribute": "called_station_id",
                "operator": Operator.STARTS_WITH,
                "target_value": "00:01:02",
            },
        ]
    ]
    db.add(ar)
    await db.commit()
    await db.refresh(ar, attribute_names=["conditions"])

    assert evaluate_rule(
        ar, {"username": "test@example.com", "called_station_id": "00:01:02"}
    )
    assert evaluate_rule(
        ar, {"username": "test@example.com", "called_station_id": "00:01:03"}
    )
    assert evaluate_rule(
        ar, {"username": "test@other_domain.com", "called_station_id": "00:01:02"}
    )
    assert not evaluate_rule(ar, {"username": "test@other_domain.com"})


async def test_assignment_rule_in_list(db: AsyncSession) -> None:
    # Add AssignmentRule
    ar = AssignmentRule(
        name="Test_AR", target_vlan=213, match_logic=MatchLogic.ALL, is_active=True
    )

    ar.conditions = [
        RuleCondition(**d)
        for d in [
            {
                "attribute": "username",
                "operator": Operator.ENDS_WITH,
                "target_value": "@example.com",
            },
            {
                "attribute": "ldap_groups",
                "operator": Operator.IN_LIST,
                "target_value": "GROUP_1",
            },
        ]
    ]
    db.add(ar)
    await db.commit()
    await db.refresh(ar, attribute_names=["conditions"])

    assert not evaluate_rule(ar, {"username": "test@example.com"})
