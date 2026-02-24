from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.nas import NasPort


class NasPortFilter(Filter):
    username: Optional[str] = None
    username__in: Optional[list[str]] = None
    username__ilike: Optional[str] = None
    username__like: Optional[str] = None
    username__neq: Optional[str] = None

    order_by: list[str] = ["username"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = NasPort
        search_model_fields = ["username"]
        search_field_name = "q"
