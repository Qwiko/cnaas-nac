from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from datetime import datetime, timedelta
from cnaas_nac.core.logging import get_logger
from sqlalchemy import select, delete, func, and_
from cnaas_nac.models.radcheck import RadCheck
from cnaas_nac.models.radpostauth import RadPostAuth
from cnaas_nac.core.db import async_session_factory

logger = get_logger()


scheduler = AsyncIOScheduler()


def setup_scheduled_tasks() -> AsyncIOScheduler:
    logger.info("Setting up tasks")

    scheduler.add_job(prune_postauth, "interval", days=1)
    scheduler.add_job(prune_inactive_radcheck, "interval", days=1)

    return scheduler


async def prune_postauth():
    async with async_session_factory() as db:
        logger.info("Starting task: prune_postauth")
        threshold_date = datetime.now() - timedelta(days=30)

        # Row Number 1 is the most recent login
        ranking_subq = (
            select(
                RadPostAuth.id,
                RadPostAuth.authdate,
                func.row_number()
                .over(
                    partition_by=RadPostAuth.username,
                    order_by=RadPostAuth.authdate.desc(),
                )
                .label("row_num"),
            )
        ).cte("ranking_subq")

        # Delete if: (The log is older than 30 days) AND (It is NOT among the top 10)
        delete_stmt = delete(RadPostAuth).where(
            and_(
                RadPostAuth.authdate < threshold_date,
                RadPostAuth.id.in_(
                    select(ranking_subq.c.id).where(ranking_subq.c.row_num > 10)
                ),
            )
        )

        result = await db.execute(delete_stmt)
        await db.commit()
        logger.info(f"Completed task: prune_postauth. Removed {result.rowcount} lines.")


async def prune_inactive_radcheck():
    async with async_session_factory() as db:
        logger.info("Starting task: prune_inactive_radcheck")

        cutoff = datetime.now() - timedelta(days=30)

        last_activity_subq = (
            select(
                RadPostAuth.username, func.max(RadPostAuth.authdate).label("last_seen")
            )
            .group_by(RadPostAuth.username)
            .subquery()
        )

        stmt = (
            select(RadCheck.username)
            .outerjoin(
                last_activity_subq, RadCheck.username == last_activity_subq.c.username
            )
            .where(last_activity_subq.c.last_seen < cutoff, not RadCheck.enabled)
        )

        # Execute and get the list of usernames
        results = (await db.execute(stmt)).scalars().all()

        for user in results:
            logger.info(
                f"Deleting user: {user}, inactive and have not been seen for 30 days."
            )
            await db.delete(user)

        # Get all users without a radpostauth
        log_exists_stmt = (
            select(1).where(RadPostAuth.username == RadCheck.username).exists()
        )

        stmt = select(RadCheck.username).where(~log_exists_stmt, not RadCheck.enabled)

        # Execute and return list of usernames
        users_with_logs = (await db.execute(stmt)).scalars().all()

        for user in users_with_logs:
            logger.info(
                f"User: {user} does not have any radpostauths associated with it, creating one."
            )
            db.add(RadPostAuth(username=user))

        await db.commit()

        logger.info("Completed task: prune_inactive_radcheck.")
