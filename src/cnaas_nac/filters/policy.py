from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.policy import (
    ClientType,
    MatchLogic,
    Policy,
    PortLocking,
    PortType,
)


class PolicyFilter(Filter):
    name: Optional[str] = None
    name__in: Optional[list[str]] = None
    name__ilike: Optional[str] = None
    name__like: Optional[str] = None
    name__neq: Optional[str] = None

    client_type: Optional[ClientType] = None
    client_type__in: Optional[list[ClientType]] = None
    client_type__ilike: Optional[str] = None
    client_type__like: Optional[str] = None
    client_type__neq: Optional[ClientType] = None

    match_logic: Optional[MatchLogic] = None
    match_logic__in: Optional[list[MatchLogic]] = None
    match_logic__ilike: Optional[str] = None
    match_logic__like: Optional[str] = None
    match_logic__neq: Optional[MatchLogic] = None

    port_locking: Optional[PortLocking] = None
    port_locking__in: Optional[list[PortLocking]] = None
    port_locking__ilike: Optional[str] = None
    port_locking__like: Optional[str] = None
    port_locking__neq: Optional[PortLocking] = None

    port_type: Optional[PortType] = None
    port_type__in: Optional[list[PortType]] = None
    port_type__ilike: Optional[str] = None
    port_type__like: Optional[str] = None
    port_type__neq: Optional[PortType] = None

    order_by: list[str] = ["name"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = Policy
        search_model_fields = ["name"]
        search_field_name = "q"
