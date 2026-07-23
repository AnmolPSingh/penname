"""Tell donor data apart from document furniture.

Presidio's spaCy recognizer reports every named entity at a flat 0.85, whatever
the model actually thought. In a donor letter that is tolerable. In a proposal
it is not: headings like "Reach", "In Depth", "Real Value" and "Next Steps" come
back as people, organisations and places, all labelled "Very sure", and the two
names that mattered end up buried in a list the user has to untick by hand.

Two signals separate the two:

1. The word is document furniture (see noise_words.txt).
2. The document itself writes the same words in lowercase somewhere else.
   "Reach" as a heading plus "our reach" in the body is strong local evidence
   that nobody is called Reach.

Position was tried as a third signal and removed: "a short line the span covers
entirely" describes a heading, but it equally describes every cell of a
spreadsheet and the signature line of a letter, so it cost real names.

None of this touches pattern-backed values. An email address is an email
address; only the language model's guesses are second-guessed here.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from penname.core.types import Span

#: Types that come from the language model guessing, rather than from a pattern.
SOFT_TYPES = frozenset(
    {"PERSON", "ORGANIZATION", "ORG", "LOCATION", "GPE", "NRP", "DATE_TIME"}
)

_WORDS_FILE = Path(__file__).with_name("noise_words.txt")
_MONTHS = (
    "january february march april may june july august september october "
    "november december jan feb mar apr jun jul aug sep sept oct nov dec"
).split()


@lru_cache(maxsize=1)
def noise_words() -> frozenset[str]:
    if not _WORDS_FILE.exists():  # pragma: no cover - packaging safety net
        return frozenset()
    lines = _WORDS_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip().lower()
        for line in lines
        if line.strip() and not line.startswith("#")
    )


def _normalise(value: str) -> str:
    """Fold to a comparable form: lowercase, collapsed spaces, no edge punctuation."""
    return re.sub(r"\s+", " ", value).strip(" \t\r\n.,;:!?\"'()[]").lower()


def _is_document_furniture(value: str) -> bool:
    normalised = _normalise(value)
    if normalised in noise_words():
        return True
    # "The Board" -> "board"; headings often carry a leading article.
    without_article = re.sub(r"^(the|a|an|our|your|their)\s+", "", normalised)
    return without_article in noise_words()


def _appears_lowercase_elsewhere(text: str, value: str) -> bool:
    """True when the document also writes these words in ordinary lowercase.

    A donor's name is capitalised every time it appears. A common word that
    happens to head a section is not.
    """
    normalised = _normalise(value)
    if not normalised:
        return False
    pattern = re.compile(
        r"(?<![A-Za-z])" + r"\s+".join(re.escape(w) for w in normalised.split()) + r"(?![A-Za-z])"
    )
    for match in pattern.finditer(text):
        if match.group(0).islower():
            return True
    return False


def _is_vague_date(span: Span) -> bool:
    """"the first year" and "five years" identify nobody. "12 March 2025" does."""
    if span.entity_type != "DATE_TIME":
        return False
    value = span.text.lower()
    if any(ch.isdigit() for ch in value):
        return False
    return not any(month in value.split() for month in _MONTHS)


def is_noise(text: str, span: Span) -> bool:
    """Whether this span is document structure rather than donor data."""
    if span.entity_type not in SOFT_TYPES:
        return False
    if _is_vague_date(span):
        return True
    if _is_document_furniture(span.text):
        return True
    return _appears_lowercase_elsewhere(text, span.text)


def filter_spans(text: str, spans: list[Span]) -> list[Span]:
    """Drop the spans that are document furniture, and re-score what remains."""
    return [
        span._replace(score=rescore(span))
        if hasattr(span, "_replace")
        else Span(span.start, span.end, span.entity_type, rescore(span), span.text)
        for span in spans
        if not is_noise(text, span)
    ]


def rescore(span: Span) -> float:
    """Replace Presidio's flat 0.85 with something the UI can honestly show.

    "Very sure" should mean a pattern matched: an email address, a phone number,
    a fund code. A language model's guess at a name is never more than "fairly
    sure", however confident Presidio claims to be, because it is exactly the
    guess that produced "Deliverables" as a person.
    """
    if span.entity_type not in SOFT_TYPES:
        return span.score
    words = len(span.text.split())
    if words >= 2:
        return min(span.score, 0.75)  # "Fairly sure"
    return min(span.score, 0.55)  # "Less sure, check this"
