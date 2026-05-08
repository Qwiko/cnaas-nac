from typing import Annotated, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from cnaas_nac.models.policy import (
    ClientType,
    ConditionOperator,
    MatchLogic,
    PortLocking,
    PortType,
)
from cnaas_nac.schemas.generic import TimestampSchema


class PolicyReplyBase(BaseModel):
    """Shared properties for Policy Replies."""

    attribute: str = Field(..., max_length=100)
    value: str = Field(..., max_length=255)

    @field_validator("value", mode="after")
    @classmethod
    def validate_vlan_is_integer(cls, value: str, info: ValidationInfo) -> str:
        target_attr = info.data.get("attribute")
        if target_attr == "Tunnel-Private-Group-Id":
            if not value.isnumeric():
                raise ValueError("must be a number.")
            if int(value) < 1 or int(value) > 4094:
                raise ValueError("must be between 1 and 4094.")
        return value


class PolicyConditionBase(BaseModel):
    """Shared properties for Policy Conditions."""

    attribute: str = Field(..., max_length=100)
    operator: ConditionOperator
    value: str | int

    @field_validator("operator", mode="after")
    @classmethod
    def validate_group_id_operator(
        cls, operator: ConditionOperator, info: ValidationInfo
    ) -> ConditionOperator:
        target_attr = info.data.get("attribute")
        if target_attr == "group_id" and operator != ConditionOperator.EQUALS:
            raise ValueError("attribute group_id must be used with operator EQUALS.")

        return operator


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

    conditions: List[PolicyConditionCreate]

    replies: List[PolicyReplyBase]
    
    @field_validator("conditions", mode="after")
    @classmethod
    def validate_conditions(cls, value: List[PolicyConditionCreate]) -> List[PolicyConditionCreate]:
        if len(value) == 0:
            raise ValueError("At least one condition is required.")
        return value

    @field_validator("replies", mode="after")
    @classmethod
    def validate_replies(cls, value: List[PolicyReplyBase]) -> List[PolicyReplyBase]:
        if len(value) == 0:
            raise ValueError("At least one reply is required.")
        return value

class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(PolicyBase):
    pass


class PolicyResponse(PolicyBase, TimestampSchema):
    id: int
