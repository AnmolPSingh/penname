"""Builds the default detector: Presidio+spaCy, plus GLiNER when available.

GLiNER is optional. When it (and its bundled model) are present, detection is
the union of both — higher recall. When it is not, the app falls back to
Presidio+spaCy so it always works. Loading GLiNER never reaches the network.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from penname.core.detect.base import EntityDetector

logger = logging.getLogger("penname.detect")


def _try_load_gliner() -> EntityDetector | None:
    """Return a GlinerDetector if GLiNER and a local model are available;
    otherwise None. Never raises, never downloads — any failure (GLiNER not
    installed, its deps missing, no local model, a corrupt model) falls back to
    Presidio+spaCy so the app always works."""
    try:
        from penname.core.detect.gliner_detector import GlinerDetector
        from penname.core.detect.gliner_model import resolve_model_path

        model_path = resolve_model_path()
        if model_path is None:
            logger.info("GLiNER model not found locally; using Presidio+spaCy only.")
            return None
        return GlinerDetector(model_path)
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all for graceful fallback
        logger.info("GLiNER unavailable (%s); using Presidio+spaCy only.", exc)
        return None


@lru_cache(maxsize=1)
def get_default_detector() -> EntityDetector:
    """The detector the engine uses by default. Cached: models load once."""
    from penname.core.detect.composite_detector import CompositeDetector
    from penname.core.detect.presidio_detector import get_default_detector as _presidio

    presidio = _presidio()
    gliner = _try_load_gliner()
    # GLiNER first so its scores are considered before Presidio's on overlap.
    detectors = [d for d in (gliner, presidio) if d is not None]
    return CompositeDetector(detectors)
