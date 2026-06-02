import keyring
import keyring.backend
import keyring.errors
import pytest
from typing import ClassVar

from security.keystore import get_secret, set_secret


class _MemoryKeyring(keyring.backend.KeyringBackend):
    """In-memory backend — no OS keychain touched during tests."""

    priority: ClassVar[float] = 10.0

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        key = (service, username)
        if key not in self._store:
            raise keyring.errors.PasswordDeleteError("not found")
        del self._store[key]


@pytest.fixture(autouse=True)
def _memory_keyring():
    backend = _MemoryKeyring()
    keyring.set_keyring(backend)
    yield
    keyring.set_keyring(keyring.get_keyring().__class__())


def test_get_secret_returns_empty_when_not_set():
    assert get_secret("nonexistent") == ""


def test_set_and_get_secret():
    set_secret("gemini_api_key", "my-secret-key")
    assert get_secret("gemini_api_key") == "my-secret-key"


def test_set_secret_empty_deletes():
    set_secret("gemini_api_key", "some-key")
    set_secret("gemini_api_key", "")
    assert get_secret("gemini_api_key") == ""


def test_set_secret_empty_on_missing_is_noop():
    set_secret("gemini_api_key", "")  # should not raise
    assert get_secret("gemini_api_key") == ""


def test_set_secret_overwrites():
    set_secret("gemini_api_key", "first")
    set_secret("gemini_api_key", "second")
    assert get_secret("gemini_api_key") == "second"
