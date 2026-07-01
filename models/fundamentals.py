from __future__ import annotations

from pydantic import BaseModel


class StockFundamentals(BaseModel):
    market_cap: int | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    profit_margins: float | None = None
    revenue_growth: float | None = None
    debt_to_equity: float | None = None
    return_on_equity: float | None = None
    dividend_yield: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    beta: float | None = None
