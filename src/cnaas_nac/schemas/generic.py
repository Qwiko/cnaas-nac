from typing import Annotated, Literal
from netutils.mac import mac_to_format, is_valid_mac
from pydantic import BaseModel, Field, AfterValidator, AwareDatetime
from pydantic_extra_types.mac_address import MacAddress as PydanticMacAddress


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str


class Error(BaseModel):
    root: dict
    field: str


class ErrorBody(BaseModel):
    errors: Error


class ValidationErrorResponse(BaseModel):
    body: ErrorBody


def format_mac(v: str) -> str:
    if is_valid_mac(v):
        v = mac_to_format(v, "MAC_COLON_TWO")
    return v


class TimestampSchema(BaseModel):
    created_at: AwareDatetime
    updated_at: AwareDatetime


VlanID = Annotated[int, Field(..., ge=1, le=4094, description="VLAN ID range")]
Username = Annotated[
    str | PydanticMacAddress,
    Field(..., description="Username"),
    AfterValidator(format_mac),
]
# Specific mac_address type that can be reused in other schemas, with validation and formatting.
MacAddress = Annotated[
    PydanticMacAddress,
    Field(..., description="MAC address"),
    AfterValidator(format_mac),
]
