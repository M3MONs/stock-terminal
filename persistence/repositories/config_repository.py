import sqlite3
from typing import Callable


class ConfigRepository:
    def __init__(self, connection_factory: Callable[[], sqlite3.Connection]) -> None:
        self.connection_factory = connection_factory

    _SELECT_QUERY = "SELECT key, value FROM app_config"
    _UPSERT_QUERY = "INSERT INTO app_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"

    def get_all(self) -> dict[str, str]:
        with self.connection_factory() as conn:
            rows = conn.execute(self._SELECT_QUERY).fetchall()
        return {r["key"]: r["value"] for r in rows}

    def save_all(self, items: dict[str, str]) -> None:
        with self.connection_factory() as conn:
            conn.executemany(self._UPSERT_QUERY, list(items.items()))
