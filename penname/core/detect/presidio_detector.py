"""Presidio analyzer backed by the bundled spaCy model. Fully offline."""

from __future__ import annotations

from functools import lru_cache

from penname.core.types import Span

DEFAULT_MIN_SCORE = 0.4

_NLP_CONFIGURATION = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
}


class PresidioDetector:
    def __init__(self, min_score: float = DEFAULT_MIN_SCORE):
        # Imported lazily so the rest of core stays importable without the model.
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        from penname.core.detect.sector_recognizers import build_sector_recognizers

        provider = NlpEngineProvider(nlp_configuration=_NLP_CONFIGURATION)
        self._analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
        for recognizer in build_sector_recognizers():
            self._analyzer.registry.add_recognizer(recognizer)
        self._min_score = min_score

    def detect(self, text: str) -> list[Span]:
        results = self._analyzer.analyze(text=text, language="en")
        return [
            Span(
                start=r.start,
                end=r.end,
                entity_type=r.entity_type,
                score=r.score,
                text=text[r.start : r.end],
            )
            for r in results
            if r.score >= self._min_score
        ]


@lru_cache(maxsize=1)
def get_default_detector() -> PresidioDetector:
    """The analyzer loads a large model; share one instance per process."""
    return PresidioDetector()
