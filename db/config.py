from db import get_connection
from models.app_config import AppConfig


def load_config() -> AppConfig:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM app_config").fetchall()
    data = {r["key"]: r["value"] for r in rows}
    return AppConfig.model_validate(data) if data else AppConfig()


def save_config(config: AppConfig) -> None:
    items = config.model_dump()
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO app_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            [(k, str(v)) for k, v in items.items()],
        )
