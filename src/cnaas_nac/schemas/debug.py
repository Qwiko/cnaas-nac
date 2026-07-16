from typing import Optional, Self

from pydantic import BaseModel, IPvAnyAddress, model_validator
from pydantic_extra_types.mac_address import MacAddress

from cnaas_nac.models.policy import PortType
from cnaas_nac.schemas.generic import Username


class DebugBase(BaseModel):
    username: Optional[Username] = None
    nas_identifier: Optional[str] = None
    nas_port_id: Optional[str] = None
    nas_port_type: Optional[PortType] = None
    calling_station_id: Optional[MacAddress] = None
    called_station_id: Optional[MacAddress] = None
    nas_ip_address: Optional[IPvAnyAddress] = None
    realm: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if not any(getattr(self, field) is not None for field in self.model_fields):
            raise ValueError("At least one field must be set.")
        return self


class DebugLog(BaseModel):
    id: int
    node_name: str
    log_line: str
