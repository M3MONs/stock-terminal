from __future__ import annotations

import keyring
import keyring.errors

_SERVICE = "stock-terminal"


def get_secret(name: str) -> str:
    return keyring.get_password(_SERVICE, name) or ""


def set_secret(name: str, value: str) -> None:
    if value:
        keyring.set_password(_SERVICE, name, value)
    else:
        try:
            keyring.delete_password(_SERVICE, name)
        except keyring.errors.PasswordDeleteError:
            pass
