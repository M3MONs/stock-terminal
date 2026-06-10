from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime

from data.adapters.base import AdapterError
from data.adapters.twelvedata import TwelveDataAdapter
from models.timeframe import Timeframe


_RAW_OHLCV = {
    "symbol": "AAPL",
    "timeframe": "1d",
    "rows": [
        {
            "datetime": "2024-01-02 09:30:00",
            "open": "150.25",
            "high": "152.00",
            "low": "149.80",
            "close": "151.50",
            "volume": "987654",
        },
        {
            "datetime": "2024-01-03 09:30:00",
            "open": "151.50",
            "high": "153.00",
            "low": "150.00",
            "close": "152.75",
            "volume": "654321",
        },
    ],
}

_RAW_META = {
    "name": "Apple Inc",
    "exchange": "NASDAQ",
    "currency": "USD",
    "close": "151.50",
    "percent_change": "0.45",
}


def test_to_ohlcv_series_candle_count():
    adapter = TwelveDataAdapter()
    series = adapter.to_ohlcv_series(_RAW_OHLCV, "AAPL", Timeframe.D1)
    assert len(series.candles) == 2


def test_to_ohlcv_series_symbol_and_timeframe():
    adapter = TwelveDataAdapter()
    series = adapter.to_ohlcv_series(_RAW_OHLCV, "AAPL", Timeframe.D1)
    assert series.symbol == "AAPL"
    assert series.timeframe == Timeframe.D1


def test_to_ohlcv_series_decimal_values():
    adapter = TwelveDataAdapter()
    series = adapter.to_ohlcv_series(_RAW_OHLCV, "AAPL", Timeframe.D1)
    candle = series.candles[0]
    assert candle.open == Decimal("150.25")
    assert candle.high == Decimal("152.00")
    assert candle.low == Decimal("149.80")
    assert candle.close == Decimal("151.50")
    assert candle.volume == 987654


def test_to_ohlcv_series_timestamp_parsed():
    adapter = TwelveDataAdapter()
    series = adapter.to_ohlcv_series(_RAW_OHLCV, "AAPL", Timeframe.D1)
    assert series.candles[0].timestamp == datetime(2024, 1, 2, 9, 30, 0)


def test_to_ohlcv_series_missing_datetime_raises():
    adapter = TwelveDataAdapter()
    raw = {"symbol": "AAPL", "timeframe": "1d", "rows": [{"open": "1", "high": "1", "low": "1", "close": "1", "volume": "1"}]}
    with pytest.raises(AdapterError, match="Missing datetime"):
        adapter.to_ohlcv_series(raw, "AAPL", Timeframe.D1)


def test_to_ohlcv_series_bad_datetime_raises():
    adapter = TwelveDataAdapter()
    raw = {"symbol": "AAPL", "timeframe": "1d", "rows": [{"datetime": "not-a-date", "open": "1", "high": "1", "low": "1", "close": "1", "volume": "1"}]}
    with pytest.raises(AdapterError, match="Unparseable datetime"):
        adapter.to_ohlcv_series(raw, "AAPL", Timeframe.D1)


def test_to_stock_meta_fields():
    adapter = TwelveDataAdapter()
    meta = adapter.to_stock_meta(_RAW_META, "AAPL")
    assert meta.symbol == "AAPL"
    assert meta.name == "Apple Inc"
    assert meta.exchange == "NASDAQ"
    assert meta.currency == "USD"
    assert meta.price == Decimal("151.50")
    assert meta.change_pct == pytest.approx(0.45)


def test_to_stock_meta_missing_optional_fields():
    adapter = TwelveDataAdapter()
    meta = adapter.to_stock_meta({}, "AAPL")
    assert meta.price is None
    assert meta.change_pct is None
    assert meta.currency == "USD"
