"""Engine support for the mandatory human-review step:
remove a value, choose a pen name, add a value detection missed."""

import pytest

from penname.core.engine import PennameSession, RoundTripError

TEXT = (
    "Margaret Wilson pledged $25,000. Contact Sarah Chen at "
    "s.chen@riversidecf.org. The Fund code is RW-2025-CLEAN."
)


def test_ignored_value_keeps_its_real_text() -> None:
    session = PennameSession()
    first = session.pseudonymize(TEXT)
    assert any(e.original == "Sarah Chen" for e in first.mapping.entries)

    session.ignore_value("PERSON", "Sarah Chen")
    result = session.pseudonymize(TEXT)

    assert "Sarah Chen" in result.text
    assert all(e.original != "Sarah Chen" for e in result.mapping.entries)
    assert session.reverse(result.text, result.mapping) == TEXT


def test_user_chosen_pen_name_is_used() -> None:
    session = PennameSession()
    session.set_pen_name("PERSON", "Margaret Wilson", "Dorothy Fields")

    result = session.pseudonymize(TEXT)

    assert "Dorothy Fields" in result.text
    assert session.reverse(result.text, result.mapping) == TEXT


def test_user_chosen_pen_name_must_be_usable() -> None:
    session = PennameSession()
    with pytest.raises(ValueError):
        session.set_pen_name("PERSON", "Margaret Wilson", "")
    with pytest.raises(ValueError):
        session.set_pen_name("PERSON", "Margaret Wilson", "Margaret Wilson")


def test_pen_name_colliding_with_kept_text_fails_loudly() -> None:
    """A chosen pen name that duplicates text remaining in the document cannot
    be reversed unambiguously; the engine must refuse rather than corrupt.
    (Here the user keeps "Sarah Chen" as real text AND picks it as a pen name.)"""
    session = PennameSession()
    session.ignore_value("PERSON", "Sarah Chen")
    session.set_pen_name("PERSON", "Margaret Wilson", "Sarah Chen")

    with pytest.raises(RoundTripError):
        session.pseudonymize(TEXT)


def test_added_custom_value_is_replaced_everywhere() -> None:
    session = PennameSession()
    session.always_replace("RW-2025-CLEAN", entity_type="FUND_CODE")

    result = session.pseudonymize(TEXT)

    assert "RW-2025-CLEAN" not in result.text
    assert any(e.original == "RW-2025-CLEAN" for e in result.mapping.entries)
    assert session.reverse(result.text, result.mapping) == TEXT
