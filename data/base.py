from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from models.timeframe import Timeframe


class DataSource(ABC):
    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, limit: int = 100) -> dict[str, Any]: ...

    @abstractmethod
    def fetch_meta(self, symbol: str) -> dict[str, Any]: ...


class SourceError(Exception): ...
