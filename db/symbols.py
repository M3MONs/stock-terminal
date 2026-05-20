import json

from db import get_connection
from models.tagged_symbol import TaggedSymbol


def list_symbols() -> list[TaggedSymbol]:
    with get_connection() as conn:
        rows = conn.execute("SELECT symbol, tags FROM watched_symbols ORDER BY symbol").fetchall()
    return [TaggedSymbol(symbol=r["symbol"], tags=json.loads(r["tags"])) for r in rows]


def add_symbol(symbol: str, tags: list[str] | None = None) -> None:
    tags_json = json.dumps(tags or [])
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO watched_symbols (symbol, tags) VALUES (?, ?) ON CONFLICT(symbol) DO NOTHING",
            (symbol.upper(), tags_json),
        )


def remove_symbol(symbol: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM watched_symbols WHERE symbol = ?", (symbol.upper(),))


def update_tags(symbol: str, tags: list[str]) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE watched_symbols SET tags = ? WHERE symbol = ?",
            (json.dumps(tags), symbol.upper()),
        )
