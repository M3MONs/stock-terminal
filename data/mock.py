import random
from datetime import datetime, timedelta, timezone
from typing import Any

from data.base import DataSource
from data.registry import register_source
from models.timeframe import Timeframe


@register_source("mock")
class MockDataSource(DataSource):
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, limit: int = 100) -> dict[str, Any]:
        candles = self._generate_candles(limit)
        return {"symbol": symbol, "timeframe": str(timeframe), "candles": candles}

    def _generate_candles(self, limit: int) -> list[dict[str, Any]]:
        candles = []
        price = random.uniform(50.0, 500.0)
        now = datetime.now(timezone.utc)
        for i in range(limit):
            ts = now - timedelta(hours=limit - i)
            candle, price = self._build_candle(ts, price)
            candles.append(candle)
        return candles

    def _build_candle(self, ts: datetime, open_: float) -> tuple[dict[str, Any], float]:
        change = random.uniform(-open_ * 0.02, open_ * 0.02)
        close = max(0.01, open_ + change)
        high = max(open_, close) + random.uniform(0, abs(change) * 0.5)
        low = min(open_, close) - random.uniform(0, abs(change) * 0.5)
        candle = {
            "timestamp": ts.isoformat(),
            "open": str(round(open_, 2)),
            "high": str(round(high, 2)),
            "low": str(round(low, 2)),
            "close": str(round(close, 2)),
            "volume": random.randint(1_000, 10_000_000),
        }
        return candle, close

    def fetch_meta(self, symbol: str) -> dict[str, Any]:
        price = round(random.uniform(10.0, 500.0), 2)
        change_pct = round(random.uniform(-5.0, 5.0), 2)
        return {
            "symbol": symbol,
            "name": f"{symbol} Corp",
            "exchange": "MOCK",
            "currency": "USD",
            "price": price,
            "change_pct": change_pct,
        }
