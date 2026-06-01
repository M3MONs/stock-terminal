from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from models.candle import Candle
from models.ohlcv_series import OHLCVSeries
from models.timeframe import Timeframe


def _candle(ts="2024-01-02T09:30:00") -> Candle:
    return Candle(
        timestamp=datetime.fromisoformat(ts),
        open=Decimal("100"),
        high=Decimal("105"),
        low=Decimal("99"),
        close=Decimal("103"),
        volume=500_000,
    )


def test_empty_candles():
    s = OHLCVSeries(symbol="AAPL", timeframe=Timeframe.D1, candles=[])
    assert s.candles == []
    assert s.meta is None


def test_with_candles():
    candles = [_candle("2024-01-02T09:30:00"), _candle("2024-01-02T09:35:00")]
    s = OHLCVSeries(symbol="AAPL", timeframe=Timeframe.M5, candles=candles)
    assert len(s.candles) == 2


def test_symbol_stored():
    s = OHLCVSeries(symbol="TSLA", timeframe=Timeframe.H1, candles=[])
    assert s.symbol == "TSLA"


def test_missing_required_field_raises():
    with pytest.raises(ValidationError):
        OHLCVSeries(timeframe=Timeframe.D1, candles=[])  # type: ignore[call-arg]
