from pydantic import BaseModel

from cnaas_nac.schemas.generic import TimestampSchema


class EndpointGroupBase(BaseModel):
    name: str


class EndpointGroupResponse(EndpointGroupBase, TimestampSchema):
    id: int
