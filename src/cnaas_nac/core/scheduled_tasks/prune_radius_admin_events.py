from datetime import datetime, timedelta

from sqlalchemy import delete

from cnaas_nac.core.db import async_session_factory
from cnaas_nac.core.logging import get_logger
from cnaas_nac.models.radiusadminevent import RadiusAdminEvent
from cnaas_nac.core.settings import settings

logger = get_logger()


async def prune_radius_admin_events() -> None:
    async with async_session_factory() as db:
        logger.info("Starting task: prune_radius_admin_events")
        threshold_date = datetime.now() - timedelta(
            days=settings.RADIUS_ADMIN_EVENTS_RETENTION_DAYS
        )

        delete_stmt = delete(RadiusAdminEvent).where(RadiusAdminEvent.created_at < threshold_date)

        result = await db.execute(delete_stmt)

        await db.commit()

        logger.info(
            f"Completed task: prune_radius_admin_events. Removed {result.rowcount} radius admin events."  # type: ignore[attr-defined]
        )
