from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from models.candle import Candle


def _candle(**overrides) -> dict:
    base = {
        "timestamp": datetime(2024, 1, 2, 9, 30),
        "open": "100.00",
        "high": "105.50",
        "low": "99.00",
        "close": "103.25",
        "volume": 1_000_000,
    }
    return {**base, **overrides}


def test_valid_candle():
    c = Candle(**_candle())
    assert c.open == Decimal("100.00")
    assert c.volume == 1_000_000


def test_decimal_coercion_from_int():
    c = Candle(**_candle(open=100, high=105, low=99, close=103))
    assert isinstance(c.open, Decimal)


def test_high_below_low_is_allowed():
    # Model has no cross-field constraint; Pydantic stores as-is
    c = Candle(**_candle(high="50.00", low="99.00"))
    assert c.high < c.low


def test_missing_field_raises():
    data = _candle()
    del data["volume"]
    with pytest.raises(ValidationError):
        Candle(**data)


def test_invalid_timestamp_raises():
    with pytest.raises(ValidationError):
        Candle(**_candle(timestamp="not-a-date"))
