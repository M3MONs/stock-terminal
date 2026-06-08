import logging

from db import init_db
from ui.dashboard import Dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)


def main() -> None:
    init_db()
    Dashboard().run()


if __name__ == "__main__":
    main()
