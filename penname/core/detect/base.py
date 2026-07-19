"""Detector interface. Presidio+spaCy implements it today; GLiNER slots in later."""

from __future__ import annotations

from typing import Protocol

from penname.core.types import Span


class EntityDetector(Protocol):
    def detect(self, text: str) -> list[Span]: ...
