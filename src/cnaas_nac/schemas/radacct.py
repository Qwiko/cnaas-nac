from datetime import datetime
from ipaddress import IPv4Address, IPv6Address, IPv6Network
from typing import Optional

from pydantic import BaseModel, IPvAnyAddress
from pydantic_extra_types.mac_address import MacAddress

from cnaas_nac.schemas.generic import Username


class RadAcctLog(BaseModel):
    id: int
    endpoint_id: Optional[int] = None

    username: Username
    realm: Optional[str] = None
    calling_station_id: MacAddress
    nas_ip_address: IPvAnyAddress
    nas_port_id: str
    nas_identifier: Optional[str] = None
    acct_start_time: datetime
    acct_update_time: Optional[datetime] = None
    acct_stop_time: Optional[datetime] = None
    acct_session_time: Optional[int] = None
    acct_input_octets: Optional[int] = None
    acct_output_octets: Optional[int] = None


class RadAcctLogFull(RadAcctLog):
    acct_terminate_cause: Optional[str] = None
    service_type: Optional[str] = None
    framed_protocol: Optional[str] = None
    framed_ip_address: Optional[IPv4Address] = None
    framed_ipv6_address: Optional[IPv6Address] = None
    framed_ipv6_prefix: Optional[IPv6Network] = None
    framed_interface_id: Optional[str] = None
    delegated_ipv6_prefix: Optional[IPv6Network] = None
