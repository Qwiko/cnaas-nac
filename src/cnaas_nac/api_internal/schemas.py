from typing import Annotated, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    field_validator,
)
from pydantic_extra_types.mac_address import MacAddress
from cnaas_nac.core.settings import settings
from cnaas_nac.schemas.generic import Username


class InternalAuth(BaseModel):
    username: Username
    nas_identifier: Optional[str] = None
    nas_port_id: Optional[str] = None
    calling_station_id: Optional[MacAddress] = None
    called_station_id: Optional[MacAddress] = None
    nas_ip_address: Annotated[IPvAnyAddress, Field(examples=["1.1.1.1"])]

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
    ] = AttributeDetail(op=":=", value=settings.RADIUS.DEFAULT_VLAN)


class AccessReject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reply_message: Annotated[AttributeDetail, Field(..., alias="Reply-Message")] = (
        AttributeDetail(
            op=":=",
            value="Reply-Message",
        )
    )
