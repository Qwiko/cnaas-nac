from typing import Optional

from pydantic import BaseModel, IPvAnyAddress
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


class DebugLog(BaseModel):
    id: int
    node_name: str
    log_line: str
