import json
import sqlite3
from typing import Callable
from models.tagged_symbol import TaggedSymbol


class SymbolRepository:
    def __init__(self, connection_factory: Callable[[], sqlite3.Connection]) -> None:
        self.connection_factory = connection_factory

    _SELECT_ALL_QUERY = "SELECT symbol, tags FROM watched_symbols ORDER BY symbol"
    _ADD_QUERY = "INSERT INTO watched_symbols (symbol, tags) VALUES (?, ?) ON CONFLICT(symbol) DO NOTHING"
    _DELETE_QUERY = "DELETE FROM watched_symbols WHERE symbol = ?"
    _UPDATE_TAGS_QUERY = "UPDATE watched_symbols SET tags = ? WHERE symbol = ?"

    def get_all(self) -> list[TaggedSymbol]:
        with self.connection_factory() as conn:
            rows = conn.execute(self._SELECT_ALL_QUERY).fetchall()
        return [TaggedSymbol(symbol=r["symbol"], tags=json.loads(r["tags"])) for r in rows]

    def add(self, symbol: str, tags: list[str] | None = None) -> None:
        tags_json = json.dumps(tags or [])
        with self.connection_factory() as conn:
            conn.execute(
                self._ADD_QUERY,
                (symbol.upper(), tags_json),
            )

    def remove(self, symbol: str) -> None:
        with self.connection_factory() as conn:
            conn.execute(self._DELETE_QUERY, (symbol.upper(),))

    def update_tags(self, symbol: str, tags: list[str]) -> None:
        with self.connection_factory() as conn:
            conn.execute(
                self._UPDATE_TAGS_QUERY,
                (json.dumps(tags), symbol.upper()),
            )
