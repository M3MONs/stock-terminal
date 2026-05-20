from __future__ import annotations
from typing import Callable

from data.base import DataSource

_sources: dict[str, type[DataSource]] = {}


def register_source(name: str) -> Callable[..., type[DataSource]]:
    def decorator(cls: type[DataSource]) -> type[DataSource]:
        _sources[name] = cls
        return cls
    return decorator


def get_source(name: str) -> DataSource:
    if name not in _sources:
        raise KeyError(f"Source '{name}' not registered. Available: {list(_sources)}")
    return _sources[name]()


def list_sources() -> list[str]:
    return list(_sources)
