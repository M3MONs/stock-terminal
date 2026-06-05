from __future__ import annotations

from typing import TypeVar, cast

from pydantic import BaseModel

from connectors.base import BaseAgentConnector, ConnectorError
from connectors.registry import register_connector

T = TypeVar("T", bound=BaseModel)


@register_connector("gemini", key_field="gemini_api_key")
class GeminiConnector(BaseAgentConnector):
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.0,
        api_key: str = "",
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, **kwargs)
        self._api_key = api_key

    def ping(self) -> None:
        try:
            from google import genai
        except ImportError as e:
            raise ConnectorError("google-genai not installed") from e
        
        if not self._api_key:
            raise ConnectorError("Gemini API key not configured")
        
        try:
            client = genai.Client(api_key=self._api_key)
            next(iter(client.models.list()))
        except ConnectorError:
            raise
        except Exception as e:
            raise ConnectorError(str(e)) from e

    def generate_structured(self, prompt: str, response_model: type[T], **kwargs) -> T:
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ConnectorError("google-genai not installed") from e

        if not self._api_key:
            raise ConnectorError("Gemini API key not configured")

        try:
            client = genai.Client(api_key=self._api_key)
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
