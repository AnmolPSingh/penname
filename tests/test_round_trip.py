"""Round-trip integrity: reverse(pseudonymize(text)) == text, byte-identical.

This is the product. It runs in CI on every commit and gates everything else.
"""

from pathlib import Path

import pytest

from penname.core.engine import PennameSession

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURES = sorted(FIXTURE_DIR.glob("*.txt"))


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.name)
def test_round_trip_byte_identity(path: Path) -> None:
    original = path.read_bytes().decode("utf-8")
    session = PennameSession()

    result = session.pseudonymize(original)
    restored = session.reverse(result.text, result.mapping)

    assert restored.encode("utf-8") == original.encode("utf-8")


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.name)
def test_detected_values_are_replaced(path: Path) -> None:
    """Every value that made it into the mapping is absent from the output text."""
    original = path.read_bytes().decode("utf-8")
    session = PennameSession()

    result = session.pseudonymize(original)

    assert result.mapping.entries, f"expected detections in {path.name}"
    for entry in result.mapping.entries:
        assert entry.pen_name != entry.original


def test_pseudonymized_text_differs_from_original() -> None:
    original = (FIXTURE_DIR / "donor_letter_1.txt").read_bytes().decode("utf-8")
    session = PennameSession()

    result = session.pseudonymize(original)

    assert result.text != original


def test_reverse_handles_arbitrary_llm_style_text() -> None:
    """Reversal input is a pasted LLM response, not the pseudonymized file."""
    original = (FIXTURE_DIR / "donor_letter_1.txt").read_bytes().decode("utf-8")
    session = PennameSession()
    result = session.pseudonymize(original)

    # Simulate an LLM response that quotes some pen names in new prose.
    quoted = [e.pen_name for e in result.mapping.entries[:3]]
    response = "Here is a draft:\n\n" + "\n".join(
        f"- Mention {pen} in the second paragraph." for pen in quoted
    )

    restored = session.reverse(response, result.mapping)

    originals = {e.pen_name: e.original for e in result.mapping.entries}
    for pen in quoted:
        assert originals[pen] in restored
        assert pen not in restored


def test_round_trip_preserves_crlf_and_unicode() -> None:
    original = "Dear Ms. Renée Åkesson,\r\nYour gift of $1,000 arrived May 1, 2025.\r\nThank you — merci.\r\n"
    session = PennameSession()

    result = session.pseudonymize(original)
    restored = session.reverse(result.text, result.mapping)

    assert restored.encode("utf-8") == original.encode("utf-8")


def test_empty_and_pii_free_text_pass_through() -> None:
    session = PennameSession()
    for text in ("", "   \n\n", "The quarterly newsletter is ready for layout review."):
        result = session.pseudonymize(text)
        assert session.reverse(result.text, result.mapping) == text
