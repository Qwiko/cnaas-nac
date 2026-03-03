from typing import Optional
from pydantic import BaseModel, model_validator

from cnaas_nac.schemas.generic import VlanID


class VlanBase(BaseModel):
    vlan: VlanID
    name: Optional[str]

    @model_validator(mode="before")
    def default_name(cls, values):
        if not values.get("name"):
            values["name"] = f"VLAN {values['vlan']}"
        return values


class VlanResponse(VlanBase):
    pass
