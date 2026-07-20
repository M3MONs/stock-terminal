from __future__ import annotations

import importlib
import logging
import pkgutil

from connectors.registry import get_connector, list_connectors

__all__ = ["get_connector", "list_connectors"]

_log = logging.getLogger(__name__)
_discovered = False


def autodiscover() -> None:
    global _discovered
    if _discovered:
        return
    _discovered = True
    import connectors

    for _, name, _ in pkgutil.iter_modules(connectors.__path__):
        if name not in ("base", "registry", "preflight"):
            try:
                importlib.import_module(f"connectors.{name}")
            except ImportError:
                _log.warning("connectors: failed to load '%s' (missing dependency?)", name, exc_info=True)


autodiscover()
