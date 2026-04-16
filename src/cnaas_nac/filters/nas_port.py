from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.schemas.generic import MacAddress, Username


class NasPortFilter(Filter):
    id: Optional[int] = None
    id__in: Optional[list[int]] = None
    id__neq: Optional[str] = None

    endpoint_id: Optional[int] = None
    endpoint_id__in: Optional[list[int]] = None
    endpoint_id__neq: Optional[str] = None

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

    order_by: list[str] = ["username"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = NasPort
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"
