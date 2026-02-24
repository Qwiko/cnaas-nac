from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from cnaas_nac.models.assignment_rule import AssignmentRule


class AssignmentRuleFilter(Filter):
    name: Optional[str] = None
    name__in: Optional[list[str]] = None
    name__ilike: Optional[str] = None
    name__like: Optional[str] = None
    name__neq: Optional[str] = None

    order_by: list[str] = ["name"]

    q: Optional[str] = None

    class Constants(Filter.Constants):
        model = AssignmentRule
        search_model_fields = ["name"]
        search_field_name = "q"
