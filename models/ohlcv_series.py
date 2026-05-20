from pydantic import BaseModel
from .timeframe import Timeframe
from .candle import Candle
from .stock_meta import StockMeta

class OHLCVSeries(BaseModel):
    symbol: str
    timeframe: Timeframe
    candles: list[Candle]
    meta: StockMeta | None = None
