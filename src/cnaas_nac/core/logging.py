import logging


def get_logger() -> logging.Logger:
    logger = logging.getLogger("cnaas-nac")

    if not logger.handlers:
        formatter = logging.Formatter("%(levelname)s in %(module)s: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)
    return logger
