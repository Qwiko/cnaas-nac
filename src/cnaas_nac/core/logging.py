import logging
from logging.config import dictConfig

from cnaas_nac.core.settings import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelname)s %(name)s - %(message)s",
            "use_colors": True,
        }
    },
    "handlers": {
        "console": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "fastapi": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "asyncio": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "starlette": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "cnaas-nac": {
            "handlers": ["console"],
            "level": settings.LOGGING,
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)


def get_logger() -> logging.Logger:
    logger = logging.getLogger("cnaas-nac")

    return logger
