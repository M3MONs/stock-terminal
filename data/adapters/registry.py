from __future__ import annotations
from typing import Callable

from data.adapters.base import DataAdapter

_adapters: dict[str, type[DataAdapter]] = {}


def register_adapter(name: str) -> Callable[..., type[DataAdapter]]:
    def decorator(cls: type[DataAdapter]) -> type[DataAdapter]:
        _adapters[name] = cls
        return cls
    return decorator


def get_adapter(name: str) -> DataAdapter:
    if name not in _adapters:
        raise KeyError(f"Adapter '{name}' not registered. Available: {list(_adapters)}")
    return _adapters[name]()


def list_adapters() -> list[str]:
    return list(_adapters)
