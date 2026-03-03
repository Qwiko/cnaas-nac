from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.endpoint import EndpointGroup


class EndpointGroupFilter(Filter):
    id: Optional[int] = None
    id__in: Optional[list[int]] = None
    id__neq: Optional[str] = None

    name: Optional[str] = None
    name__in: Optional[list[str]] = None
    name__ilike: Optional[str] = None
    name__like: Optional[str] = None
    name__neq: Optional[str] = None

    order_by: list[str] = ["name"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = EndpointGroup
        search_model_fields = ["name"]
        search_field_name = "q"
