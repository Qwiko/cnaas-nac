from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.api_internal.exceptions import Unauthorized
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.rule_engine import evaluate_rule
from cnaas_nac.core.settings import settings
from cnaas_nac.models.assignment_rule import AssignmentRule
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.user import User
from cnaas_nac.api_internal.schemas import InternalAuth

logger = get_logger()


async def accept(db: AsyncSession, auth: InternalAuth, vlan: int) -> dict:
    """Helper function to return a Access-Accept"""

    reply = {
        "Tunnel-Private-Group-Id": {"op": ":=", "value": str(vlan)},
        "Tunnel-Type": {"op": ":=", "value": "VLAN"},
        "Tunnel-Medium-Type": {"op": ":=", "value": "IEEE-802"},
    }

    return reply


async def reject(db: AsyncSession, auth: InternalAuth, reason: str) -> None:
    """
    Reject the user with a 401.

    From FreeRADIUS documentation:

    #  Authorize/Authenticate
    #
    #  Code   Meaning       Process body  Module code
    #  404    not found     no            notfound
    #  410    gone          no            notfound
    #  403    forbidden     no            userlock
    #  401    unauthorized  yes           reject
    #  204    no content    no            ok
    #  2xx    successful    yes           ok/updated
    #  5xx    server error  no            fail
    #  xxx    -             no            invalid
    #
    #  The status code is held in %{reply:REST-HTTP-Status-Code}.
    """

    raise Unauthorized(reason)


async def create_new_user(db: AsyncSession, auth: InternalAuth) -> User:
    vlan = None
    enabled = False

    # Handle reassignment rules.
    stmt = (
        select(AssignmentRule)
        .where(
            AssignmentRule.is_active,
        )
        .order_by(AssignmentRule.priority.asc())
        .options(selectinload(AssignmentRule.conditions))
        .execution_options(stream_results=True)
    )

    results = await db.stream_scalars(stmt)
    async for rule in results:
        if evaluate_rule(rule, dict(auth)):
            # Match found, set new vlan if needed.
            vlan = rule.target_vlan
            enabled = True
            logger.debug(f"User: {auth.username} is assigned to vlan: {vlan}")
            break
    else:
        # Default to DEFAULT_VLAN
        vlan = settings.RADIUS.DEFAULT_VLAN

    try:
        user = User(
            username=auth.username,
            enabled=enabled,
            vlan=vlan,
        )
        nas_port = NasPort(
            username=auth.username,
            nas_ip_address=auth.nas_ip_address,
            nas_identifier=auth.nas_identifier,
            nas_port_id=auth.nas_port_id,
            calling_station_id=auth.calling_station_id,
            called_station_id=auth.called_station_id,
        )

        db.add(user)
        db.add(nas_port)
        await db.commit()

        return user
    except Exception as e:
        error_msg = str(e)
        logger.error(error_msg)
        raise Unauthorized(error_msg)
