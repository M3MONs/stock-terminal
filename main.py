from infra.logging import setup_logging
from infra.paths import AGENTS_DIR, KNOWLEDGE_DIR
from persistence import init_db
from ui.dashboard import Dashboard


def main() -> None:
    setup_logging()
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    Dashboard().run()


if __name__ == "__main__":
    main()
