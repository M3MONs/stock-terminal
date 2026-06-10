from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from data.adapters.base import AdapterError, DataAdapter
from data.adapters.registry import register_adapter
from models.candle import Candle
from models.ohlcv_series import OHLCVSeries
from models.stock_meta import StockMeta
from models.timeframe import Timeframe


@register_adapter("twelvedata")
class TwelveDataAdapter(DataAdapter):
    def to_ohlcv_series(self, raw: dict[str, Any], symbol: str, timeframe: Timeframe) -> OHLCVSeries:
        candles = []
        for row in raw["rows"]:
            dt_raw = row.get("datetime")
            if dt_raw is None:
                raise AdapterError(f"Missing datetime in row: {row}")
            try:
                ts = datetime.fromisoformat(dt_raw)
            except (ValueError, TypeError) as e:
                raise AdapterError(f"Unparseable datetime '{dt_raw}': {e}") from e
            candles.append(
                Candle(
                    timestamp=ts,
                    open=Decimal(row["open"]),
                    high=Decimal(row["high"]),
                    low=Decimal(row["low"]),
                    close=Decimal(row["close"]),
                    volume=int(row["volume"]),
                )
            )
        return OHLCVSeries(symbol=symbol, timeframe=timeframe, candles=candles)

    def to_stock_meta(self, raw: dict[str, Any], symbol: str) -> StockMeta:
        close = raw.get("close")
        pct = raw.get("percent_change")
        return StockMeta(
            symbol=symbol,
            name=raw.get("name"),
            exchange=raw.get("exchange"),
            currency=raw.get("currency", "USD"),
            price=Decimal(str(close)) if close is not None else None,
            change_pct=float(pct) if pct is not None else None,
        )
