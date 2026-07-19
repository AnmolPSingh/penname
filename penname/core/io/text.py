"""Bytes-faithful TXT/MD reading and writing."""

from __future__ import annotations

from pathlib import Path


def read_document(path: str | Path) -> str:
    return Path(path).read_bytes().decode("utf-8")


def write_document(path: str | Path, text: str) -> None:
    Path(path).write_bytes(text.encode("utf-8"))
