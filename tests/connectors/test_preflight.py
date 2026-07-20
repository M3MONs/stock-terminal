from unittest.mock import patch

import pytest

from connectors.base import (
    BaseAgentConnector,
    ConnectorAuthError,
    ConnectorError,
    ConnectorNotConfiguredError,
)
from connectors.preflight import connector_preflight
from connectors.registry import register_connector
from models.app_config import AppConfig


class _DummyConnector(BaseAgentConnector):
    def generate_structured(self, prompt, response_model, **kwargs):
        raise ConnectorError("not implemented")


register_connector("_preflight_keyed", key_field="preflight_test_key")(_DummyConnector)
register_connector("_preflight_no_key")(_DummyConnector)


def test_preflight_empty_connector_raises():
    with pytest.raises(ConnectorNotConfiguredError, match="no connector set"):
        connector_preflight(AppConfig(connector=""))


def test_preflight_missing_secret_raises():
    with patch("connectors.preflight.get_secret", return_value=""):
        with pytest.raises(ConnectorAuthError, match="no API key for _preflight_keyed"):
            connector_preflight(AppConfig(connector="_preflight_keyed"))


def test_preflight_ok_when_secret_present():
    with patch("connectors.preflight.get_secret", return_value="secret"):
        connector_preflight(AppConfig(connector="_preflight_keyed"))


def test_preflight_ok_when_no_key_field():
    connector_preflight(AppConfig(connector="_preflight_no_key"))
