import os

import keyring
import keyring.backend
import pytest

# GUI tests run headless everywhere (local runs and CI).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from penname.gui.qt_env import ensure_qt_plugins_reachable
except ImportError:  # PySide6 not installed (core-only environments)
    pass
else:
    ensure_qt_plugins_reachable()


class _TestKeyring(keyring.backend.KeyringBackend):
    """An in-process key store, used only by the test suite.

    Two reasons this exists:

    1. CI runners have no OS keychain, so keyring falls back to its `fail`
       backend and `_refuse_insecure_backend()` rightly raises. That refusal is
       correct product behaviour and must not be softened, so the tests supply
       a key store rather than the guard standing down.
    2. Without it, running the suite on a developer's machine writes a real
       Penname key into their login keychain. Tests should not touch it.

    Deliberately not named "Plaintext" and never shipped in the wheel: the
    guard in penname.core.mapping.keychain still rejects every insecure
    backend a real user could end up with.
    """

    priority = 1

    def __init__(self) -> None:
        super().__init__()
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._store.pop((service, username), None)


@pytest.fixture(autouse=True, scope="session")
def _isolated_keychain():
    previous = keyring.get_keyring()
    keyring.set_keyring(_TestKeyring())
    yield
    keyring.set_keyring(previous)
