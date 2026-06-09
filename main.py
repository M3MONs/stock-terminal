import logging
from logging.handlers import RotatingFileHandler

from db import LOG_PATH, init_db
from ui.dashboard import Dashboard

_handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(_handler)
for _noisy in ("httpx", "httpcore", "yfinance", "openai", "google"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


def main() -> None:
    init_db()
    Dashboard().run()


if __name__ == "__main__":
    main()
