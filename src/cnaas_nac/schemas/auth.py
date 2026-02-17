from typing import Optional, Annotated

from pydantic import BaseModel, Field, field_validator

from pydantic import AwareDatetime
from cnaas_nac.core.settings import settings
from netutils.mac import is_valid_mac, mac_to_format


class AuthBase(BaseModel):
    enabled: Optional[bool] = False
    vlan: Optional[
        Annotated[int, Field(..., ge=1, le=4094, description="VLAN ID range")]
    ] = settings.RADIUS_DEFAULT_VLAN
    access_start: Optional[AwareDatetime] = None
    access_stop: Optional[AwareDatetime] = None

class AuthCreate(AuthBase):
    username: str


    @field_validator("username", mode="after")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if is_valid_mac(v):
            return mac_to_format(v, "MAC_COLON_TWO")
        return v

class AuthUpdate(AuthBase):
    pass


class AuthResponse(AuthBase):
    id: int
