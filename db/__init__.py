import sqlite3
from pathlib import Path

from yoyo import get_backend, read_migrations

_DB_NAME = "stock.db"
_DB_DIR_NAME = ".stock-terminal"
_DB_MIGRATION_DIR_NAME = "migrations"
_DB_PATH = Path.home() / _DB_DIR_NAME / _DB_NAME
_MIGRATIONS_PATH = Path(__file__).parent.parent / _DB_MIGRATION_DIR_NAME


def get_connection() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    backend = get_backend(f"sqlite:///{_DB_PATH}")
    migrations = read_migrations(str(_MIGRATIONS_PATH))
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
