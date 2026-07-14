from typing import Optional

from pydantic import IPvAnyNetwork, BaseModel, field_validator
from cnaas_nac.schemas.generic import TimestampSchema
from ipaddress import ip_network


class NasBase(BaseModel):
    name: str
    network: IPvAnyNetwork
    description: Optional[str] = None
    server: Optional[str] = "default"

    coa_enabled: Optional[bool] = False
    coa_port: Optional[int] = 3799

    @field_validator("network", mode="after")
    @classmethod
    def network_as_string(cls, v: IPvAnyNetwork) -> str:
        """Everything is mapped as a string later"""
        return str(v)


class NasCreateUpdate(NasBase):
    secret: str
    coa_secret: Optional[str] = None

    @field_validator("network", mode="after")
    @classmethod
    def network_validation(cls, v: str) -> str:
        """
        Validate that the network does not contain more than 4098 addresses
        This is due to a limitation in the freeradius radmin tool, which must iterate over all addresses in the network to clear them from the radius server.
        """
        if ip_network(v).num_addresses > 4098:
            raise ValueError("Network cannot contain more than 4098 addresses")

        return str(v)


class NasResponse(NasBase, TimestampSchema):
    id: int


class NasOne(NasResponse):
    secret: str
    coa_secret: Optional[str] = None
