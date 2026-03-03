from typing import Annotated, List, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cnaas_nac.models.policy import (
    ClientType,
    ConditionOperator,
    MatchLogic,
    PortLocking,
    PortType,
    ReplyOperator,
)


class PolicyReplyBase(BaseModel):
    """Shared properties for Policy Replies."""

    attribute: str = Field(..., max_length=100)
    operator: ReplyOperator
    value: str = Field(..., max_length=255)


class PolicyConditionBase(BaseModel):
    """Shared properties for Policy Conditions."""

    attribute: str = Field(..., max_length=100)
    operator: ConditionOperator
    value: str | int

    @model_validator(mode="after")
    def validate_group_id_operator(self) -> Self:
        if self.attribute == "group_id" and self.operator != ConditionOperator.EQUALS:
            raise ValueError("Attribute group_id must be used with operator EQUALS.")

        return self


class PolicyConditionCreate(PolicyConditionBase):
    pass


class PolicyConditionUpdate(PolicyConditionBase):
    pass


class PolicyConditionResponse(PolicyConditionBase):
    """Properties to return to the client."""

    id: int
    rule_id: int

    # Enables Pydantic to read data from SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)


class PolicyBase(BaseModel):
    """Shared properties for Assignment Rules."""

    name: str = Field(..., max_length=100)
    description: Annotated[Optional[str], Field(..., max_length=255)] = None
    priority: int = Field(default=100)
    match_logic: MatchLogic = Field(default=MatchLogic.AND)
    client_type: Optional[ClientType] = None
    port_type: Optional[PortType] = None
    port_locking: Optional[PortLocking] = None
    enabled: bool = Field(default=True)

    conditions: List[PolicyConditionCreate] = Field(default_factory=list)

    replies: List[PolicyReplyBase] = Field(default_factory=list)


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(PolicyBase):
    pass


class PolicyResponse(PolicyBase):
    id: int
