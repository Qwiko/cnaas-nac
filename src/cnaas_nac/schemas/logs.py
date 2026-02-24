from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress
from cnaas_nac.schemas.generic import Username


class RadAcctLog(BaseModel):
    id: int
    username: Username
    nas_ip_address: IPvAnyAddress
    nas_port_id: str = None
    nas_identifier: Optional[str] = None
    acct_start_time: datetime = None
    acct_stop_time: Optional[datetime] = None
    acct_session_time: Optional[int] = None
    acct_input_octets: Optional[int] = None
    acct_output_octets: Optional[int] = None


class RadPostAuthLog(BaseModel):
    id: int
    username: Username
    nas_identifier: Optional[str] = None
    nas_port_id: Optional[str] = None
    auth_date: datetime = None
    reply_message: str = None

    @field_validator("reply_message", mode="after")
    def validate_reply_message(cls, v):
        if not v:
            return v

        # Convert 5C to newline char \
        return v.replace("5Cn", "\n")
