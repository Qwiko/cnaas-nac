from typing import Optional

from pydantic import IPvAnyAddress
from cnaas_nac.schemas.generic import Username
from cnaas_nac.schemas.generic import TimestampSchema


class NasPortResponse(TimestampSchema):
    id: int
    endpoint_id: int

    username: Username
    nas_identifier: Optional[str] = None
    nas_port_id: Optional[str] = None
    nas_ip_address: IPvAnyAddress
    calling_station_id: Optional[str] = None
    called_station_id: Optional[str] = None
