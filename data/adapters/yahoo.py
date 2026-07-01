from __future__ import annotations

from decimal import Decimal
from typing import Any

from data.adapters.base import DataAdapter, AdapterError
from data.adapters.registry import register_adapter
from models.candle import Candle
from models.fundamentals import StockFundamentals
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
        raw_price = raw.get("regularMarketPrice") or raw.get("currentPrice")
        raw_change = raw.get("regularMarketChangePercent")
        return StockMeta(
            symbol=symbol,
            name=raw.get("longName") or raw.get("shortName"),
            exchange=raw.get("exchange"),
            currency=raw.get("currency", "USD"),
            price=Decimal(str(raw_price)) if raw_price is not None else None,
            change_pct=float(raw_change) if raw_change is not None else None,
        )

    def to_fundamentals(self, raw: dict[str, Any]) -> StockFundamentals | None:
        if not raw:
            return None

        def _f(key: str) -> float | None:
            v = raw.get(key)
            return float(v) if v is not None else None

        return StockFundamentals(
            market_cap=raw.get("marketCap"),
            trailing_pe=_f("trailingPE"),
            forward_pe=_f("forwardPE"),
            peg_ratio=_f("pegRatio"),
            price_to_book=_f("priceToBook"),
            profit_margins=_f("profitMargins"),
            revenue_growth=_f("revenueGrowth"),
            debt_to_equity=_f("debtToEquity"),
            return_on_equity=_f("returnOnEquity"),
            dividend_yield=_f("dividendYield"),
            fifty_two_week_high=_f("fiftyTwoWeekHigh"),
            fifty_two_week_low=_f("fiftyTwoWeekLow"),
            beta=_f("beta"),
        )
