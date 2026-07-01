from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from models.timeframe import Timeframe


class DataSource(ABC):
    def __init__(self, **kwargs) -> None:
        pass

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, limit: int = 100) -> dict[str, Any]: ...

    @abstractmethod
    def fetch_meta(self, symbol: str) -> dict[str, Any]: ...

    def fetch_fundamentals(self, symbol: str) -> dict[str, Any]:
        return {}


class SourceError(Exception): ...
class SourceAuthError(SourceError): ...
class SourceRateLimitError(SourceError): ...
