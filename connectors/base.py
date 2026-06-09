from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseAgentConnector(ABC):
    def __init__(self, model_name: str, temperature: float = 0.0, **kwargs) -> None:
        self.model_name = model_name
        self.temperature = temperature

    @abstractmethod
    def generate_structured(self, prompt: str, response_model: type[T], **kwargs) -> T: ...

    def ping(self) -> None:
        raise ConnectorError("ping not supported by this connector")


class ConnectorError(Exception): ...
class ConnectorNotConfiguredError(ConnectorError): ...
class ConnectorAuthError(ConnectorError): ...
