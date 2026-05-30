from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel


class Outcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"


class UserAgentRecommendation(BaseModel):
    id: int | None = None
    created_at: datetime
    agent: str
    symbol: str
    opcja: str
    stop_loss: float | None = None
    stop_profit: float | None = None
    target_date: date | None = None
    outcome: Outcome | None = None
