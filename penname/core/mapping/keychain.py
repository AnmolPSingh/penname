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


def get_or_create_key() -> bytes:
    stored = keyring.get_password(SERVICE, ACCOUNT)
    if stored is not None:
        key = base64.b64decode(stored)
        if len(key) != _KEY_LEN:
            raise KeychainError("the stored Penname key is malformed")
        return key
    key = secrets.token_bytes(_KEY_LEN)
    keyring.set_password(SERVICE, ACCOUNT, base64.b64encode(key).decode("ascii"))
    return key
