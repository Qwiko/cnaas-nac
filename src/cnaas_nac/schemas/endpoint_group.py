from pydantic import BaseModel


class EndpointGroupBase(BaseModel):
    name: str


class EndpointGroupResponse(EndpointGroupBase):
    id: int
