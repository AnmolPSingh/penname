"""Public engine API. GUI, CLI, and MCP all call this and nothing lower."""

from __future__ import annotations

import re

from penname.core.detect.base import EntityDetector
from penname.core.replace.applier import apply_replacements, reverse_text, select_spans
from penname.core.replace.generator import PenNameGenerator
from penname.core.types import Mapping, MappingEntry, PseudonymizeResult, Span

_MAX_VERIFY_ATTEMPTS = 5


class RoundTripError(Exception):
    """Raised when a verified, reversible pseudonymization cannot be produced."""


class PennameSession:
    """Holds detection and pen-name state so values stay consistent across
    documents opened in one session (same real value -> same pen name)."""

    def __init__(
        self,
        detector: EntityDetector | None = None,
        generator: PenNameGenerator | None = None,
    ):
        if detector is None:
            from penname.core.detect.presidio_detector import get_default_detector

            detector = get_default_detector()
        self._detector = detector
        self._generator = generator or PenNameGenerator()
        self._ignored: set[tuple[str, str]] = set()
        self._custom_values: dict[str, str] = {}  # value -> entity_type

    def ignore_value(self, entity_type: str, original: str) -> None:
        """Review action: keep this value's real text (no pen name)."""
        self._ignored.add((entity_type, original))

    def unignore_value(self, entity_type: str, original: str) -> None:
        self._ignored.discard((entity_type, original))

    def set_pen_name(self, entity_type: str, original: str, pen_name: str) -> None:
        """Review action: use this exact pen name for a value."""
        if not pen_name.strip():
            raise ValueError("a pen name cannot be empty")
        if pen_name == original:
            raise ValueError("a pen name must be different from the real value")
        self._generator.pin_pen_name(entity_type, original, pen_name)

    def always_replace(self, value: str, entity_type: str = "CUSTOM") -> None:
        """Review action: give this exact text a pen name wherever it appears."""
        if not value.strip():
            raise ValueError("cannot add an empty value")
        self._custom_values[value] = entity_type

    def _collect_spans(self, text: str) -> list[Span]:
        spans = self._detector.detect(text) if text.strip() else []
        for value, entity_type in self._custom_values.items():
            spans.extend(
                Span(m.start(), m.end(), entity_type, 1.0, value)
                for m in re.finditer(re.escape(value), text)
            )
        spans = [s for s in spans if (s.entity_type, s.text) not in self._ignored]
        return select_spans(spans)

    def pseudonymize(self, text: str) -> PseudonymizeResult:
        spans = self._collect_spans(text)
        if not spans:
            return PseudonymizeResult(text=text, mapping=Mapping(entries=()))

        for _ in range(_MAX_VERIFY_ATTEMPTS):
            replacements = [
                (span, self._generator.pen_name_for(span.entity_type, span.text, text))
                for span in spans
            ]
            entries = tuple(
                {
                    (s.entity_type, s.text): MappingEntry(
                        original=s.text,
                        pen_name=pen,
                        entity_type=s.entity_type,
                        score=s.score,
                    )
                    for s, pen in replacements
                }.values()
            )
            mapping = Mapping(entries=entries)
            new_text = apply_replacements(text, replacements)

            # Self-verification: the round trip must hold before we return.
            if reverse_text(new_text, mapping) == text:
                return PseudonymizeResult(text=new_text, mapping=mapping)

            # A pen name (possibly cached from an earlier document) collides
            # with this text. Regenerate the pen names involved and retry.
            for span in spans:
                self._generator.forget(span.entity_type, span.text)

        raise RoundTripError(
            "could not produce a reversible pseudonymization for this document"
        )

    def reverse(self, text: str, mapping: Mapping) -> str:
        return reverse_text(text, mapping)
