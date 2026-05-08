from typing import Optional

from pydantic import IPvAnyAddress, IPvAnyNetwork, BaseModel, field_validator
from cnaas_nac.schemas.generic import TimestampSchema


class NasBase(BaseModel):
    name: str
    network: IPvAnyNetwork
    description: Optional[str] = None
    server: Optional[str] = "default"

    coa_enabled: Optional[bool] = False
    coa_port: Optional[int] = 3799

    @field_validator("network", mode="after")
    @classmethod
    def network_as_string(cls, v: IPvAnyAddress) -> str:
        """Everything is mapped as a string later"""
        return str(v)


class NasCreateUpdate(NasBase):
    secret: str
    coa_secret: Optional[str] = None


class NasResponse(NasBase, TimestampSchema):
    id: int


class NasOne(NasResponse):
    secret: str
    coa_secret: Optional[str] = None
