import sqlite3
from datetime import date, datetime, timezone
from typing import Callable

from models.user_agent_recommendation import Outcome, UserAgentRecommendation


class UserAgentRecommendationRepository:
    def __init__(self, connection_factory: Callable[[], sqlite3.Connection]) -> None:
        self.connection_factory = connection_factory

    _INSERT = """
        INSERT INTO user_agent_recommendations
            (created_at, agent, symbol, option, stop_loss, stop_profit, target_date, outcome)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id, created_at, agent, symbol, option, stop_loss, stop_profit, target_date, outcome
    """
    _SELECT_ALL = """
        SELECT id, created_at, agent, symbol, option, stop_loss, stop_profit, target_date, outcome
        FROM user_agent_recommendations
        ORDER BY created_at DESC
    """
    _SELECT_BY_SYMBOL = _SELECT_ALL.replace(
        "ORDER BY", "WHERE symbol = ? ORDER BY"
    )
    _SELECT_BY_AGENT = _SELECT_ALL.replace(
        "ORDER BY", "WHERE agent = ? ORDER BY"
    )
    _SELECT_LATEST_BY_SYMBOL = """
        SELECT id, created_at, agent, symbol, option, stop_loss, stop_profit, target_date, outcome
        FROM user_agent_recommendations
        WHERE symbol = ? ORDER BY created_at DESC LIMIT 1
    """
    _SET_OUTCOME = "UPDATE user_agent_recommendations SET outcome = ? WHERE id = ?"

    def _row_to_model(self, row: sqlite3.Row) -> UserAgentRecommendation:
        return UserAgentRecommendation(
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            agent=row["agent"],
            symbol=row["symbol"],
            option=row["option"],
            stop_loss=row["stop_loss"],
            stop_profit=row["stop_profit"],
            target_date=date.fromisoformat(row["target_date"]) if row["target_date"] else None,
            outcome=Outcome(row["outcome"]) if row["outcome"] else None,
        )

    def add(
        self,
        agent: str,
        symbol: str,
        option: str,
        stop_loss: float | None = None,
        stop_profit: float | None = None,
        target_date: date | None = None,
        outcome: Outcome | None = None,
    ) -> UserAgentRecommendation:
        now = datetime.now(timezone.utc)
        target_str = target_date.isoformat() if target_date else None
        outcome_str = outcome.value if outcome else None
        with self.connection_factory() as conn:
            cur = conn.execute(self._INSERT, (now, agent, symbol, option, stop_loss, stop_profit, target_str, outcome_str))
            row = cur.fetchone()
        return self._row_to_model(row)

    def list_all(self) -> list[UserAgentRecommendation]:
        with self.connection_factory() as conn:
            rows = conn.execute(self._SELECT_ALL).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_latest_by_symbol(self, symbol: str) -> UserAgentRecommendation | None:
        with self.connection_factory() as conn:
            row = conn.execute(self._SELECT_LATEST_BY_SYMBOL, (symbol,)).fetchone()
        return self._row_to_model(row) if row else None

    def list_by_symbol(self, symbol: str) -> list[UserAgentRecommendation]:
        with self.connection_factory() as conn:
            rows = conn.execute(self._SELECT_BY_SYMBOL, (symbol,)).fetchall()
        return [self._row_to_model(r) for r in rows]

    def list_by_agent(self, agent: str) -> list[UserAgentRecommendation]:
        with self.connection_factory() as conn:
            rows = conn.execute(self._SELECT_BY_AGENT, (agent,)).fetchall()
        return [self._row_to_model(r) for r in rows]

    def set_outcome(self, rec_id: int, outcome: Outcome) -> None:
        with self.connection_factory() as conn:
            conn.execute(self._SET_OUTCOME, (outcome.value, rec_id))
