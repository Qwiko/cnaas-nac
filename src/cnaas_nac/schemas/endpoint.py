from typing import Annotated, Optional

from netutils.mac import get_oui
from pydantic import BaseModel, Field, computed_field

from cnaas_nac.schemas.generic import TimestampSchema, Username
from cnaas_nac.models.endpoint import EndpointState
from pydantic_extra_types.mac_address import MacAddress


class EndpointBase(BaseModel):
    group_id: Optional[int] = None
    description: Optional[str] = None


class EndpointCreate(EndpointBase):
    username: MacAddress

    @computed_field  # type: ignore[prop-decorator]
    @property
    def calling_station_id(self) -> str:
        return self.username


class EndpointUpdate(EndpointBase):
    pass


class EndpointResponse(EndpointBase, TimestampSchema):
    id: int
    username: Username

    calling_station_id: MacAddress
    state: EndpointState

    nas_identifier: Annotated[
        Optional[str], Field(description="Latest nas_identifier for this endpoint")
    ] = None
    nas_port_id: Annotated[
        Optional[str], Field(description="Latest nas_port_id for this endpoint")
    ] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def oui(self) -> str:
        try:
            value = get_oui(self.calling_station_id)
        except ValueError:
            value = "Unknown"
        return value
