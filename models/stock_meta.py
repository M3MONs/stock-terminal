from pydantic import BaseModel


class StockMeta(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    currency: str = "USD"
