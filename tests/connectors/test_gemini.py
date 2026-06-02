from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from connectors.base import ConnectorError
from connectors.gemini import GeminiConnector
from connectors.registry import list_connectors


class _SampleModel(BaseModel):
    value: int
    label: str


def test_gemini_registered():
    assert "gemini" in list_connectors()


def test_raises_without_api_key():
    connector = GeminiConnector(api_key="", model_name="gemini-2.0-flash")
    with pytest.raises(ConnectorError, match="API key not configured"):
        connector.generate_structured("test", _SampleModel)


def test_generate_structured_returns_model():
    connector = GeminiConnector(model_name="gemini-2.0-flash", api_key="fake-key")

    mock_response = MagicMock()
    mock_response.parsed = _SampleModel(value=42, label="hello")

    with patch("google.genai.Client") as MockClient, \
         patch("google.genai.types.GenerateContentConfig"):
        MockClient.return_value.models.generate_content.return_value = mock_response
        result = connector.generate_structured("prompt", _SampleModel)

    assert isinstance(result, _SampleModel)
    assert result.value == 42
    assert result.label == "hello"


def test_generate_structured_falls_back_to_json_when_parsed_none():
    connector = GeminiConnector(api_key="fake-key", model_name="gemini-2.0-flash")

    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = '{"value": 7, "label": "world"}'

    with patch("google.genai.Client") as MockClient, \
         patch("google.genai.types.GenerateContentConfig"):
        MockClient.return_value.models.generate_content.return_value = mock_response
        result = connector.generate_structured("prompt", _SampleModel)

    assert result.value == 7
    assert result.label == "world"


def test_generate_structured_wraps_api_error():
    connector = GeminiConnector(api_key="fake-key", model_name="gemini-2.0-flash")

    with patch("google.genai.Client") as MockClient, \
         patch("google.genai.types.GenerateContentConfig"):
        MockClient.return_value.models.generate_content.side_effect = Exception("network error")
        with pytest.raises(ConnectorError, match="network error"):
            connector.generate_structured("prompt", _SampleModel)


def test_generate_structured_wraps_invalid_json():
    connector = GeminiConnector(api_key="fake-key", model_name="gemini-2.0-flash")

    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = "not-json"

    with patch("google.genai.Client") as MockClient, \
         patch("google.genai.types.GenerateContentConfig"):
        MockClient.return_value.models.generate_content.return_value = mock_response
        with pytest.raises(ConnectorError):
            connector.generate_structured("prompt", _SampleModel)


def test_ping_ok():
    connector = GeminiConnector(api_key="fake-key", model_name="gemini-2.0-flash")

    mock_model = MagicMock()
    with patch("google.genai.Client") as MockClient:
        MockClient.return_value.models.list.return_value = iter([mock_model])
        connector.ping()  # should not raise


def test_ping_raises_without_api_key():
    connector = GeminiConnector(api_key="", model_name="gemini-2.0-flash")
    with pytest.raises(ConnectorError, match="API key not configured"):
        connector.ping()


def test_ping_wraps_api_error():
    connector = GeminiConnector(api_key="fake-key", model_name="gemini-2.0-flash")
    with patch("google.genai.Client") as MockClient:
        MockClient.return_value.models.list.side_effect = Exception("403 API key invalid")
        with pytest.raises(ConnectorError, match="403 API key invalid"):
            connector.ping()
