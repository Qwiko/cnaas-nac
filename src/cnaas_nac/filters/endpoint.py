from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.endpoint import Endpoint


class EndpointFilter(Filter):
    id: Optional[int] = None
    id__in: Optional[list[int]] = None
    id__neq: Optional[str] = None

    group_id: Optional[int] = None
    group_id__in: Optional[list[int]] = None
    group_id__neq: Optional[str] = None

    username: Optional[str] = None
    username__in: Optional[list[str]] = None
    username__ilike: Optional[str] = None
    username__like: Optional[str] = None
    username__neq: Optional[str] = None

    calling_station_id: Optional[str] = None
    calling_station_id__in: Optional[list[str]] = None
    calling_station_id__ilike: Optional[str] = None
    calling_station_id__like: Optional[str] = None
    calling_station_id__neq: Optional[str] = None

    state: Optional[str] = None
    state__in: Optional[list[str]] = None
    state__ilike: Optional[str] = None
    state__like: Optional[str] = None
    state__neq: Optional[str] = None

    order_by: list[str] = ["username"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = Endpoint
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"
