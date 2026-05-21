import sqlite3
from typing import Callable
from models.app_config import AppConfig


class Config:
    def __init__(self, connection_factory: Callable[[], sqlite3.Connection]) -> None:
        self.connection_factory = connection_factory

    _SELECT_QUERY = "SELECT key, value FROM app_config"
    _INSERT_QUERY = "INSERT INTO app_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"

    def load(self) -> AppConfig:
        with self.connection_factory() as conn:
            rows = conn.execute(self._SELECT_QUERY).fetchall()
        data = {r["key"]: r["value"] for r in rows}
        return AppConfig.model_validate(data) if data else AppConfig()

    def save(self, config: AppConfig) -> None:
        items = config.model_dump()
        with self.connection_factory() as conn:
            conn.executemany(
                self._INSERT_QUERY,
                [(k, str(v)) for k, v in items.items()],
            )
