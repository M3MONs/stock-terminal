from __future__ import annotations

from decimal import Decimal
from typing import Any

from data.adapters.base import DataAdapter, AdapterError
from data.adapters.registry import register_adapter
from models.candle import Candle
from models.ohlcv_series import OHLCVSeries
from models.stock_meta import StockMeta
from models.timeframe import Timeframe


@register_adapter("yahoo")
class YahooAdapter(DataAdapter):
    def to_ohlcv_series(self, raw: dict[str, Any], symbol: str, timeframe: Timeframe) -> OHLCVSeries:
        candles = []
        for row in raw["rows"]:
            ts_raw = row.get("Datetime") or row.get("Date")
            if ts_raw is None:
                raise AdapterError(f"Missing timestamp in row: {row}")
            try:
                ts = ts_raw.to_pydatetime()
            except AttributeError:
                raise AdapterError(f"Unexpected timestamp type: {type(ts_raw)}")
            candles.append(
                Candle(
                    timestamp=ts,
                    open=Decimal(str(row["Open"])),
                    high=Decimal(str(row["High"])),
                    low=Decimal(str(row["Low"])),
                    close=Decimal(str(row["Close"])),
                    volume=int(row["Volume"]),
                )
            )
        return OHLCVSeries(symbol=symbol, timeframe=timeframe, candles=candles)

    def to_stock_meta(self, raw: dict[str, Any], symbol: str) -> StockMeta:
        return StockMeta(
            symbol=symbol,
            name=raw.get("longName") or raw.get("shortName"),
            exchange=raw.get("exchange"),
            currency=raw.get("currency", "USD"),
        )
