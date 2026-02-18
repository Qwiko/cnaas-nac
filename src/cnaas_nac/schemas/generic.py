from typing import Annotated, Literal
from netutils.mac import mac_to_format, is_valid_mac
from pydantic import BaseModel, Field, AfterValidator
from pydantic_extra_types.mac_address import MacAddress


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str


def format_mac(v: str) -> str:
    if is_valid_mac(v):
        return mac_to_format(v, "MAC_COLON_TWO")
    return v


VlanID = Annotated[int, Field(..., ge=1, le=4094, description="VLAN ID range")]
Username = Annotated[
    str | MacAddress, Field(..., description="Username"), AfterValidator(format_mac)
]
