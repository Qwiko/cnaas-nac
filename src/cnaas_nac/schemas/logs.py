from datetime import datetime
from typing import Optional

from pydantic import BaseModel, IPvAnyAddress

from cnaas_nac.schemas.generic import Username


class RadAcctLog(BaseModel):
    id: int
    username: Username
    nas_ip_address: IPvAnyAddress
    nas_port_id: str
    nas_identifier: Optional[str] = None
    acct_start_time: datetime
    acct_stop_time: Optional[datetime] = None
    acct_session_time: Optional[int] = None
    acct_input_octets: Optional[int] = None
    acct_output_octets: Optional[int] = None


class RadPostAuthLog(BaseModel):
    id: int
    username: Username
    nas_identifier: Optional[str] = None
    nas_port_id: Optional[str] = None
    auth_date: datetime
    reply: str
    matched_policy: Optional[str] = None
    error_message: Optional[str] = None

    # @field_validator("error_message", mode="after")
    # def validate_reply_message(cls, v):
    #     if not v:
    #         return v

    #     decoded_bytes = quopri.decodestring(v)
    #     decoded_str = decoded_bytes.decode("utf-8")

    #     return decoded_str
