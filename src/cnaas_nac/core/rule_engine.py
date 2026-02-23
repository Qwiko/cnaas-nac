import re
from typing import Dict, Any


from cnaas_nac.models.assignment_rule import (
    AssignmentRule,
    RuleCondition,
    MatchLogic,
    Operator,
)
from cnaas_nac.core.logging import get_logger

logger = get_logger()


def evaluate_condition(condition: RuleCondition, data: Dict[str, Any]) -> bool:
    """Evaluates a single condition against the request data."""

    request_value = data.get(condition.attribute)
    logger.debug(
        f"Rule: {condition.rule_id}, value: {request_value}, operator: {condition.operator}, target: {condition.target_value}"
    )

    # If the attribute isn't in the request at all, the condition fails
    if request_value is None:
        return False

    target = condition.target_value

    # Handle IN_LIST logic
    if condition.operator == Operator.IN_LIST:
        # Ensure the incoming data is actually a list before checking
        if isinstance(request_value, list):
            return target in request_value
        return False

    # Ensure both are strings for comparison, or handle types as needed
    request_value = str(request_value)

    if condition.operator == Operator.EQUALS:
        return request_value == target
    elif condition.operator == Operator.NOT_EQUALS:
        return request_value != target
    elif condition.operator == Operator.CONTAINS:
        return target in request_value
    elif condition.operator == Operator.STARTS_WITH:
        return request_value.startswith(target)
    elif condition.operator == Operator.ENDS_WITH:
        return request_value.endswith(target)
    elif condition.operator == Operator.REGEX:
        try:
            return bool(re.search(target, request_value))
        except re.error:
            return False  # Invalid regex fails safely

    return False


def evaluate_rule(rule: AssignmentRule, data: Dict[str, Any]) -> bool:
    """Evaluates a full rule based on its MatchLogic (AND/OR)."""
    if not rule.conditions:
        return False  # A rule with no conditions shouldn't match anything

    if rule.match_logic == MatchLogic.ALL:
        # AND logic: all conditions must be True
        return all(evaluate_condition(c, data) for c in rule.conditions)
    else:
        # OR logic: at least one condition must be True
        return any(evaluate_condition(c, data) for c in rule.conditions)
