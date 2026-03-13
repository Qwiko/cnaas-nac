from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import IPvAnyNetwork
from cnaas_nac.models.nas import Nas


class NasFilter(Filter):
    id: Optional[int] = None
    id__in: Optional[list[int]] = None
    id__neq: Optional[str] = None

    name: Optional[str] = None
    name__in: Optional[list[str]] = None
    name__ilike: Optional[str] = None
    name__like: Optional[str] = None
    name__neq: Optional[str] = None

    network: Optional[IPvAnyNetwork] = None
    network__in: Optional[list[IPvAnyNetwork]] = None
    network__ilike: Optional[str] = None
    network__like: Optional[str] = None
    network__neq: Optional[IPvAnyNetwork] = None

    order_by: list[str] = ["name"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = Nas
        search_model_fields = ["name", "network"]
        search_field_name = "q"
