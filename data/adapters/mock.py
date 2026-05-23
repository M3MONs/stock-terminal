from datetime import datetime
from decimal import Decimal
from typing import Any

from data.adapters.base import DataAdapter
from data.adapters.registry import register_adapter
from models.candle import Candle
from models.ohlcv_series import OHLCVSeries
from models.stock_meta import StockMeta
from models.timeframe import Timeframe


@register_adapter("mock")
class MockAdapter(DataAdapter):
    def to_ohlcv_series(self, raw: dict[str, Any], symbol: str, timeframe: Timeframe) -> OHLCVSeries:
        candles = [
            Candle(
                timestamp=datetime.fromisoformat(c["timestamp"]),
                open=Decimal(c["open"]),
                high=Decimal(c["high"]),
                low=Decimal(c["low"]),
                close=Decimal(c["close"]),
                volume=int(c["volume"]),
            )
            for c in raw["candles"]
        ]
        return OHLCVSeries(symbol=symbol, timeframe=timeframe, candles=candles)

    def to_stock_meta(self, raw: dict[str, Any], symbol: str) -> StockMeta:
        return StockMeta(
            symbol=symbol,
            name=raw.get("name"),
            exchange=raw.get("exchange"),
            currency=raw.get("currency", "USD"),
        )
