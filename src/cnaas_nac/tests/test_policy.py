import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.rule_engine import evaluate_policy
from cnaas_nac.models.endpoint import EndpointGroup
from cnaas_nac.models.policy import (
    ConditionOperator,
    MatchLogic,
    Policy,
    PolicyCondition,
)

pytestmark = pytest.mark.anyio


async def test_policy_and(db: AsyncSession) -> None:
    # Add AssignmentRule
    policy = Policy(name="test_policy", match_logic=MatchLogic.AND, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "username",
                "operator": ConditionOperator.ENDS_WITH,
                "value": "@example.com",
            },
            {
                "attribute": "called_station_id",
                "operator": ConditionOperator.STARTS_WITH,
                "value": "00:01:02",
            },
        ]
    ]
    db.add(policy)
    await db.commit()
    await db.refresh(policy, attribute_names=["conditions"])

    assert evaluate_policy(
        policy, {"username": "test@example.com", "called_station_id": "00:01:02"}, None
    )
    assert not evaluate_policy(
        policy, {"username": "test@example.com", "called_station_id": "00:01:03"}, None
    )
    assert not evaluate_policy(policy, {"username": "test@other_domain.com"}, None)


async def test_policy_or(db: AsyncSession) -> None:
    # Add Policy
    policy = Policy(name="test_policy", match_logic=MatchLogic.OR, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "username",
                "operator": ConditionOperator.ENDS_WITH,
                "value": "@example.com",
            },
            {
                "attribute": "called_station_id",
                "operator": ConditionOperator.STARTS_WITH,
                "value": "00:01:02",
            },
        ]
    ]
    db.add(policy)
    await db.commit()
    await db.refresh(policy, attribute_names=["conditions"])

    assert evaluate_policy(
        policy, {"username": "test@example.com", "called_station_id": "00:01:02"}, None
    )
    assert evaluate_policy(
        policy, {"username": "test@example.com", "called_station_id": "00:01:03"}, None
    )
    assert evaluate_policy(
        policy,
        {"username": "test@other_domain.com", "called_station_id": "00:01:02"},
        None,
    )
    assert not evaluate_policy(policy, {"username": "test@other_domain.com"}, None)


async def test_policy_in_list(db: AsyncSession) -> None:
    # Add Policy
    # TODO Improve this test
    policy = Policy(name="test_policy", match_logic=MatchLogic.AND, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "username",
                "operator": ConditionOperator.ENDS_WITH,
                "value": "@example.com",
            },
            {
                "attribute": "ldap_groups",
                "operator": ConditionOperator.IN_LIST,
                "value": "GROUP_1",
            },
        ]
    ]
    db.add(policy)
    await db.commit()
    await db.refresh(policy, attribute_names=["conditions"])

    assert not evaluate_policy(policy, {"username": "test@example.com"}, None)

    assert evaluate_policy(
        policy, {"username": "test@example.com", "ldap_groups": ["GROUP_1"]}, None
    )


async def test_policy_group_id(db: AsyncSession) -> None:
    # Add Endpoint Group and Policy
    endpoint_group = EndpointGroup(name="test_group", id=45456)
    policy = Policy(name="test_policy", match_logic=MatchLogic.AND, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "group_id",
                "operator": ConditionOperator.EQUALS,
                "value": 45456,
            },
        ]
    ]
    db.add(endpoint_group)
    db.add(policy)
    await db.commit()
    await db.refresh(policy, attribute_names=["conditions"])

    # group_id is populated during auth, not part of the request data from FreeRadius
    assert evaluate_policy(policy, {}, group_id=45456)
    assert not evaluate_policy(policy, {}, group_id=124)


async def test_policy_regex(db: AsyncSession) -> None:
    # Add Policy
    policy = Policy(name="test_policy", match_logic=MatchLogic.AND, enabled=True)

    policy.conditions = [
        PolicyCondition(**d)
        for d in [
            {
                "attribute": "username",
                "operator": ConditionOperator.REGEX,
                "value": r"^test\d+@example\.com$",
            },
        ]
    ]
    db.add(policy)
    await db.commit()
    await db.refresh(policy, attribute_names=["conditions"])

    assert evaluate_policy(policy, {"username": "test123@example.com"})
    assert not evaluate_policy(policy, {"username": "test@example.com"})
