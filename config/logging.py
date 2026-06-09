import logging
from logging.handlers import RotatingFileHandler

from config.paths import LOG_PATH

_NOISY_LIBS = ("httpx", "httpcore", "yfinance", "openai", "google")
_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 3


def setup_logging() -> None:
    handler = RotatingFileHandler(LOG_PATH, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8")
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
    for lib in _NOISY_LIBS:
        logging.getLogger(lib).setLevel(logging.WARNING)
