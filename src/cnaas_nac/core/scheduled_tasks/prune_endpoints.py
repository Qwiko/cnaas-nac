from datetime import datetime, timedelta

from sqlalchemy import and_, func, select

from cnaas_nac.core.db import async_session_factory
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.radpostauth import RadPostAuth

logger = get_logger()

mac_regex = r"^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$"


async def prune_endpoints(filter, cutoff_days: int):
    async with async_session_factory() as db:
        logger.info(f"Starting task: prune_endpoints for state: {filter}")

        cutoff = datetime.now() - timedelta(days=cutoff_days)

        # Subquery to get the latest RadPostAuth per endpoint
        last_activity_subq = (
            select(
                RadPostAuth.username,
                RadPostAuth.calling_station_id,
                func.max(RadPostAuth.auth_date).label("last_seen"),
            )
            .group_by(
                RadPostAuth.username,
                RadPostAuth.calling_station_id,
            )
            .subquery()
        )

        # Select endpoints in endpoint_state with last activity older than cutoff
        stmt = (
            select(Endpoint)
            .join(
                last_activity_subq,
                and_(
                    Endpoint.username == last_activity_subq.c.username,
                    Endpoint.calling_station_id
                    == last_activity_subq.c.calling_station_id,
                ),
            )
            .where(
                # Endpoint has not been seen since cutoff and is in the specified state
                # Endpoint updated_at must also be older than cutoff to avoid deleting recently updated endpoints without recent RadPostAuth entries
                last_activity_subq.c.last_seen < cutoff,
                Endpoint.updated_at < cutoff,
                filter,
            )
        )

        endpoints = (await db.execute(stmt)).scalars().all()

        for endpoint in endpoints:
            logger.info(
                f"Deleting endpoint id={endpoint.id}, {endpoint.username}({endpoint.calling_station_id}), have not been seen for {cutoff_days} days."
            )
            await db.delete(endpoint)

        await db.commit()
        logger.info(
            f"Completed task: prune_endpoints for {filter}, deleted: {len(endpoints)} endpoints"
        )


async def prune_mab_discovered_endpoints() -> None:
    await prune_endpoints(
        and_(
            Endpoint.state == EndpointState.DISCOVERED,
            Endpoint.username.op("~")(mac_regex),
        ),
        settings.ENDPOINT_MAB_DISCOVERED_RETENTION_DAYS,
    )


async def prune_mab_pending_endpoints() -> None:
    await prune_endpoints(
        and_(
            Endpoint.state == EndpointState.PENDING,
            Endpoint.username.op("~")(mac_regex),
        ),
        settings.ENDPOINT_MAB_PENDING_RETENTION_DAYS,
    )


async def prune_mab_rejected_endpoints() -> None:
    await prune_endpoints(
        and_(
            Endpoint.state == EndpointState.REJECTED,
            Endpoint.username.op("~")(mac_regex),
        ),
        settings.ENDPOINT_MAB_REJECTED_RETENTION_DAYS,
    )


async def prune_mab_authorized_endpoints() -> None:
    await prune_endpoints(
        and_(
            Endpoint.state == EndpointState.AUTHORIZED,
            Endpoint.username.op("~")(mac_regex),
        ),
        settings.ENDPOINT_MAB_AUTHORIZED_RETENTION_DAYS,
    )


async def prune_eap_rejected_endpoints() -> None:
    await prune_endpoints(
        and_(
            Endpoint.state == EndpointState.REJECTED,
            Endpoint.username.op("!~")(mac_regex),
        ),
        settings.ENDPOINT_EAP_REJECTED_RETENTION_DAYS,
    )


async def prune_eap_authorized_endpoints() -> None:
    await prune_endpoints(
        and_(
            Endpoint.state == EndpointState.AUTHORIZED,
            Endpoint.username.op("!~")(mac_regex),
        ),
        settings.ENDPOINT_EAP_AUTHORIZED_RETENTION_DAYS,
    )
