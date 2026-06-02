from __future__ import annotations

from typing import Callable

from connectors.base import BaseAgentConnector

_connectors: dict[str, type[BaseAgentConnector]] = {}
_key_fields: dict[str, str] = {}


def register_connector(name: str, key_field: str = "") -> Callable[..., type[BaseAgentConnector]]:
    def decorator(cls: type[BaseAgentConnector]) -> type[BaseAgentConnector]:
        _connectors[name] = cls
        _key_fields[name] = key_field
        return cls
    return decorator


def get_connector(name: str, **kwargs) -> BaseAgentConnector:
    if name not in _connectors:
        raise KeyError(f"Connector '{name}' not registered. Available: {list(_connectors)}")
    return _connectors[name](**kwargs)


def get_connector_key_field(name: str) -> str:
    return _key_fields.get(name, "")


def list_connectors() -> list[str]:
    return list(_connectors)
