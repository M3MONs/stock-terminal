import importlib
import pkgutil

from data.adapters.base import DataAdapter
from data.adapters.registry import get_adapter
from data.base import DataSource
from models.ohlcv_series import OHLCVSeries
from models.stock_meta import StockMeta
from models.timeframe import Timeframe
from data.registry import get_source


def _autodiscover() -> None:
    import data
    import data.adapters

    for _, name, _ in pkgutil.iter_modules(data.__path__):
        if name not in ("base", "registry"):
            importlib.import_module(f"data.{name}")
    for _, name, _ in pkgutil.iter_modules(data.adapters.__path__):
        if name not in ("base", "registry"):
            importlib.import_module(f"data.adapters.{name}")


_autodiscover()


class StockDataService:
    def __init__(self, source: DataSource, adapter: DataAdapter) -> None:
        self.source = source
        self.adapter = adapter

    def get_ohlcv(self, symbol: str, timeframe: Timeframe, limit: int = 500) -> OHLCVSeries:
        raw = self.source.fetch_ohlcv(symbol, timeframe, limit)
        return self.adapter.to_ohlcv_series(raw, symbol, timeframe)

    def get_meta(self, symbol: str) -> StockMeta:
        raw = self.source.fetch_meta(symbol)
        return self.adapter.to_stock_meta(raw, symbol)


def create_service(provider: str) -> StockDataService:
    return StockDataService(source=get_source(provider), adapter=get_adapter(provider))
