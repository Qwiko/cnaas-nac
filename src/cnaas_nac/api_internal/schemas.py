from typing import Annotated, Any, Literal, Optional

from netutils.mac import is_valid_mac, mac_to_format
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    computed_field,
    field_validator,
)

from cnaas_nac.core.settings import settings


class InternalAuth(BaseModel):
    username: str
    password: str
    nas_identifier: Optional[str] = None
    nas_port_id: Optional[str] = None
    calling_station_id: Optional[str] = None
    called_station_id: Optional[str] = None
    nas_ip_address: Annotated[IPvAnyAddress, Field(examples=["1.1.1.1"])]

    def __init__(self, **data):
        # Handle password field
        # Not sending a password field will default password = username
        if "password" not in data:
            data["password"] = data.get("username")
        super().__init__(**data)

    @field_validator("username", mode="after")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if is_valid_mac(v):
            return mac_to_format(v, "MAC_COLON_TWO")
        return v

    @field_validator("nas_ip_address", mode="after")
    @classmethod
    def nas_ip_as_string(cls, v: IPvAnyAddress) -> str:
        """Everything is mapped as a string later"""
        return str(v)


class AttributeDetail(BaseModel):
    op: Literal["=", ":="] = ":="
    value: str | int


class AccessAccept(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tunnel_type: Annotated[AttributeDetail, Field(..., alias="Tunnel-Type")] = (
        AttributeDetail(
            op=":=",
            value="VLAN",
        )
    )
    tunnel_medium_type: Annotated[
        AttributeDetail, Field(..., alias="Tunnel-Medium-Type")
    ] = AttributeDetail(op=":=", value="IEEE-802")
    tunnel_private_group_id: Annotated[
        AttributeDetail, Field(..., alias="Tunnel-Private-Group-Id")
    ] = AttributeDetail(op=":=", value=settings.RADIUS_DEFAULT_VLAN)


class AccessReject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reply_message: Annotated[AttributeDetail, Field(..., alias="Reply-Message")] = (
        AttributeDetail(
            op=":=",
            value="Reply-Message",
        )
    )
