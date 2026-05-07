import logging

from cnaas_nac.core.settings import settings


def get_logger() -> logging.Logger:
    logger = logging.getLogger("cnaas-nac")

    logger.setLevel(settings.LOGGING)
    return logger
