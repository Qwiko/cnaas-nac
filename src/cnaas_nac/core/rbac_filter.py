from typing import Sequence, Type, TypeVar

from sqlalchemy import Select, or_

from cnaas_nac.models.base import Base
from cnaas_nac.models.endpoint import Endpoint, EndpointGroup, EndpointState
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth

T = TypeVar("T", bound=Base)


def apply_group_filter(
    stmt: Select[tuple[T]],
    model: Type[T],
    group_ids: Sequence[int],
) -> Select[tuple[T]]:
    if not group_ids:
        return stmt

    if model == Endpoint:
        stmt = stmt.where(
            or_(model.group_id.in_(group_ids), model.state == EndpointState.DISCOVERED)  # type: ignore[attr-defined]
        )
    if model == EndpointGroup:
        stmt = stmt.where(
            model.id.in_(group_ids)  # type: ignore[attr-defined]
        )
    elif model == RadAcct or model == RadPostAuth or model == NasPort:
        stmt = stmt.where(
            or_(
                model.endpoint_group_id.in_(group_ids),  # type: ignore[attr-defined]
                model.endpoint_state  # type: ignore[attr-defined]
                == EndpointState.DISCOVERED,  # type: ignore[attr-defined]
            )
        )
    return stmt
