from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,
)

from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.scheduled_tasks.prune_endpoints import (
    prune_eap_authorized_endpoints,
    prune_eap_rejected_endpoints,
    prune_mab_authorized_endpoints,
    prune_mab_discovered_endpoints,
    prune_mab_pending_endpoints,
    prune_mab_rejected_endpoints,
)
from cnaas_nac.core.scheduled_tasks.prune_postauth import prune_postauth
from cnaas_nac.core.scheduled_tasks.prune_radacct import prune_radacct
from cnaas_nac.core.scheduled_tasks.prune_radius_admin_events import (
    prune_radius_admin_events,
)

logger = get_logger()


scheduler = AsyncIOScheduler()


def setup_scheduled_tasks() -> AsyncIOScheduler:
    logger.info("Setting up scheduled tasks")

    scheduler.add_job(prune_eap_authorized_endpoints, "cron", hour=1, minute=0)
    scheduler.add_job(prune_eap_rejected_endpoints, "cron", hour=1, minute=0)

    scheduler.add_job(prune_mab_authorized_endpoints, "cron", hour=1, minute=0)
    scheduler.add_job(prune_mab_discovered_endpoints, "cron", hour=1, minute=0)
    scheduler.add_job(prune_mab_pending_endpoints, "cron", hour=1, minute=0)
    scheduler.add_job(prune_mab_rejected_endpoints, "cron", hour=1, minute=0)

    scheduler.add_job(prune_postauth, "cron", hour=2, minute=0)
    scheduler.add_job(prune_radacct, "cron", hour=2, minute=0)

    scheduler.add_job(prune_radius_admin_events, "cron", hour=2, minute=30)

    return scheduler
