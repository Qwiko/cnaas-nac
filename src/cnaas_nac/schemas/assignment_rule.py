from typing import Optional

from pydantic import BaseModel


from typing import List
from pydantic import ConfigDict, Field

from cnaas_nac.models.assignment_rule import MatchLogic, Operator

# -------------------------------------------------------------------
# Rule Condition Schemas
# -------------------------------------------------------------------


class RuleConditionBase(BaseModel):
    """Shared properties for Rule Conditions."""

    attribute: str = Field(..., max_length=100)
    operator: Operator
    target_value: str = Field(..., max_length=255)


class RuleConditionCreate(RuleConditionBase):
    """Properties to receive on condition creation."""

    pass
    # Note: rule_id is intentionally omitted here as it's usually
    # inferred from the URL path or handled by the parent rule creation.


class RuleConditionUpdate(BaseModel):
    """Properties to receive on condition update (all optional)."""

    attribute: Optional[str] = Field(None, max_length=100)
    operator: Optional[Operator] = None
    target_value: Optional[str] = Field(None, max_length=255)


class RuleConditionResponse(RuleConditionBase):
    """Properties to return to the client."""

    id: int
    rule_id: int

    # Enables Pydantic to read data from SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)


class AssignmentRuleBase(BaseModel):
    """Shared properties for Assignment Rules."""

    name: str = Field(..., max_length=100)
    priority: int = Field(default=100)
    target_vlan: int
    match_logic: MatchLogic = Field(default=MatchLogic.ALL)
    reevaluate_existing: bool = Field(default=False)
    is_active: bool = Field(default=True)

    conditions: List[RuleConditionCreate] = Field(default_factory=list)


class AssignmentRuleCreate(AssignmentRuleBase):
    pass


class AssignmentRuleUpdate(AssignmentRuleBase):
    pass


class AssignmentRuleResponse(AssignmentRuleBase):
    id: int
