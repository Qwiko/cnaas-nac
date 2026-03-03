from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth


class AccountingLogFilter(Filter):
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

    order_by: list[str] = ["acct_start_time"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = RadAcct
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"


class RadPostLogFilter(Filter):
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

    order_by: list[str] = ["auth_date"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = RadPostAuth
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"
