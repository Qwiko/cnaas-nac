from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]


from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.scheduled_tasks.prune_endpoints import (
    prune_discovered_endpoints,
    prune_authorized_endpoints,
    prune_pending_endpoints,
    prune_rejected_endpoints,
)
from cnaas_nac.core.scheduled_tasks.prune_radacct import prune_radacct
from cnaas_nac.core.scheduled_tasks.prune_postauth import prune_postauth

logger = get_logger()


scheduler = AsyncIOScheduler()


def setup_scheduled_tasks() -> AsyncIOScheduler:
    logger.info("Setting up scheduled tasks")

    scheduler.add_job(prune_discovered_endpoints, "interval", days=1)
    scheduler.add_job(prune_authorized_endpoints, "interval", days=1)
    scheduler.add_job(prune_pending_endpoints, "interval", days=1)
    scheduler.add_job(prune_rejected_endpoints, "interval", days=1)

    scheduler.add_job(prune_postauth, "interval", days=1)

    scheduler.add_job(prune_radacct, "interval", days=1)

    return scheduler
