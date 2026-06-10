from __future__ import annotations
from typing import Callable

from data.base import DataSource

_sources: dict[str, type[DataSource]] = {}
_key_fields: dict[str, str] = {}


def register_source(name: str, key_field: str = "") -> Callable[..., type[DataSource]]:
    def decorator(cls: type[DataSource]) -> type[DataSource]:
        _sources[name] = cls
        _key_fields[name] = key_field
        return cls
    return decorator


def get_source_key_field(name: str) -> str:
    return _key_fields.get(name, "")


def get_source(name: str, api_key: str = "") -> DataSource:
    if name not in _sources:
        raise KeyError(f"Source '{name}' not registered. Available: {list(_sources)}")
    if api_key:
        return _sources[name](api_key=api_key)
    return _sources[name]()


def list_sources() -> list[str]:
    return list(_sources)
