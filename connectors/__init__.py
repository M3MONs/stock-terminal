from __future__ import annotations

import importlib
import pkgutil

from connectors.registry import get_connector, list_connectors

__all__ = ["get_connector", "list_connectors"]


def _autodiscover() -> None:
    import connectors

    for _, name, _ in pkgutil.iter_modules(connectors.__path__):
        if name not in ("base", "registry"):
            try:
                importlib.import_module(f"connectors.{name}")
            except ImportError:
                pass


_autodiscover()
