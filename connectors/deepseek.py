from __future__ import annotations

import logging
from typing import TypeVar

from pydantic import BaseModel

from connectors.base import BaseAgentConnector, ConnectorAuthError, ConnectorError
from connectors.registry import register_connector

T = TypeVar("T", bound=BaseModel)

_BASE_URL = "https://api.deepseek.com"
_log = logging.getLogger(__name__)


@register_connector("deepseek", key_field="deepseek_api_key")
class DeepSeekConnector(BaseAgentConnector):
    def __init__(
        self,
        model_name: str = "deepseek-v4-pro",
        temperature: float = 0.0,
        api_key: str = "",
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, **kwargs)
        self._api_key = api_key

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ConnectorError("openai not installed") from e
        if not self._api_key:
            raise ConnectorAuthError("DeepSeek API key not configured")
        return OpenAI(api_key=self._api_key, base_url=_BASE_URL)

    def ping(self) -> None:
        try:
            client = self._client()
            next(iter(client.models.list()))
        except ConnectorError:
            raise
        except Exception as e:
            raise ConnectorError(str(e)) from e

    def generate_structured(self, prompt: str, response_model: type[T], **kwargs) -> T:
        _log.debug("generate_structured model=%s prompt_len=%d", self.model_name, len(prompt))
        try:
            client = self._client()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Respond in JSON format."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            _log.debug("generate_structured response_len=%d", len(content))
            return response_model.model_validate_json(content)
        except ConnectorError:
            raise
        except Exception as e:
            _log.error("generate_structured failed: %s", e, exc_info=True)
            raise ConnectorError(str(e)) from e
