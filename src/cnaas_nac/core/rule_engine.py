import re
from typing import Dict, Any, Optional


from cnaas_nac.models.endpoint import Endpoint
from cnaas_nac.models.policy import (
    Policy,
    PolicyCondition,
    MatchLogic,
    ConditionOperator,
)
from cnaas_nac.core.logging import get_logger

logger = get_logger()


def evaluate_condition(
    condition: PolicyCondition, data: Dict[str, Any], group_id: Optional[int]
) -> bool:
    """Evaluates a single condition against the request data."""
    if condition.attribute == "group_id":
        # group_id is always EQUALS.
        if not group_id:
            return False
        return condition.value == group_id
    else:
        request_value = data.get(condition.attribute)
    logger.debug(
        f"Policy: {condition.policy.name}({condition.policy_id}), attribute: {condition.attribute}, real_value: {request_value}, operator: {condition.operator}, expected_value: {condition.value}"
    )

    # If the attribute isn't in the request at all, the condition fails
    if request_value is None:
        return False

    target_value = condition.value

    # Handle IN_LIST logic
    if condition.operator == ConditionOperator.IN_LIST:
        # Ensure the incoming data is actually a list before checking
        if isinstance(request_value, list):
            return target_value in request_value
        return False

    # Make sure request_value is a string past this point.
    request_value = str(request_value)
    target_value = str(target_value)

    if condition.operator == ConditionOperator.EQUALS:
        return request_value == target_value
    elif condition.operator == ConditionOperator.NOT_EQUALS:
        return request_value != target_value
    elif condition.operator == ConditionOperator.CONTAINS:
        return target_value in request_value
    elif condition.operator == ConditionOperator.STARTS_WITH:
        return request_value.startswith(target_value)
    elif condition.operator == ConditionOperator.ENDS_WITH:
        return request_value.endswith(target_value)
    elif condition.operator == ConditionOperator.REGEX:
        try:
            return bool(re.search(target_value, request_value))
        except re.error:
            return False  # Invalid regex fails safely

    return False


def evaluate_policy(
    rule: Policy, data: Dict[str, Any], group_id: Optional[int]
) -> bool:
    """Evaluates a full rule based on its MatchLogic (AND/OR)."""
    if not rule.conditions:
        return False  # A rule with no conditions shouldn't match anything

    if rule.match_logic == MatchLogic.AND:
        # AND logic: all conditions must be True
        return all(evaluate_condition(c, data, group_id) for c in rule.conditions)
    else:
        # OR logic: at least one condition must be True
        return any(evaluate_condition(c, data, group_id) for c in rule.conditions)
