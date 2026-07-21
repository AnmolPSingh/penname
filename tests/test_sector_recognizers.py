"""Penname's differentiation: sector-specific detection for donor documents.

Donation amounts, wealth/capacity ratings, fund/campaign/appeal codes, and
constituent IDs — the entities generic PII detection misses.
"""

import pytest

from penname.core.engine import PennameSession
from penname.core.replace.generator import PenNameGenerator


@pytest.fixture(scope="module")
def session() -> PennameSession:
    return PennameSession()


def _types_in(session: PennameSession, text: str) -> set[str]:
    result = session.pseudonymize(text)
    return {e.entity_type for e in result.mapping.entries}


def _entry_for(session: PennameSession, text: str, original: str):
    result = session.pseudonymize(text)
    return next(e for e in result.mapping.entries if e.original == original), result


def test_detects_constituent_id(session: PennameSession) -> None:
    text = "Please pull the record for constituent C-10041 before the call."
    entry, result = _entry_for(session, text, "C-10041")
    assert entry.entity_type == "CONSTITUENT_ID"
    assert "C-10041" not in result.text
    assert session.reverse(result.text, result.mapping) == text


def test_detects_fund_code(session: PennameSession) -> None:
    text = "Apply this gift to the FY25-CLEANWATER appeal, not the general fund."
    entry, result = _entry_for(session, text, "FY25-CLEANWATER")
    assert entry.entity_type == "FUND_CODE"
    assert session.reverse(result.text, result.mapping) == text


def test_detects_donation_amount(session: PennameSession) -> None:
    text = "Margaret's pledge of $25,000 arrived last week."
    assert "DONATION_AMOUNT" in _types_in(session, text)


def test_detects_wealth_capacity_rating(session: PennameSession) -> None:
    text = "Wealth screening puts her giving capacity at $50K-$100K this year."
    assert "WEALTH_RATING" in _types_in(session, text)


def test_sector_round_trip_over_mixed_document(session: PennameSession) -> None:
    text = (
        "Constituent C-10041 (capacity rating $50K-$100K) made a $25,000 gift to "
        "the FY25-CLEANWATER appeal. Follow up about a planned bequest."
    )
    result = session.pseudonymize(text)
    assert session.reverse(result.text, result.mapping) == text
    types = {e.entity_type for e in result.mapping.entries}
    assert {"CONSTITUENT_ID", "FUND_CODE", "DONATION_AMOUNT", "WEALTH_RATING"} <= types


# -- format-preserving pen names --------------------------------------------

def test_amount_pen_name_stays_a_currency_amount() -> None:
    gen = PenNameGenerator(seed=1)
    pen = gen.pen_name_for("DONATION_AMOUNT", "$25,000", avoid_text="")
    assert pen.startswith("$")
    assert pen != "$25,000"
    digits = int(pen.lstrip("$").replace(",", ""))
    # magnitude preserved: within an order of magnitude of 25,000
    assert 2_500 <= digits <= 250_000


def test_constituent_id_pen_name_keeps_its_shape() -> None:
    gen = PenNameGenerator(seed=1)
    pen = gen.pen_name_for("CONSTITUENT_ID", "C-10041", avoid_text="")
    assert pen != "C-10041"
    assert len(pen) == len("C-10041")
    assert pen[1] == "-" and pen[2:].isdigit()


def test_wealth_rating_pen_name_keeps_currency_units() -> None:
    gen = PenNameGenerator(seed=1)
    pen = gen.pen_name_for("WEALTH_RATING", "$50K-$100K", avoid_text="")
    assert pen != "$50K-$100K"
    # $ and K magnitude units preserved; only the digits changed
    assert pen.count("$") == 2 and pen.count("K") == 2
    assert "-" in pen


def test_fund_code_pen_name_keeps_separators() -> None:
    gen = PenNameGenerator(seed=1)
    pen = gen.pen_name_for("FUND_CODE", "FY25-CLEANWATER", avoid_text="")
    assert pen != "FY25-CLEANWATER"
    assert "-" in pen
    assert len(pen) == len("FY25-CLEANWATER")
