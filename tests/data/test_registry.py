import pytest

from data.base import DataSource, SourceAuthError
from data.registry import get_source, get_source_key_field, list_sources, register_source

class _DummySource(DataSource):
    def __init__(self, **kwargs) -> None:
        self.api_key = kwargs.get("api_key", "")

    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        return {}

    def fetch_meta(self, symbol):
        return {}


class _KeyedSource(DataSource):
    def __init__(self, api_key: str = "", **kwargs) -> None:
        self.api_key = api_key

    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        if not self.api_key:
            raise SourceAuthError("key required")
        return {}

    def fetch_meta(self, symbol):
        return {}


def test_register_and_get():
    register_source("_test_dummy")(_DummySource)
    source = get_source("_test_dummy")
    assert isinstance(source, _DummySource)


def test_get_unknown_raises_key_error():
    with pytest.raises(KeyError, match="not registered"):
        get_source("_nonexistent_source_xyz")


def test_list_sources_returns_list():
    register_source("_test_list")(_DummySource)
    assert "_test_list" in list_sources()


def test_register_source_without_key_field():
    register_source("_test_no_key")(_DummySource)
    assert get_source_key_field("_test_no_key") == ""


def test_register_source_with_key_field():
    register_source("_test_keyed_src", key_field="my_api_key")(_KeyedSource)
    assert get_source_key_field("_test_keyed_src") == "my_api_key"


def test_get_source_key_field_unknown_returns_empty():
    assert get_source_key_field("_nonexistent_xyz") == ""


def test_get_source_passes_api_key():
    register_source("_test_key_pass", key_field="some_key")(_KeyedSource)
    source = get_source("_test_key_pass", api_key="secret")
    assert isinstance(source, _KeyedSource)
    assert source.api_key == "secret"


def test_get_source_no_api_key_no_crash_for_keyless_source():
    register_source("_test_no_crash")(_DummySource)
    source = get_source("_test_no_crash")
    assert isinstance(source, _DummySource)


def test_source_auth_error_is_source_error():
    from data.base import SourceError
    with pytest.raises(SourceError):
        raise SourceAuthError("missing key")


def test_yahoo_unaffected():
    assert "yahoo" in list_sources()
    assert get_source_key_field("yahoo") == ""
    source = get_source("yahoo")
    assert source is not None
