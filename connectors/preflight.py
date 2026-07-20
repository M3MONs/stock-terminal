from __future__ import annotations

from connectors.base import ConnectorAuthError, ConnectorNotConfiguredError
from connectors.registry import get_connector_key_field
from infra.security.keystore import get_secret
from models.app_config import AppConfig


def connector_preflight(cfg: AppConfig) -> None:
    """Raise if connector or its API key is not ready for signal generation."""
    if not cfg.connector:
        raise ConnectorNotConfiguredError("no connector set")
    key_field = get_connector_key_field(cfg.connector)
    if key_field and not get_secret(key_field):
        raise ConnectorAuthError(f"no API key for {cfg.connector}")
