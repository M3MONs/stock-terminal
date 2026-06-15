from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from connectors.base import ConnectorAuthError, ConnectorError
from connectors.claude import ClaudeConnector
from connectors.registry import list_connectors


class _SampleModel(BaseModel):
    value: int
    label: str


def test_claude_registered():
    assert "claude" in list_connectors()


def test_raises_without_api_key():
    connector = ClaudeConnector(api_key="", model_name="claude-sonnet-4-6")
    with pytest.raises(ConnectorAuthError, match="API key not configured"):
        connector.generate_structured("test", _SampleModel)


def test_generate_structured_returns_model():
    connector = ClaudeConnector(api_key="fake-key", model_name="claude-sonnet-4-6")

    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "respond"
    mock_block.input = {"value": 42, "label": "hello"}

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        result = connector.generate_structured("prompt", _SampleModel)

    assert isinstance(result, _SampleModel)
    assert result.value == 42
    assert result.label == "hello"


def test_generate_structured_raises_when_no_tool_block():
    connector = ClaudeConnector(api_key="fake-key", model_name="claude-sonnet-4-6")

    mock_block = MagicMock()
    mock_block.type = "text"

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        with pytest.raises(ConnectorError, match="No structured response block"):
            connector.generate_structured("prompt", _SampleModel)


def test_generate_structured_wraps_api_error():
    connector = ClaudeConnector(api_key="fake-key", model_name="claude-sonnet-4-6")

    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = Exception("network error")
        with pytest.raises(ConnectorError, match="network error"):
            connector.generate_structured("prompt", _SampleModel)


def test_ping_ok():
    connector = ClaudeConnector(api_key="fake-key", model_name="claude-sonnet-4-6")

    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.models.retrieve.return_value = MagicMock()
        connector.ping()  # should not raise


def test_ping_raises_without_api_key():
    connector = ClaudeConnector(api_key="", model_name="claude-sonnet-4-6")
    with pytest.raises(ConnectorAuthError, match="API key not configured"):
        connector.ping()


def test_ping_wraps_api_error():
    connector = ClaudeConnector(api_key="fake-key", model_name="claude-sonnet-4-6")
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.models.retrieve.side_effect = Exception("401 Unauthorized")
        with pytest.raises(ConnectorError, match="401 Unauthorized"):
            connector.ping()
