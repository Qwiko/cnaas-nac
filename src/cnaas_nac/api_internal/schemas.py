from typing import Annotated, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    computed_field,
    field_validator,
)
from pydantic_extra_types.mac_address import MacAddress

from cnaas_nac.models.policy import ClientType, PortType
from cnaas_nac.schemas.generic import Username
from netutils.mac import is_valid_mac


class InternalAuth(BaseModel):
    # model_config = ConfigDict(use_enum_values=True)

    username: Username
    nas_identifier: Optional[str] = None
    nas_port_id: str
    nas_port_type: PortType
    calling_station_id: Annotated[MacAddress, Field(examples=["00:00:00:00:00:00"])]
    called_station_id: Annotated[MacAddress, Field(examples=["00:00:00:00:00:00"])]
    nas_ip_address: Annotated[IPvAnyAddress, Field(examples=["1.1.1.1"])]
    ldap_groups: Annotated[list[str], Field(examples=[["admins", "employees"]])] = []

    @field_validator('ldap_groups', mode='before')
    @classmethod
    def parse_radius_groups(cls, value):
        if isinstance(value, str):
            if not value.strip():
                return []
            return [group.strip() for group in value.split(',') if group.strip()]
        
        return value

    @field_validator("nas_ip_address", mode="after")
    @classmethod
    def nas_ip_as_string(cls, v: IPvAnyAddress) -> str:
        """Everything is mapped as a string later"""
        return str(v)

    @computed_field()  # type: ignore[prop-decorator]
    @property
    def client_type(self) -> ClientType:
        if is_valid_mac(self.username):
            return ClientType.MAB
        return ClientType.EAP


class AttributeDetail(BaseModel):
    op: Literal["=", ":="] = ":="
    value: str


# class AccessAccept(BaseModel):
#     model_config = ConfigDict(populate_by_name=True)

#     tunnel_type: Annotated[AttributeDetail, Field(..., alias="Tunnel-Type")] = (
#         AttributeDetail(
#             op=":=",
#             value="VLAN",
#         )
#     )
#     tunnel_medium_type: Annotated[
#         AttributeDetail, Field(..., alias="Tunnel-Medium-Type")
#     ] = AttributeDetail(op=":=", value="IEEE-802")
#     tunnel_private_group_id: Annotated[
#         AttributeDetail, Field(..., alias="Tunnel-Private-Group-Id")
#     ] = AttributeDetail(op=":=", value=settings.RADIUS.DEFAULT_VLAN)


class AccessReject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    auth_type: Annotated[AttributeDetail, Field(..., alias="control:Auth-Type")] = (
        AttributeDetail(
            op=":=",
            value="Reject",
        )
    )
    policy_id: Annotated[
        Optional[AttributeDetail], Field(..., alias="NAC-Policy-Id")
    ] = None

    error_message: Annotated[AttributeDetail, Field(..., alias="NAC-Error-Message")] = (
        AttributeDetail(
            op=":=",
            value="NAC-Error-Message",
        )
    )
