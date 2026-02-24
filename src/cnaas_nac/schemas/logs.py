from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress
from cnaas_nac.schemas.generic import Username


class RadAcctLog(BaseModel):
    id: int = Field(validation_alias="radacctid")
    username: Username
    nasipaddress: IPvAnyAddress
    nasportid: str = None
    nasidentifier: Optional[str] = None
    acctstarttime: datetime = None
    acctstoptime: Optional[datetime] = None
    acctsessiontime: Optional[int] = None
    acctinputoctets: Optional[int] = None
    acctoutputoctets: Optional[int] = None


class RadPostAuthLog(BaseModel):
    id: int
    username: Username
    nasidentifier: Optional[str] = None
    nasportid: Optional[str] = None
    authdate: datetime = None
    reply_message: str = None

    @field_validator("reply_message", mode="after")
    def validate_reply_message(cls, v):
        if not v:
            return v

        # Convert 5C to newline char \
        return v.replace("5Cn", "\n")
