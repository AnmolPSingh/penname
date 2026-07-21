"""Custom Presidio recognizers for the nonprofit/philanthropy sector.

These are Penname's differentiation: donation amounts, wealth/capacity
ratings, fund/campaign/appeal codes, and constituent IDs — the entities
generic PII detection misses. Planned-giving and bequest terminology is used
as context that raises confidence in nearby sector values (those terms are
generic vocabulary, so they are not themselves replaced).

Patterns are intentionally conservative; the human review step is the safety
net for anything they miss or over-match.
"""

from __future__ import annotations

# Sector context words. Presidio boosts a pattern's score when these appear
# nearby, which lets us keep the raw patterns tight without missing real hits.
_GIVING_CONTEXT = [
    "gift",
    "gave",
    "donation",
    "donor",
    "pledge",
    "contribution",
    "bequest",
    "legacy",
    "planned giving",
    "estate",
    "annual fund",
]
_WEALTH_CONTEXT = ["capacity", "wealth", "rating", "screening", "score", "affinity"]
_FUND_CONTEXT = ["fund", "campaign", "appeal", "code", "designation", "restricted"]
_ID_CONTEXT = ["constituent", "donor", "record", "account", "id", "number"]


def build_sector_recognizers() -> list:
    """Return the sector PatternRecognizers. Imported lazily by the detector."""
    from presidio_analyzer import Pattern, PatternRecognizer

    donation_amount = PatternRecognizer(
        supported_entity="DONATION_AMOUNT",
        name="donation_amount_recognizer",
        patterns=[
            # $25,000  /  £1,000.00  /  €500
            Pattern(
                "currency_amount",
                r"[$£€]\s?\d{1,3}(?:,\d{3})+(?:\.\d{2})?|[$£€]\s?\d+(?:\.\d{2})?",
                0.6,
            ),
        ],
        context=_GIVING_CONTEXT,
    )

    wealth_rating = PatternRecognizer(
        supported_entity="WEALTH_RATING",
        name="wealth_rating_recognizer",
        patterns=[
            # $50K-$100K  /  $1M+  /  $250K
            Pattern(
                "capacity_band",
                r"\$\d+(?:\.\d+)?[KMB]\+?(?:\s?[-–]\s?\$\d+(?:\.\d+)?[KMB]\+?)?",
                0.5,
            ),
            # explicit "capacity rating: A1" style tokens
            Pattern("rating_token", r"\b[Tt]ier\s?[A-E]\b", 0.35),
        ],
        context=_WEALTH_CONTEXT,
    )

    fund_code = PatternRecognizer(
        supported_entity="FUND_CODE",
        name="fund_code_recognizer",
        patterns=[
            # FY25-CLEANWATER  /  AF-2025-SPRING  /  CAP2024-BLDG
            Pattern(
                "fund_code",
                r"\b[A-Z]{2,}\d{0,4}(?:[-][A-Z0-9]{2,}){1,3}\b",
                0.5,
            ),
        ],
        context=_FUND_CONTEXT,
    )

    constituent_id = PatternRecognizer(
        supported_entity="CONSTITUENT_ID",
        name="constituent_id_recognizer",
        patterns=[
            # C-10041  /  CONS-000123  /  ID#4471123
            Pattern("prefixed_id", r"\b(?:C|CONS|ID|REC|DP)[-#]\d{4,10}\b", 0.5),
        ],
        context=_ID_CONTEXT,
    )

    return [donation_amount, wealth_rating, fund_code, constituent_id]


SECTOR_ENTITIES = (
    "DONATION_AMOUNT",
    "WEALTH_RATING",
    "FUND_CODE",
    "CONSTITUENT_ID",
)
