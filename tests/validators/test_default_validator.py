import pytest
from validators.default import DefaultSymbolValidator


@pytest.fixture
def v() -> DefaultSymbolValidator:
    return DefaultSymbolValidator()


@pytest.mark.parametrize("symbol", ["AAPL", "BRK.B", "BRK-B", "A", "ABCDEFGHIJKLMNO"])
def test_valid_symbols(v, symbol):
    assert v.validate(symbol) is None


@pytest.mark.parametrize("symbol", [
    "",                   # empty
    "aapl",               # lowercase
    "AAPL MSFT",          # space
    "AAPL!",              # special char
    "A" * 16,             # too long (>15)
])
def test_invalid_symbols(v, symbol):
    assert v.validate(symbol) is not None


def test_empty_returns_specific_message(v):
    assert "empty" in v.validate("").lower()


def test_invalid_returns_specific_message(v):
    msg = v.validate("aapl")
    assert msg is not None
    assert "1-15" in msg or "letters" in msg.lower() or "chars" in msg.lower()
