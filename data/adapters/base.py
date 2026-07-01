from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from models.fundamentals import StockFundamentals
from models.stock_meta import StockMeta
from models.ohlcv_series import OHLCVSeries
from models.timeframe import Timeframe


class DataAdapter(ABC):
    @abstractmethod
    def to_ohlcv_series(self, raw: dict[str, Any], symbol: str, timeframe: Timeframe) -> OHLCVSeries: ...

    @abstractmethod
    def to_stock_meta(self, raw: dict[str, Any], symbol: str) -> StockMeta: ...

    @abstractmethod
    def to_fundamentals(self, raw: dict[str, Any]) -> StockFundamentals | None:
        return None


class AdapterError(ValueError): ...
