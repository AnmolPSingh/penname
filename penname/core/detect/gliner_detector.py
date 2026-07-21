"""GLiNER NER backend — higher-recall detection for names, organizations, and
places that the spaCy pipeline misses.

Fully offline at runtime (non-negotiable rule 1): the model is loaded from a
local directory only, never downloaded. Fetch it once at build/dev time with
``python -m penname.core.detect.gliner_model``. If GLiNER or its model is not
present, this module is simply not used — the composite detector falls back to
Presidio+spaCy.
"""

from __future__ import annotations

import os

from penname.core.types import Span

# Default PII-tuned GLiNER model. Pinned by name; fetched at build time.
DEFAULT_MODEL = "urchade/gliner_multi_pii-v1"
DEFAULT_THRESHOLD = 0.5

# GLiNER prompt labels -> Penname entity types. We ask GLiNER only for the
# contextual entities it is strong at; Presidio patterns own emails, phones,
# amounts, IDs, and the sector entities.
_LABELS = {
    "person": "PERSON",
    "organization": "ORGANIZATION",
    "location": "LOCATION",
}


def _force_offline() -> None:
    """Guarantee no network access when the model loads."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


class GlinerDetector:
    def __init__(self, model_path: str, threshold: float = DEFAULT_THRESHOLD):
        _force_offline()
        from gliner import GLiNER

        # local_files_only guarantees the load never reaches the network.
        self._model = GLiNER.from_pretrained(model_path, local_files_only=True)
        self._threshold = threshold
        self._labels = list(_LABELS)

    def detect(self, text: str) -> list[Span]:
        if not text.strip():
            return []
        found = self._model.predict_entities(
            text, self._labels, threshold=self._threshold
        )
        spans: list[Span] = []
        for ent in found:
            entity_type = _LABELS.get(ent["label"].lower())
            if entity_type is None:
                continue
            spans.append(
                Span(
                    start=ent["start"],
                    end=ent["end"],
                    entity_type=entity_type,
                    score=float(ent.get("score", self._threshold)),
                    text=text[ent["start"] : ent["end"]],
                )
            )
        return spans
