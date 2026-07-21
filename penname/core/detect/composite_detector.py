"""Run several detectors and merge their spans.

GLiNER catches names/organizations spaCy misses; Presidio's pattern and sector
recognizers own the structured values (emails, phones, amounts, IDs). The union
of their spans is deduplicated downstream by the engine's ``select_spans``
(higher score / longer match wins on overlap), so this class only concatenates.
"""

from __future__ import annotations

from penname.core.detect.base import EntityDetector
from penname.core.types import Span


class CompositeDetector:
    def __init__(self, detectors: list[EntityDetector]):
        if not detectors:
            raise ValueError("a composite detector needs at least one detector")
        self._detectors = detectors

    def detect(self, text: str) -> list[Span]:
        spans: list[Span] = []
        for detector in self._detectors:
            spans.extend(detector.detect(text))
        return spans
