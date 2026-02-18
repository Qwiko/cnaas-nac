from typing import Optional, Annotated

from pydantic import BaseModel, Field, field_validator

from pydantic import AwareDatetime
from cnaas_nac.core.settings import settings
from cnaas_nac.schemas.generic import Username, VlanID


class AuthBase(BaseModel):
    enabled: Optional[bool] = False
    vlan: Optional[VlanID] = settings.RADIUS_DEFAULT_VLAN
    access_start: Optional[AwareDatetime] = None
    access_stop: Optional[AwareDatetime] = None


class AuthCreate(AuthBase):
    username: Username


class AuthUpdate(AuthBase):
    pass


class AuthResponse(AuthBase):
    id: int
    username: Username
