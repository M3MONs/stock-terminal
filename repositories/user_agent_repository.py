import sqlite3
from typing import Callable

from models.user_agent import UserAgent


class UserAgentRepository:
    def __init__(self, connection_factory: Callable[[], sqlite3.Connection]) -> None:
        self.connection_factory = connection_factory

    _SELECT_ALL_QUERY = "SELECT id, name, file_path, enabled FROM user_agents ORDER BY id"
    _ADD_QUERY = "INSERT INTO user_agents (name, file_path) VALUES (?, ?) RETURNING id, name, file_path, enabled"
    _DELETE_QUERY = "DELETE FROM user_agents WHERE id = ?"
    _SET_ENABLED_QUERY = "UPDATE user_agents SET enabled = ? WHERE id = ?"

    def get_all(self) -> list[UserAgent]:
        with self.connection_factory() as conn:
            rows = conn.execute(self._SELECT_ALL_QUERY).fetchall()
        return [UserAgent.model_validate(dict(r)) for r in rows]

    def add(self, name: str, file_path: str) -> UserAgent:
        with self.connection_factory() as conn:
            cur = conn.execute(self._ADD_QUERY, (name, file_path))
            row = cur.fetchone()
        return UserAgent.model_validate(dict(row))

    def remove(self, agent_id: int) -> None:
        with self.connection_factory() as conn:
            conn.execute(self._DELETE_QUERY, (agent_id,))

    def set_enabled(self, agent_id: int, enabled: bool) -> None:
        with self.connection_factory() as conn:
            conn.execute(self._SET_ENABLED_QUERY, (int(enabled), agent_id))
