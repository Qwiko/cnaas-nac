from datetime import datetime, timedelta

from sqlalchemy import delete

from cnaas_nac.core.db import async_session_factory
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings

from cnaas_nac.models.radpostauth import RadPostAuth

logger = get_logger()


async def prune_postauth():
    async with async_session_factory() as db:
        logger.info("Starting task: prune_postauth")
        threshold_date = datetime.now() - timedelta(
            days=settings.RADPOSTAUTH_RETENTION_DAYS
        )

        delete_stmt = delete(RadPostAuth).where(RadPostAuth.auth_date < threshold_date)

        result = await db.execute(delete_stmt)

        await db.commit()
        logger.info(f"Completed task: prune_postauth. Removed {result.rowcount} lines.")
