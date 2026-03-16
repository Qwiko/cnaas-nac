from datetime import datetime, timedelta

from sqlalchemy import and_, func, select

from cnaas_nac.core.db import async_session_factory
from cnaas_nac.core.logging import get_logger

from cnaas_nac.models.endpoint import Endpoint, EndpointState
from cnaas_nac.models.radpostauth import RadPostAuth

logger = get_logger()


async def prune_endpoints(endpoint_state: EndpointState, cutoff_days: int):
    async with async_session_factory() as db:
        logger.info(f"Starting task: prune_endpoints for state: {endpoint_state}")

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
                last_activity_subq.c.last_seen < cutoff,
                Endpoint.state == endpoint_state,
            )
        )

        endpoints = (await db.execute(stmt)).scalars().all()

        for endpoint in endpoints:
            logger.info(
                f"Deleting endpoint id={endpoint.id}, {endpoint.username}({endpoint.calling_station_id}), have not been seen for { cutoff_days } days."
            )
            await db.delete(endpoint)

        await db.commit()
        logger.info(f"Completed task: prune_endpoints for state: {endpoint_state}, deleted: {len(endpoints)} endpoints")


async def prune_discovered_endpoints():
    await prune_endpoints(EndpointState.DISCOVERED, 30)


async def prune_rejected_endpoints():
    await prune_endpoints(EndpointState.REJECTED, 30)


async def prune_pending_endpoints():
    await prune_endpoints(EndpointState.PENDING, 30)


async def prune_authorized_endpoints():
    await prune_endpoints(EndpointState.AUTHORIZED, 30)
