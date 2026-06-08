from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class TradingOption(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Outcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"


class UserAgentRecommendation(BaseModel):
    id: int | None = None
    created_at: datetime
    agent: str
    symbol: str
    option: TradingOption
    stop_loss: Decimal | None = None
    stop_profit: Decimal | None = None
    target_date: date | None = None
    outcome: Outcome | None = None
