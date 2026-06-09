from config.logging import setup_logging
from db import init_db
from ui.dashboard import Dashboard


def main() -> None:
    setup_logging()
    init_db()
    Dashboard().run()


if __name__ == "__main__":
    main()
