from __future__ import annotations

import logging
from typing import Any

import requests
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
_TIMEOUT: tuple[float, float] = (3.05, 15.0)

_log = logging.getLogger(__name__)


def _is_rate_limited(exc: Exception) -> bool:
    msg = str(exc).lower()
    if "too many requests" in msg or "rate limit" in msg:
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        resp = getattr(exc, "response", None)
        if resp is not None and resp.status_code == 429:
            return True
    return False


class _TimeoutSession(requests.Session):
    def request(self, *args: Any, **kwargs: Any):
        kwargs.setdefault("timeout", _TIMEOUT)
        return super().request(*args, **kwargs)


@register_source("yahoo")
class YahooSource(DataSource):
    def __init__(self) -> None:
        super().__init__()
        self._session = _TimeoutSession()

    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, limit: int = 100) -> dict[str, Any]:
        interval = _INTERVAL_MAP[timeframe]
        period = "60d" if timeframe in _INTRADAY else "max"
        _log.debug("Fetching OHLCV for %s interval=%s period=%s", symbol, interval, period)
        try:
            df = yf.Ticker(symbol, session=self._session).history(period=period, interval=interval, timeout=_TIMEOUT[1])
        except requests.exceptions.Timeout:
            _log.warning("Timeout fetching OHLCV for %s (interval=%s)", symbol, interval)
            raise SourceError(f"Request timed out for symbol: {symbol}")
        except Exception as e:
            if _is_rate_limited(e):
                _log.warning("Yahoo Finance rate limit hit for %s (interval=%s): %s", symbol, interval, e)
                raise SourceError(f"Rate limited by Yahoo Finance for symbol: {symbol}") from e
            _log.error("Unexpected error fetching OHLCV for %s: %s", symbol, e, exc_info=True)
            raise SourceError(str(e)) from e
        if df.empty:
            _log.warning("No OHLCV data returned for %s (interval=%s, period=%s)", symbol, interval, period)
            raise SourceError(f"No data returned for symbol: {symbol}")
        df = df.tail(limit).reset_index()
        _log.debug("Fetched %d candles for %s (%s)", len(df), symbol, interval)
        return {"symbol": symbol, "timeframe": str(timeframe), "rows": df.to_dict("records")}

    def fetch_meta(self, symbol: str) -> dict[str, Any]:
        _log.debug("Fetching meta for %s", symbol)
        try:
            info = yf.Ticker(symbol, session=self._session).info
        except requests.exceptions.Timeout:
            _log.warning("Timeout fetching meta for %s", symbol)
            raise SourceError(f"Request timed out for symbol: {symbol}")
        except Exception as e:
            if _is_rate_limited(e):
                _log.warning("Yahoo Finance rate limit hit fetching meta for %s: %s", symbol, e)
                raise SourceError(f"Rate limited by Yahoo Finance for symbol: {symbol}") from e
            _log.error("Unexpected error fetching meta for %s: %s", symbol, e, exc_info=True)
            raise SourceError(str(e)) from e
        if not info.get("symbol") and not info.get("regularMarketPrice") and not info.get("currentPrice"):
            _log.warning("Symbol not found or empty info for %s", symbol)
            raise SourceError(f"Symbol not found: {symbol}")
        return info
