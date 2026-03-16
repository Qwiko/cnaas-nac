from datetime import datetime, timedelta

from sqlalchemy import delete

from cnaas_nac.core.db import async_session_factory
from cnaas_nac.core.logging import get_logger
from cnaas_nac.models.radacct import RadAcct

logger = get_logger()


async def prune_radacct():
    async with async_session_factory() as db:
        logger.info("Starting task: prune_acct")
        threshold_date = datetime.now() - timedelta(days=90)

        delete_stmt = delete(RadAcct).where(RadAcct.acct_stop_time < threshold_date)

        result = await db.execute(delete_stmt)

        await db.commit()

        no_endpoint_stmt = delete(RadAcct).where(RadAcct.endpoint_id.is_(None))

        no_endpoint_result = await db.execute(no_endpoint_stmt)

        await db.commit()

        logger.info(
            f"Completed task: prune_acct. Removed {result.rowcount} radacct, {no_endpoint_result.rowcount} radacct with no associated endpoint."
        )
