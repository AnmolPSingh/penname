"""Mapping key storage in the OS keychain (macOS Keychain / Windows Credential Manager)."""

from __future__ import annotations

import base64
import secrets

import keyring

SERVICE = "Penname"
ACCOUNT = "mapping-key"
_KEY_LEN = 32  # AES-256


class KeychainError(Exception):
    pass


def _refuse_insecure_backend() -> None:
    """The mapping key must live in a real OS keychain. keyring auto-selects
    its backend from whatever is installed; refuse plaintext fallbacks."""
    backend = keyring.get_keyring()
    module = type(backend).__module__ or ""
    name = type(backend).__name__
    if module.startswith("keyrings.alt") or "Plaintext" in name or "fail" in module:
        raise KeychainError(
            "no secure keychain is available on this computer, so Penname "
            "cannot store its encryption key safely. Mapping files were not "
            "created."
        )


def get_or_create_key() -> bytes:
    _refuse_insecure_backend()
    stored = keyring.get_password(SERVICE, ACCOUNT)
    if stored is not None:
        key = base64.b64decode(stored)
        if len(key) != _KEY_LEN:
            raise KeychainError("the stored Penname key is malformed")
        return key
    key = secrets.token_bytes(_KEY_LEN)
    keyring.set_password(SERVICE, ACCOUNT, base64.b64encode(key).decode("ascii"))
    return key
