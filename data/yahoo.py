from __future__ import annotations

import re
from typing import Any

import yfinance as yf

from data.base import DataSource, SourceError
from data.registry import register_source
from models.timeframe import Timeframe

_INTERVAL_MAP: dict[Timeframe, str] = {
    Timeframe.M5: "5m",
    Timeframe.M15: "15m",
    Timeframe.M30: "30m",
    Timeframe.H1: "1h",
    Timeframe.H4: "4h",
    Timeframe.D1: "1d",
    Timeframe.W1: "1wk",
}

_INTRADAY = {Timeframe.M5, Timeframe.M15, Timeframe.M30, Timeframe.H1, Timeframe.H4}
_FX_PAIR_RE = re.compile(r"^[A-Z]{6}$")
_FX_CODES = {
    "AUD",
    "CAD",
    "CHF",
    "CNY",
    "CZK",
    "DKK",
    "EUR",
    "GBP",
    "HKD",
    "HUF",
    "JPY",
    "MXN",
    "NOK",
    "NZD",
    "PLN",
    "SEK",
    "SGD",
    "TRY",
    "USD",
    "ZAR",
}


@register_source("yahoo")
class YahooSource(DataSource):
    def resolve_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if normalized.endswith("=X"):
            return normalized
        if _FX_PAIR_RE.match(normalized):
            base, quote = normalized[:3], normalized[3:]
            if base in _FX_CODES and quote in _FX_CODES:
                return f"{normalized}=X"
        return normalized

    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, limit: int = 100) -> dict[str, Any]:
        interval = _INTERVAL_MAP[timeframe]
        period = "60d" if timeframe in _INTRADAY else "max"
        try:
            df = yf.Ticker(symbol).history(period=period, interval=interval)
        except Exception as e:
            raise SourceError(str(e)) from e
        if df.empty:
            raise SourceError(f"No data returned for symbol: {symbol}")
        df = df.tail(limit).reset_index()
        return {"symbol": symbol, "timeframe": str(timeframe), "rows": df.to_dict("records")}

    def fetch_meta(self, symbol: str) -> dict[str, Any]:
        try:
            info = yf.Ticker(symbol).info
        except Exception as e:
            raise SourceError(str(e)) from e
        if not info.get("symbol") and not info.get("regularMarketPrice") and not info.get("currentPrice"):
            raise SourceError(f"Symbol not found: {symbol}")
        return info

    def fetch_fundamentals(self, symbol: str) -> dict[str, Any]:
        try:
            return yf.Ticker(symbol).info
        except Exception as e:
            raise SourceError(str(e)) from e
