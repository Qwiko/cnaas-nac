from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.endpoint import Endpoint
from cnaas_nac.schemas.generic import MacAddress, Username


class EndpointFilter(Filter):
    id: Optional[int] = None
    id__in: Optional[list[int]] = None
    id__neq: Optional[str] = None

    group_id: Optional[int] = None
    group_id__in: Optional[list[int]] = None
    group_id__neq: Optional[str] = None

    username: Optional[Username] = None
    username__in: Optional[list[Username]] = None
    username__ilike: Optional[str] = None
    username__like: Optional[str] = None
    username__neq: Optional[Username] = None

    calling_station_id: Optional[MacAddress] = None
    calling_station_id__in: Optional[list[MacAddress]] = None
    calling_station_id__ilike: Optional[str] = None
    calling_station_id__like: Optional[str] = None
    calling_station_id__neq: Optional[MacAddress] = None

    state: Optional[str] = None
    state__in: Optional[list[str]] = None
    state__ilike: Optional[str] = None
    state__like: Optional[str] = None
    state__neq: Optional[str] = None

    nas_identifier: Optional[str] = None
    nas_identifier__in: Optional[list[str]] = None
    nas_identifier__ilike: Optional[str] = None
    nas_identifier__like: Optional[str] = None
    nas_identifier__neq: Optional[str] = None

    nas_port_id: Optional[str] = None
    nas_port_id__in: Optional[list[str]] = None
    nas_port_id__ilike: Optional[str] = None
    nas_port_id__like: Optional[str] = None
    nas_port_id__neq: Optional[str] = None

    order_by: list[str] = ["username"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = Endpoint
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"
