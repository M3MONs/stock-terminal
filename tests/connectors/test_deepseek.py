from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from connectors.base import ConnectorError
from connectors.deepseek import DeepSeekConnector
from connectors.registry import list_connectors


class _SampleModel(BaseModel):
    value: int
    label: str


def test_deepseek_registered():
    assert "deepseek" in list_connectors()


def test_raises_without_api_key():
    connector = DeepSeekConnector(api_key="", model_name="test-model")
    with pytest.raises(ConnectorError, match="API key not configured"):
        connector.generate_structured("test", _SampleModel)


def test_generate_structured_returns_model():
    connector = DeepSeekConnector(api_key="fake-key", model_name="test-model")

    mock_message = MagicMock()
    mock_message.content = '{"value": 42, "label": "hello"}'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = mock_response
        result = connector.generate_structured("prompt", _SampleModel)

    assert isinstance(result, _SampleModel)
    assert result.value == 42
    assert result.label == "hello"


def test_generate_structured_wraps_invalid_json():
    connector = DeepSeekConnector(api_key="fake-key", model_name="test-model")

    mock_message = MagicMock()
    mock_message.content = "not-json"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = mock_response
        with pytest.raises(ConnectorError):
            connector.generate_structured("prompt", _SampleModel)


def test_generate_structured_wraps_api_error():
    connector = DeepSeekConnector(api_key="fake-key", model_name="test-model")

    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.side_effect = Exception("network error")
        with pytest.raises(ConnectorError, match="network error"):
            connector.generate_structured("prompt", _SampleModel)


def test_ping_ok():
    connector = DeepSeekConnector(api_key="fake-key", model_name="test-model")

    mock_model = MagicMock()
    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.models.list.return_value = iter([mock_model])
        connector.ping()  # should not raise


def test_ping_raises_without_api_key():
    connector = DeepSeekConnector(api_key="", model_name="test-model")
    with pytest.raises(ConnectorError, match="API key not configured"):
        connector.ping()


def test_ping_wraps_api_error():
    connector = DeepSeekConnector(api_key="fake-key", model_name="test-model")
    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.models.list.side_effect = Exception("401 Unauthorized")
        with pytest.raises(ConnectorError, match="401 Unauthorized"):
            connector.ping()
