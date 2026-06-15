from __future__ import annotations

import logging
from typing import TypeVar

from pydantic import BaseModel

from connectors.base import BaseAgentConnector, ConnectorAuthError, ConnectorError
from connectors.registry import register_connector

T = TypeVar("T", bound=BaseModel)

_log = logging.getLogger(__name__)


@register_connector("claude", key_field="claude_api_key")
class ClaudeConnector(BaseAgentConnector):
    def __init__(
        self,
        model_name: str = "claude-sonnet-4-6",
        temperature: float = 0.0,
        api_key: str = "",
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, **kwargs)
        self._api_key = api_key

    def _client(self):
        try:
            import anthropic
        except ImportError as e:
            raise ConnectorError("anthropic not installed") from e
        if not self._api_key:
            raise ConnectorAuthError("Claude API key not configured")
        return anthropic.Anthropic(api_key=self._api_key)

    def ping(self) -> None:
        try:
            client = self._client()
            client.models.retrieve(self.model_name)
        except ConnectorError:
            raise
        except Exception as e:
            raise ConnectorError(str(e)) from e

    def generate_structured(self, prompt: str, response_model: type[T], **kwargs) -> T:
        _log.debug("generate_structured model=%s prompt_len=%d", self.model_name, len(prompt))
        try:
            client = self._client()
            tool_name = "respond"
            response = client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                temperature=self.temperature,
                tools=[
                    {
                        "name": tool_name,
                        "description": "Respond with structured data.",
                        "input_schema": response_model.model_json_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": tool_name},
                messages=[{"role": "user", "content": prompt}],
            )
            for block in response.content:
                if block.type == "tool_use" and block.name == tool_name:
                    _log.debug("generate_structured got tool_use block")
                    return response_model.model_validate(block.input)
            raise ConnectorError("No structured response block returned by Claude")
        except ConnectorError:
            raise
        except Exception as e:
            _log.error("generate_structured failed: %s", e, exc_info=True)
            raise ConnectorError(str(e)) from e
