"""Document furniture must not be mistaken for donor data.

A real proposal is full of Title Case headings ("Reach", "In Depth", "Real
Value", "Next Steps"). spaCy reads those as names, organisations and places,
and Presidio reports every one at a flat 0.85 confidence. Before this filter,
the review screen buried the two real donor names under a dozen headings, all
labelled "Very sure", and the user had to untick most of the list by hand.
"""

from penname.core.detect.noise_filter import filter_spans, rescore
from penname.core.labels import certainty_label
from penname.core.types import Span

PROPOSAL = """Proposal for Riverside Community Foundation

Prepared by Margaret Wilson, Director of Development.

Reach
We will extend our reach across three counties in the first year.

In Depth
An in depth analysis of the current programme follows.

Real Value
The real value of this partnership is measured over five years.

Next Steps
The Board will review Deliverables in Q3.
"""


def _span(value: str, entity_type: str, score: float = 0.85) -> Span:
    start = PROPOSAL.index(value)
    return Span(start, start + len(value), entity_type, score, value)


def test_heading_words_are_dropped() -> None:
    """Standalone Title Case headings are structure, not data."""
    spans = [
        _span("Reach", "PERSON"),
        _span("In Depth", "PERSON"),
        _span("Real Value", "ORGANIZATION"),
        _span("Next Steps", "ORGANIZATION"),
    ]
    assert filter_spans(PROPOSAL, spans) == []


def test_words_used_in_lowercase_elsewhere_are_dropped() -> None:
    """If the document also writes it in lowercase, it is a common word.

    "Reach" is a heading but "our reach" appears in the body; that mismatch is
    the strongest local evidence that it is not somebody's name.
    """
    kept = filter_spans(PROPOSAL, [_span("Reach", "PERSON")])
    assert kept == []


def test_generic_business_words_are_dropped() -> None:
    spans = [_span("Deliverables", "PERSON"), _span("The Board", "ORGANIZATION")]
    assert filter_spans(PROPOSAL, spans) == []


def test_real_names_and_organisations_survive() -> None:
    """The filter must not cost us the values that matter."""
    spans = [
        _span("Margaret Wilson", "PERSON"),
        _span("Riverside Community Foundation", "ORGANIZATION"),
    ]
    kept = {s.text for s in filter_spans(PROPOSAL, spans)}
    assert kept == {"Margaret Wilson", "Riverside Community Foundation"}


def test_pattern_backed_types_are_never_filtered() -> None:
    """Emails, phones and sector codes come from patterns, not guesswork."""
    text = "Reach reach: a@b.org"
    spans = [
        Span(13, 20, "EMAIL_ADDRESS", 1.0, "a@b.org"),
        Span(0, 5, "PERSON", 0.85, "Reach"),
    ]
    kept = filter_spans(text, spans)
    assert [s.entity_type for s in kept] == ["EMAIL_ADDRESS"]


def test_vague_dates_are_dropped_but_real_ones_kept() -> None:
    text = "We met in the first year, then again on 12 March 2025."
    vague = Span(11, 25, "DATE_TIME", 0.85, "the first year")
    real = Span(40, 53, "DATE_TIME", 0.85, "12 March 2025")
    kept = [s.text for s in filter_spans(text, [vague, real])]
    assert kept == ["12 March 2025"]


def test_confidence_is_honest_about_guesswork() -> None:
    """"Very sure" must mean a pattern matched, not that a model guessed.

    Presidio hands back a flat 0.85 for every spaCy entity, so the old UI
    called each one "Very sure" whether it was a donor or a heading.
    """
    guess = Span(0, 5, "PERSON", 0.85, "Sarah")
    pattern = Span(0, 7, "EMAIL_ADDRESS", 1.0, "a@b.org")

    assert certainty_label(rescore(guess)) != "Very sure"
    assert certainty_label(rescore(pattern)) == "Very sure"


def test_multi_word_names_rank_above_single_words() -> None:
    single = rescore(Span(0, 5, "PERSON", 0.85, "Sarah"))
    full = rescore(Span(0, 15, "PERSON", 0.85, "Margaret Wilson"))
    assert full > single


def test_a_bare_name_in_a_spreadsheet_cell_survives() -> None:
    """Regression: every cell is a short unpunctuated line.

    An earlier version treated "a short line the span covers entirely" as a
    heading. That describes every cell in a CSV or XLSX export, so names in
    spreadsheets stopped being detected at all.
    """
    cell = "Priya Raghunathan"
    span = Span(0, len(cell), "PERSON", 1.0, cell)
    assert filter_spans(cell, [span]) != []


def test_a_signature_line_survives() -> None:
    letter = "Thank you for your support.\n\nMargaret Wilson\nDirector\n"
    start = letter.index("Margaret Wilson")
    span = Span(start, start + 15, "PERSON", 0.85, "Margaret Wilson")
    assert [s.text for s in filter_spans(letter, [span])] == ["Margaret Wilson"]
