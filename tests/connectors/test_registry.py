import pytest

from connectors.base import BaseAgentConnector, ConnectorError
from connectors.registry import get_connector, get_connector_key_field, list_connectors, register_connector


class _DummyConnector(BaseAgentConnector):
    def generate_structured(self, prompt, response_model, **kwargs):
        raise ConnectorError("not implemented")


def test_register_and_get():
    register_connector("_test_dummy")(_DummyConnector)
    connector = get_connector("_test_dummy", model_name="test-model")
    assert isinstance(connector, _DummyConnector)
    assert connector.model_name == "test-model"


def test_get_unknown_raises_key_error():
    with pytest.raises(KeyError, match="not registered"):
        get_connector("_nonexistent_connector_xyz")


def test_list_connectors_returns_list():
    register_connector("_test_list")(_DummyConnector)
    names = list_connectors()
    assert "_test_list" in names


def test_connector_error_is_exception():
    with pytest.raises(ConnectorError):
        raise ConnectorError("test error")


def test_register_connector_with_key_field():
    register_connector("_test_keyed", key_field="my_api_key")(_DummyConnector)
    assert get_connector_key_field("_test_keyed") == "my_api_key"


def test_get_connector_key_field_unknown_returns_empty():
    assert get_connector_key_field("_nonexistent_xyz") == ""


def test_gemini_key_field():
    assert get_connector_key_field("gemini") == "gemini_api_key"


def test_deepseek_key_field():
    assert get_connector_key_field("deepseek") == "deepseek_api_key"
