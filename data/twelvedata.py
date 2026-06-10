from __future__ import annotations

from typing import Any

import httpx

from data.base import DataSource, SourceAuthError, SourceError, SourceRateLimitError
from data.rate_limiter import RateLimiter
from data.registry import register_source
from models.timeframe import Timeframe

_BASE_URL = "https://api.twelvedata.com"

_INTERVAL_MAP: dict[Timeframe, str] = {
    Timeframe.M5: "5min",
    Timeframe.M15: "15min",
    Timeframe.M30: "30min",
    Timeframe.H1: "1h",
    Timeframe.H4: "4h",
    Timeframe.D1: "1day",
    Timeframe.W1: "1week",
}

_rate_limiter = RateLimiter(max_per_minute=8)


def _check_response(r: httpx.Response) -> None:
    if r.status_code == 401:
        raise SourceAuthError("TwelveData API key invalid or missing")
    if r.status_code == 429:
        raise SourceRateLimitError("TwelveData rate limit exceeded")
    if r.status_code >= 400:
        raise SourceError(f"TwelveData HTTP {r.status_code}: {r.text[:200]}")
    body = r.json()
    if body.get("status") == "error":
        raise SourceError(f"TwelveData error: {body.get('message', r.text[:200])}")


@register_source("twelvedata", key_field="twelvedata_api_key")
class TwelveDataSource(DataSource):
    def __init__(self, api_key: str = "", **kwargs) -> None:
        self._key = api_key

    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, limit: int = 100) -> dict[str, Any]:
        _rate_limiter.wait()
        r = httpx.get(
            f"{_BASE_URL}/time_series",
            params={
                "symbol": symbol,
                "interval": _INTERVAL_MAP[timeframe],
                "outputsize": limit,
                "apikey": self._key,
            },
            timeout=10,
        )
        _check_response(r)
        data = r.json()
        values = data.get("values")
        if not values:
            raise SourceError(f"No data returned for symbol: {symbol}")
        rows = list(reversed(values))
        return {"symbol": symbol, "timeframe": str(timeframe), "rows": rows}

    def fetch_meta(self, symbol: str) -> dict[str, Any]:
        _rate_limiter.wait()
        r = httpx.get(
            f"{_BASE_URL}/quote",
            params={"symbol": symbol, "apikey": self._key},
            timeout=10,
        )
        _check_response(r)
        return r.json()
