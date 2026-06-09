from __future__ import annotations

from types import ModuleType
from typing import TypeVar, cast

from google.genai.client import Client
from pydantic import BaseModel

from connectors.base import BaseAgentConnector, ConnectorAuthError, ConnectorError
from connectors.registry import register_connector

T = TypeVar("T", bound=BaseModel)


@register_connector("gemini", key_field="gemini_api_key")
class GeminiConnector(BaseAgentConnector):
    def __init__(
        self,
        model_name: str = "gemini-3.5-flash",
        temperature: float = 0.0,
        api_key: str = "",
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, **kwargs)
        self._api_key = api_key

    def _get_client(self) -> tuple[Client, ModuleType]:
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ConnectorError("google-genai not installed") from e
        if not self._api_key:
            raise ConnectorAuthError("Gemini API key not configured")
        return genai.Client(api_key=self._api_key), types

    def ping(self) -> None:
        client, _ = self._get_client()
        try:
            next(iter(client.models.list()))
        except ConnectorError:
            raise
        except Exception as e:
            raise ConnectorError(str(e)) from e

    def generate_structured(self, prompt: str, response_model: type[T], **kwargs) -> T:
        client, types = self._get_client()
        try:
            config = types.GenerateContentConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=response_model,
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            if response.parsed is not None:
                return cast(T, response.parsed)
            return response_model.model_validate_json(response.text or "")
        except ConnectorError:
            raise
        except Exception as e:
            raise ConnectorError(str(e)) from e
