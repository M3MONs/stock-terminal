from __future__ import annotations

from typing import Callable

from connectors.base import BaseAgentConnector

_connectors: dict[str, type[BaseAgentConnector]] = {}


def register_connector(name: str) -> Callable[..., type[BaseAgentConnector]]:
    def decorator(cls: type[BaseAgentConnector]) -> type[BaseAgentConnector]:
        _connectors[name] = cls
        return cls
    return decorator


def get_connector(name: str) -> BaseAgentConnector:
    if name not in _connectors:
        raise KeyError(f"Connector '{name}' not registered. Available: {list(_connectors)}")
    return _connectors[name]()


def list_connectors() -> list[str]:
    return list(_connectors)
