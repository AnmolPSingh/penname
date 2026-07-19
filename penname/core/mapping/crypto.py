"""AES-256-GCM framing for mapping files (.pnmap)."""

from __future__ import annotations

import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"PNMAP"
VERSION = 1
_NONCE_LEN = 12


class MappingFileError(Exception):
    """Raised when a .pnmap file cannot be read (wrong key, corrupt, wrong format)."""


def encrypt(key: bytes, plaintext: bytes) -> bytes:
    nonce = secrets.token_bytes(_NONCE_LEN)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, MAGIC)
    return MAGIC + bytes([VERSION]) + nonce + ciphertext


def decrypt(key: bytes, blob: bytes) -> bytes:
    header_len = len(MAGIC) + 1 + _NONCE_LEN
    if len(blob) < header_len or not blob.startswith(MAGIC):
        raise MappingFileError("this file is not a Penname mapping file")
    version = blob[len(MAGIC)]
    if version != VERSION:
        raise MappingFileError(f"unsupported mapping file version: {version}")
    nonce = blob[len(MAGIC) + 1 : header_len]
    try:
        return AESGCM(key).decrypt(nonce, blob[header_len:], MAGIC)
    except Exception as exc:
        raise MappingFileError(
            "could not unlock this mapping file — wrong key or damaged file"
        ) from exc
