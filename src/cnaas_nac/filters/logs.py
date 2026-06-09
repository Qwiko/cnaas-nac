from datetime import datetime
from ipaddress import ip_network
from typing import Annotated, Any, Optional, Union

from sqlalchemy.orm import Query
from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.contrib.sqlalchemy.filter import _orm_operator_transformer
from pydantic import BeforeValidator, IPvAnyNetwork
from sqlalchemy import Select, or_

from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth
from cnaas_nac.schemas.generic import MacAddress, Username


def validate_nas_ip_address(v: Any) -> None | IPvAnyNetwork:
    # Only returns when the address is fully defined.
    # Otherwise null
    try:
        return ip_network(v)
    except ValueError:
        return None


class LogFilter(Filter):
    def filter(self, query: Union[Query, Select]) -> Union[Query, Select]:
        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, Filter):
                query = field_value.filter(query)
            else:
                if "__" in field_name:
                    field_name, operator = field_name.split("__")
                    operator, value = _orm_operator_transformer[operator](value)  # type: ignore[no-untyped-call]
                else:
                    operator = "__eq__"

                if field_name == self.Constants.search_field_name and hasattr(
                    self.Constants, "search_model_fields"
                ):
                    search_filters = [
                        getattr(self.Constants.model, field).ilike(f"%{value}%")
                        for field in self.Constants.search_model_fields
                    ]
                    query = query.filter(or_(*search_filters))
                else:
                    model_field = getattr(self.Constants.model, field_name)
                    if "ip_address" in field_name and "__in" in field_name:
                        query = query.filter(getattr(model_field).op("<<=")(value))  # type: ignore[call-overload]
                    else:
                        query = query.filter(getattr(model_field, operator)(value))

        return query


class AccountingFilter(LogFilter):
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

    realm: Optional[str] = None
    realm__in: Optional[list[str]] = None
    realm__ilike: Optional[str] = None
    realm__like: Optional[str] = None
    realm__neq: Optional[str] = None

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

    nas_ip_address__in: Annotated[
        Optional[IPvAnyNetwork], BeforeValidator(validate_nas_ip_address)
    ] = None

    order_by: list[str] = ["acct_start_time"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = RadAcct
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"


class AuthenticationFilter(LogFilter):
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

    nas_ip_address__in: Annotated[
        Optional[IPvAnyNetwork], BeforeValidator(validate_nas_ip_address)
    ] = None

    order_by: list[str] = ["auth_date"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = RadPostAuth
        search_model_fields = ["username", "calling_station_id"]
        search_field_name = "q"
