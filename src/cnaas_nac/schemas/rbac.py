from typing import Annotated, Literal
from pydantic import BaseModel, Field, PositiveInt, field_validator


class RBACPermissionModel(BaseModel):
    resource: Literal[
        "accounting",
        "authentication",
        "endpoint_group",
        "endpoint",
        "nas_port",
        "policy",
        "radius_client",
        "rbac",
        "vlan",
    ]
    methods: list[Literal["GET", "POST", "PUT", "DELETE"]]


# Base properties shared across multiple schemas
class RBACBase(BaseModel):
    name: str

    permissions: list[RBACPermissionModel]

    @field_validator("permissions", mode="after")
    @classmethod
    def validate_unique_list(
        cls, value: list[RBACPermissionModel]
    ) -> list[RBACPermissionModel]:
        resource_list = [v.resource for v in value]
        if len(resource_list) != len(set(resource_list)):
            raise ValueError("resource need to be unique, between permissions.")
        return value


class RBACCreate(RBACBase):
    allowed_endpoint_groups: list[PositiveInt] = []


class RBACUpdate(RBACBase):
    allowed_endpoint_groups: list[PositiveInt] = []


# Schema for Responses (Returns the ID from the database)
class RBACResponse(RBACBase):
    id: int

    allowed_endpoint_group_ids: Annotated[
        list[PositiveInt],
        Field(serialization_alias="allowed_endpoint_groups", default_factory=list),
    ]
