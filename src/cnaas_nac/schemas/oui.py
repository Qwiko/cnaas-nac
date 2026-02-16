from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DeviceOuiBase(BaseModel):
    oui: str
    vlan: int = Field(..., ge=1, le=4094, description="VLAN ID range")
    description: Optional[str] = ""
    
    @field_validator("oui", mode="after")
    @classmethod
    def validate_oui(cls, v: str) -> str:
        # Remove separator
        for seperator in [":", "-"]:
            v = v.replace(seperator, "")
        
        if len(v) != 6:
            raise ValueError("oui is not valid, must be in format: '012345', '01:23:34' or '01-23-34'")    
        
        # Normalize to 00:00:00
        v = ':'.join(v[i:i+2] for i in range(0, 6, 2))
        return v

class DeviceOuiResponse(DeviceOuiBase):
    id: int
