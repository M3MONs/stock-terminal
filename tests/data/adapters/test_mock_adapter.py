import pytest
from decimal import Decimal

from data.adapters.mock import MockAdapter
from models.timeframe import Timeframe


RAW_OHLCV = {
    "candles": [
        {
            "timestamp": "2024-01-02T09:30:00",
            "open": "100.00",
            "high": "105.50",
            "low": "99.00",
            "close": "103.25",
            "volume": "1000000",
        },
        {
            "timestamp": "2024-01-02T09:35:00",
            "open": "103.25",
            "high": "106.00",
            "low": "102.00",
            "close": "104.50",
            "volume": "800000",
        },
    ]
}

RAW_META = {
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "currency": "USD",
    "price": "185.50",
    "change_pct": "1.23",
}


def test_to_ohlcv_series_candle_count():
    adapter = MockAdapter()
    series = adapter.to_ohlcv_series(RAW_OHLCV, "AAPL", Timeframe.M5)
    assert len(series.candles) == 2


def test_to_ohlcv_series_symbol_and_timeframe():
    adapter = MockAdapter()
    series = adapter.to_ohlcv_series(RAW_OHLCV, "AAPL", Timeframe.M5)
    assert series.symbol == "AAPL"
    assert series.timeframe == Timeframe.M5


def test_to_ohlcv_series_decimal_values():
    adapter = MockAdapter()
    series = adapter.to_ohlcv_series(RAW_OHLCV, "AAPL", Timeframe.M5)
    assert series.candles[0].open == Decimal("100.00")
    assert series.candles[0].volume == 1_000_000


def test_to_stock_meta_fields():
    adapter = MockAdapter()
    meta = adapter.to_stock_meta(RAW_META, "AAPL")
    assert meta.symbol == "AAPL"
    assert meta.name == "Apple Inc."
    assert meta.price == Decimal("185.50")
    assert meta.change_pct == pytest.approx(1.23)


def test_to_stock_meta_missing_optional_fields():
    adapter = MockAdapter()
    meta = adapter.to_stock_meta({}, "AAPL")
    assert meta.price is None
    assert meta.change_pct is None
    assert meta.currency == "USD"
