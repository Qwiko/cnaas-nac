from typing import Optional

from pydantic import BaseModel

from pydantic import AwareDatetime
from cnaas_nac.core.settings import settings
from cnaas_nac.schemas.generic import Username, VlanID
from cnaas_nac.schemas.generic import TimestampSchema

class UserBase(BaseModel):
    enabled: bool = False
    vlan: VlanID = settings.RADIUS.DEFAULT_VLAN
    access_start: Optional[AwareDatetime] = None
    access_stop: Optional[AwareDatetime] = None


class UserCreate(UserBase):
    username: Username


class UserUpdate(UserBase):
    pass


class UserResponse(UserBase, TimestampSchema):
    username: Username
