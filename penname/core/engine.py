"""Public engine API. GUI, CLI, and MCP all call this and nothing lower."""

from __future__ import annotations

from penname.core.detect.base import EntityDetector
from penname.core.replace.applier import apply_replacements, reverse_text, select_spans
from penname.core.replace.generator import PenNameGenerator
from penname.core.types import Mapping, MappingEntry, PseudonymizeResult

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

    def pseudonymize(self, text: str) -> PseudonymizeResult:
        spans = select_spans(self._detector.detect(text)) if text.strip() else []
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
                        original=s.text, pen_name=pen, entity_type=s.entity_type
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
