"""Encrypted persistence for mappings. Plaintext exists in memory only."""

from __future__ import annotations

import json
from pathlib import Path

from penname.core.mapping import crypto
from penname.core.types import Mapping


class MappingStore:
    def __init__(self, key: bytes | None = None):
        self._key = key

    def _resolve_key(self) -> bytes:
        if self._key is None:
            from penname.core.mapping.keychain import get_or_create_key

            self._key = get_or_create_key()
        return self._key

    def save(self, mapping: Mapping, path: str | Path) -> None:
        plaintext = json.dumps(mapping.to_dict(), ensure_ascii=False).encode("utf-8")
        Path(path).write_bytes(crypto.encrypt(self._resolve_key(), plaintext))

    def load(self, path: str | Path) -> Mapping:
        plaintext = crypto.decrypt(self._resolve_key(), Path(path).read_bytes())
        return Mapping.from_dict(json.loads(plaintext.decode("utf-8")))
