from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from data.base import SourceAuthError, SourceError, SourceRateLimitError
from data.twelvedata import TwelveDataSource, _rate_limiter
from models.timeframe import Timeframe


def _make_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.text = ""
    r.json.return_value = json_data or {}
    return r


_SERIES_RESPONSE = {
    "status": "ok",
    "values": [
        {"datetime": "2024-01-03 09:30:00", "open": "152.0", "high": "153.0", "low": "151.0", "close": "152.5", "volume": "500000"},
        {"datetime": "2024-01-02 09:30:00", "open": "150.0", "high": "152.0", "low": "149.5", "close": "151.5", "volume": "987654"},
    ],
}

_QUOTE_RESPONSE = {
    "symbol": "AAPL",
    "name": "Apple Inc",
    "exchange": "NASDAQ",
    "currency": "USD",
    "close": "151.50",
    "percent_change": "0.45",
}


@pytest.fixture(autouse=True)
def skip_rate_limit():
    """Bypass rate limiter in unit tests."""
    with patch.object(_rate_limiter, "wait", return_value=None):
        yield


def test_fetch_ohlcv_returns_chronological_rows():
    src = TwelveDataSource(api_key="test-key")
    with patch("data.twelvedata.httpx.get", return_value=_make_response(200, _SERIES_RESPONSE)):
        raw = src.fetch_ohlcv("AAPL", Timeframe.D1, limit=100)
    # API returns newest-first; source must reverse to chronological
    assert raw["rows"][0]["datetime"] == "2024-01-02 09:30:00"
    assert raw["rows"][1]["datetime"] == "2024-01-03 09:30:00"


def test_fetch_ohlcv_raw_shape():
    src = TwelveDataSource(api_key="test-key")
    with patch("data.twelvedata.httpx.get", return_value=_make_response(200, _SERIES_RESPONSE)):
        raw = src.fetch_ohlcv("AAPL", Timeframe.D1, limit=100)
    assert raw["symbol"] == "AAPL"
    assert raw["timeframe"] == str(Timeframe.D1)
    assert len(raw["rows"]) == 2


def test_fetch_ohlcv_empty_values_raises():
    src = TwelveDataSource(api_key="test-key")
    with patch("data.twelvedata.httpx.get", return_value=_make_response(200, {"status": "ok", "values": []})):
        with pytest.raises(SourceError, match="No data returned"):
            src.fetch_ohlcv("AAPL", Timeframe.D1)


def test_fetch_ohlcv_missing_values_raises():
    src = TwelveDataSource(api_key="test-key")
    with patch("data.twelvedata.httpx.get", return_value=_make_response(200, {"status": "ok"})):
        with pytest.raises(SourceError, match="No data returned"):
            src.fetch_ohlcv("AAPL", Timeframe.D1)


def test_fetch_meta_returns_raw():
    src = TwelveDataSource(api_key="test-key")
    with patch("data.twelvedata.httpx.get", return_value=_make_response(200, _QUOTE_RESPONSE)):
        raw = src.fetch_meta("AAPL")
    assert raw["name"] == "Apple Inc"


def test_401_raises_source_auth_error():
    src = TwelveDataSource(api_key="bad-key")
    with patch("data.twelvedata.httpx.get", return_value=_make_response(401)):
        with pytest.raises(SourceAuthError):
            src.fetch_ohlcv("AAPL", Timeframe.D1)


def test_429_raises_source_rate_limit_error():
    src = TwelveDataSource(api_key="test-key")
    with patch("data.twelvedata.httpx.get", return_value=_make_response(429)):
        with pytest.raises(SourceRateLimitError):
            src.fetch_ohlcv("AAPL", Timeframe.D1)


def test_5xx_raises_source_error():
    src = TwelveDataSource(api_key="test-key")
    r = _make_response(500)
    r.text = "Internal Server Error"
    with patch("data.twelvedata.httpx.get", return_value=r):
        with pytest.raises(SourceError, match="HTTP 500"):
            src.fetch_ohlcv("AAPL", Timeframe.D1)


def test_body_status_error_raises_source_error():
    src = TwelveDataSource(api_key="test-key")
    body = {"status": "error", "message": "Symbol not found"}
    with patch("data.twelvedata.httpx.get", return_value=_make_response(200, body)):
        with pytest.raises(SourceError, match="Symbol not found"):
            src.fetch_ohlcv("AAPL", Timeframe.D1)


def test_twelvedata_registered():
    from data.registry import get_source, get_source_key_field, list_sources
    assert "twelvedata" in list_sources()
    assert get_source_key_field("twelvedata") == "twelvedata_api_key"
    src = get_source("twelvedata", api_key="key")
    assert isinstance(src, TwelveDataSource)
