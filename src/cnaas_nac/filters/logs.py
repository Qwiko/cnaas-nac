from datetime import datetime
from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth


class AccountingFilter(Filter):
    id: Optional[int] = None
    id__in: Optional[list[int]] = None
    id__neq: Optional[str] = None

    endpoint_id: Optional[int] = None
    endpoint_id__in: Optional[list[int]] = None
    endpoint_id__neq: Optional[str] = None

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

    acct_start_time: Optional[datetime] = None
    acct_start_time__isnull: Optional[bool] = None
    acct_start_time__gt: Optional[datetime] = None
    acct_start_time__gte: Optional[datetime] = None
    acct_start_time__lt: Optional[datetime] = None
    acct_start_time__lte: Optional[datetime] = None

    acct_update_time: Optional[datetime] = None
    acct_update_time__isnull: Optional[bool] = None
    acct_update_time__gt: Optional[datetime] = None
    acct_update_time__gte: Optional[datetime] = None
    acct_update_time__lt: Optional[datetime] = None
    acct_update_time__lte: Optional[datetime] = None

    acct_stop_time: Optional[datetime] = None
    acct_stop_time__isnull: Optional[bool] = None
    acct_stop_time__gt: Optional[datetime] = None
    acct_stop_time__gte: Optional[datetime] = None
    acct_stop_time__lt: Optional[datetime] = None
    acct_stop_time__lte: Optional[datetime] = None

    order_by: list[str] = ["acct_start_time"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = RadAcct
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"


class AuthenticationFilter(Filter):
    id: Optional[int] = None
    id__in: Optional[list[int]] = None
    id__neq: Optional[str] = None

    endpoint_id: Optional[int] = None
    endpoint_id__in: Optional[list[int]] = None
    endpoint_id__neq: Optional[str] = None

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

    matched_policy_id: Optional[int] = None
    matched_policy_id__in: Optional[list[int]] = None
    matched_policy_id__ilike: Optional[int] = None
    matched_policy_id__like: Optional[int] = None
    matched_policy_id__neq: Optional[int] = None

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

    reply: Optional[str] = None
    reply__in: Optional[list[str]] = None
    reply__ilike: Optional[str] = None
    reply__like: Optional[str] = None
    reply__neq: Optional[str] = None

    auth_date: Optional[datetime] = None
    auth_date__gt: Optional[datetime] = None
    auth_date__gte: Optional[datetime] = None
    auth_date__lt: Optional[datetime] = None
    auth_date__lte: Optional[datetime] = None

    order_by: list[str] = ["auth_date"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = RadPostAuth
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"
