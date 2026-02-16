from typing import Optional, Annotated

from pydantic import BaseModel, Field

from pydantic import AwareDatetime
from cnaas_nac.core.settings import settings


class AuthBase(BaseModel):
    username: str
    enabled: Optional[bool] = False
    vlan: Optional[
        Annotated[int, Field(..., ge=1, le=4094, description="VLAN ID range")]
    ] = settings.RADIUS_DEFAULT_VLAN
    access_start: Optional[AwareDatetime] = None
    access_stop: Optional[AwareDatetime] = None


class AuthResponse(AuthBase):
    id: int
