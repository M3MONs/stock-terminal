from decimal import Decimal

from pydantic import BaseModel


class StockMeta(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    currency: str = "USD"
    price: Decimal | None = None
    change_pct: float | None = None
