from typing import Any

from netutils.mac import is_valid_mac
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.api_internal.exceptions import Unauthorized
from cnaas_nac.api_internal.schemas import InternalAuth
from cnaas_nac.core.logging import get_logger
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.policy import Policy

logger = get_logger()


async def accept(
    db: AsyncSession,
    auth: InternalAuth,
    endpoint: Endpoint | None,
    matched_policy: Policy,
) -> dict[str, Any]:
    """Helper function to return a Access-Accept"""

    await update_endpoint_state(db, auth, endpoint, EndpointState.AUTHORIZED)

    accept_reply: dict[str, list[str] | str] = {}

    for reply in matched_policy.replies:
        attribute = reply.attribute
        value = reply.value

        if attribute in accept_reply:
            if isinstance(accept_reply[attribute], list):
                accept_reply[attribute].append(value)  # type: ignore[union-attr]
            else:
                accept_reply[attribute] = [accept_reply.get(attribute), value]  # type: ignore[list-item]
        else:
            accept_reply[attribute] = value

    # Add NAC-Policy-Id attribute
    accept_reply["NAC-Policy-Id"] = str(matched_policy.id)
    print(accept_reply)
    return accept_reply


async def reject(
    db: AsyncSession,
    auth: InternalAuth,
    endpoint: Endpoint | None,
    error_message: str,
    matched_policy: Policy | None,
) -> None:
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

    await update_endpoint_state(db, auth, endpoint, EndpointState.REJECTED)

    logger.info(
        f"User: {auth.username}({auth.calling_station_id}) rejected, reason: {error_message}"
    )
    raise Unauthorized(error_message, matched_policy.id if matched_policy else None)


async def update_endpoint_state(
    db: AsyncSession,
    auth: InternalAuth,
    endpoint: Endpoint | None,
    endpoint_state: EndpointState,
) -> None:
    if not endpoint:
        endpoint = Endpoint(
            username=auth.username, calling_station_id=auth.calling_station_id
        )
        db.add(endpoint)

    # Only update state if not equals to DISCOVERED.
    if (
        endpoint.state == EndpointState.DISCOVERED
        and endpoint_state == EndpointState.REJECTED
    ):
        logger.debug(
            f"User: {auth.username}({auth.calling_station_id}) is discovered, state kept as discovered."
        )
    else:
        logger.debug(
            f"User: {auth.username}({auth.calling_station_id}) update state: {endpoint_state}"
        )
        endpoint.state = endpoint_state

    await db.commit()


async def create_new_endpoint(db: AsyncSession, auth: InternalAuth) -> Endpoint:
    try:
        endpoint = Endpoint(
            username=auth.username,
            calling_station_id=auth.calling_station_id,
            state=EndpointState.DISCOVERED
            if is_valid_mac(auth.username)
            else EndpointState.REJECTED,
        )
        nas_port = NasPort(
            username=auth.username,
            nas_ip_address=auth.nas_ip_address,
            nas_identifier=auth.nas_identifier,
            nas_port_id=auth.nas_port_id,
            calling_station_id=auth.calling_station_id,
            called_station_id=auth.called_station_id,
        )

        db.add(endpoint)
        db.add(nas_port)
        await db.commit()
        return endpoint
    except Exception as e:
        error_msg = str(e)
        logger.error(error_msg)
        raise Unauthorized(error_msg)
