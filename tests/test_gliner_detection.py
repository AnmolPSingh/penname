"""GLiNER integration: composite merge, graceful fallback, and (when the model
is installed) real detection.

GLiNER cannot be installed on this x86_64-macOS sandbox (onnxruntime has no
Intel-Mac wheel), so the real-model test skips when GLiNER is absent. The merge
and fallback logic — the parts that could actually break the app — are tested
with lightweight stubs and run everywhere.
"""

from __future__ import annotations

import importlib.util

import pytest

from penname.core.detect.composite_detector import CompositeDetector
from penname.core.engine import PennameSession
from penname.core.types import Span

GLINER_INSTALLED = importlib.util.find_spec("gliner") is not None


class _StubDetector:
    def __init__(self, spans: list[Span]):
        self._spans = spans

    def detect(self, text: str) -> list[Span]:
        return list(self._spans)


# -- composite merge --------------------------------------------------------

def test_composite_unions_spans_from_all_detectors() -> None:
    a = _StubDetector([Span(0, 3, "PERSON", 0.9, "Bob")])
    b = _StubDetector([Span(8, 12, "ORGANIZATION", 0.8, "ACME")])
    composite = CompositeDetector([a, b])

    spans = composite.detect("Bob at ACME")
    types = {s.entity_type for s in spans}
    assert types == {"PERSON", "ORGANIZATION"}


def test_composite_requires_at_least_one_detector() -> None:
    with pytest.raises(ValueError):
        CompositeDetector([])


def test_gliner_only_entity_gets_pseudonymized_via_composite() -> None:
    """A value only the GLiNER-like detector finds is still replaced and
    reverses cleanly — proving the merged spans flow through the engine."""
    text = "Meet Dana Fielding at the Harbor Trust."
    presidio_like = _StubDetector([])  # misses everything
    gliner_like = _StubDetector(
        [
            Span(5, 18, "PERSON", 0.95, "Dana Fielding"),
            Span(26, 38, "ORGANIZATION", 0.9, "Harbor Trust"),
        ]
    )
    session = PennameSession(detector=CompositeDetector([gliner_like, presidio_like]))

    result = session.pseudonymize(text)
    assert "Dana Fielding" not in result.text
    assert "Harbor Trust" not in result.text
    assert session.reverse(result.text, result.mapping) == text
    assert {e.entity_type for e in result.mapping.entries} == {"PERSON", "ORGANIZATION"}


def test_composite_overlap_resolved_by_engine_dedup() -> None:
    """When both detectors fire on overlapping spans, select_spans keeps the
    higher-scoring one, so the round trip still holds."""
    text = "Gift from Margaret Wilson."
    d1 = _StubDetector([Span(10, 18, "PERSON", 0.6, "Margaret")])
    d2 = _StubDetector([Span(10, 25, "PERSON", 0.95, "Margaret Wilson")])
    session = PennameSession(detector=CompositeDetector([d1, d2]))

    result = session.pseudonymize(text)
    assert session.reverse(result.text, result.mapping) == text
    assert "Margaret Wilson" not in result.text


# -- graceful fallback ------------------------------------------------------

def test_organization_gets_a_company_pen_name() -> None:
    from penname.core.replace.generator import PenNameGenerator

    pen = PenNameGenerator(seed=1).pen_name_for("ORGANIZATION", "Harbor Trust", "")
    assert pen and pen != "Harbor Trust"


def test_factory_falls_back_without_gliner(monkeypatch) -> None:
    """When GLiNER can't load, the factory still returns a working detector."""
    import penname.core.detect.factory as factory

    factory.get_default_detector.cache_clear()
    monkeypatch.setattr(factory, "_try_load_gliner", lambda: None)

    detector = factory.get_default_detector()
    # It detects via Presidio+spaCy — a plain name is still found.
    spans = detector.detect("Please thank Margaret Wilson for the gift.")
    assert any(s.text == "Margaret Wilson" for s in spans)
    factory.get_default_detector.cache_clear()


# -- real model (skips when GLiNER isn't installed) -------------------------

@pytest.mark.skipif(not GLINER_INSTALLED, reason="GLiNER not installed on this platform")
def test_real_gliner_detects_person_offline() -> None:
    from penname.core.detect.gliner_detector import GlinerDetector
    from penname.core.detect.gliner_model import resolve_model_path

    model_path = resolve_model_path()
    if model_path is None:
        pytest.skip("GLiNER model not fetched locally")

    detector = GlinerDetector(model_path)
    spans = detector.detect("Please thank Margaret Wilson for the gift.")
    assert any(s.entity_type == "PERSON" for s in spans)
