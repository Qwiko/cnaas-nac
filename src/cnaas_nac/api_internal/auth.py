from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, inspect, not_, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.api_internal.schemas import InternalAuth
from cnaas_nac.api_internal.utils import accept, create_new_endpoint, reject
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.logging import get_logger
from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.endpoint import Endpoint
from cnaas_nac.models.policy import MatchLogic, Policy, PolicyCondition, PortLocking
from cnaas_nac.core.rule_engine import evaluate_policy

logger = get_logger()

router = APIRouter(prefix="/api/v2", tags=["auth"])


@router.post("/auth", response_model=dict[str, Any])
async def post_auth(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    auth: InternalAuth,
) -> Any:
    """
    Internal endpoint that is used from the Freeradius rest module
    """

    endpoint = (
        await db.execute(
            select(Endpoint)
            .where(
                Endpoint.username == auth.username,
                Endpoint.calling_station_id == auth.calling_station_id,
            )
            .options(selectinload(Endpoint.group))
        )
    ).scalar_one_or_none()

    # Get policy rules.
    stmt = (
        select(Policy)
        .where(
            Policy.enabled,
            or_(Policy.client_type == auth.client_type, Policy.client_type.is_(None)),
            or_(Policy.port_type == auth.nas_port_type, Policy.port_type.is_(None)),
        )
        .order_by(Policy.priority.asc())
        .options(selectinload(Policy.conditions))
        .execution_options(stream_results=True)
    )

    policy_count_subq = (
        select(func.count(PolicyCondition.id))
        .where(PolicyCondition.policy_id == Policy.id)
        .correlate(Policy)
        .scalar_subquery()
    )

    # Filter the db query on known attributes.
    # This removes the need to compute conditions for groups that will never match.
    if endpoint and endpoint.group:
        # If we have a group we can filter away policies with a single condition pointing at another group.
        # or multiple conditions but with matchlogic AND
        # We will never match that policy.
        stmt = stmt.where(
            not_(
                and_(
                    or_(policy_count_subq == 1, Policy.match_logic == MatchLogic.AND),
                    Policy.conditions.any(
                        PolicyCondition.group_id != endpoint.group_id
                    ),
                ),
            ),
        )
    else:
        # Likewise if we dont have a group we will never match a policy with a condition pointing to a group.
        stmt = stmt.where(
            # We will never match a policy with match_logic AND and a condition points to a group_id
            not_(
                and_(
                    or_(policy_count_subq == 1, Policy.match_logic == MatchLogic.AND),
                    Policy.conditions.any(PolicyCondition.group_id.is_not(None)),
                )
            ),
        )

    matched_policy: Policy | None = None
    results = await db.stream_scalars(stmt)
    async for policy in results:
        if evaluate_policy(policy, dict(auth), endpoint.group_id if endpoint else None):
            matched_policy = policy
            break
    else:
        logger.debug(f"No policy matched for user: {auth.username}")

        if not endpoint:
            logger.debug("Adding new endpoint")
            endpoint = await create_new_endpoint(db, auth)

        return await reject(db, auth, endpoint, "Did not match any policy.", None)

    # Dictionary with key:value needed to create a NasPort
    # from auth model.
    auth_nas_port_dict = {
        k: v for k, v in auth.model_dump().items() if hasattr(NasPort, k)
    }

    db_nas_port = (
        await db.execute(
            select(NasPort).where(
                NasPort.username == auth.username,
                NasPort.calling_station_id == auth.calling_station_id,
                or_(
                    and_(
                        NasPort.called_station_id == auth.called_station_id,
                        NasPort.nas_port_id == auth.nas_port_id,
                    ),
                    and_(
                        NasPort.nas_identifier == auth.nas_identifier,
                        NasPort.nas_port_id == auth.nas_port_id,
                    ),
                ),
            )
        )
    ).scalar_one_or_none()

    if db_nas_port:
        logger.debug(
            f"User: {auth.username}({auth.calling_station_id}), connected on a known previous port."
        )

        # Update nasport if some information have changed.
        # For example changed hostname but same called_station_id
        # Or replaced switch, same hostname but changed called_station_id.
        for k, v in auth_nas_port_dict.items():
            if getattr(db_nas_port, k) != v:
                setattr(db_nas_port, k, v)

        if inspect(db_nas_port).modified:
            logger.debug(
                f"Port: {db_nas_port.nas_identifier}:{db_nas_port.nas_port_id} have been modified with new data."
            )
        else:
            # Force updated_at update for this nasport.
            # Even if the data is the same.
            logger.debug(
                f"No new data for port: {db_nas_port.nas_identifier}:{db_nas_port.nas_port_id}, still updating updated_at to use as last_seen."
            )
            db_nas_port.updated_at = datetime.now(timezone.utc)

        await db.commit()

    if not db_nas_port and not matched_policy.port_locking:
        logger.info(
            f"User: {auth.username}({auth.calling_station_id}) connected on new port. Adding nasport"
        )
        db_nas_port = NasPort(**auth_nas_port_dict)
        db.add(db_nas_port)
        await db.commit()

    if matched_policy.port_locking:
        # Get expected port this endpoint should be connected to.
        expected_port = (
            (
                await db.execute(
                    select(NasPort)
                    .where(
                        NasPort.username == auth.username,
                    )
                    .order_by(NasPort.updated_at.desc())
                )
            )
            .scalars()
            .first()
        )
        if not expected_port:
            logger.info(
                f"User: {auth.username}({auth.calling_station_id}) does not have any expected port, creating one."
            )
            expected_port = NasPort(**auth_nas_port_dict)
            db.add(expected_port)
            await db.commit()

        # Switch does not match
        if (
            auth.nas_identifier != expected_port.nas_identifier
            or auth.called_station_id != expected_port.called_station_id
        ):
            return await reject(
                db,
                auth,
                endpoint,
                f"connected on: {auth.called_station_id}({auth.nas_identifier}):{auth.nas_port_id}, expected: {expected_port.nas_identifier}:{expected_port.nas_port_id}",
                matched_policy,
            )
        # For PortLocking.SWITCH_PORT port must also be the same
        if matched_policy.port_locking == PortLocking.SWITCH_PORT and (
            not db_nas_port or db_nas_port.id != expected_port.id
        ):
            return await reject(
                db,
                auth,
                endpoint,
                f"connected on: {auth.called_station_id}({auth.nas_identifier}):{auth.nas_port_id}, expected: {expected_port.nas_identifier}:{expected_port.nas_port_id}",
                matched_policy,
            )

    # Fetch replies from the db.
    await db.refresh(matched_policy, attribute_names=["replies"])
    logger.info(
        f"User: {auth.username}({auth.calling_station_id}) passed policy checks, accepted."
    )
    return await accept(db, auth, endpoint, matched_policy)
