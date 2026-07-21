"""Consistent, format-aware pen-name generation.

One generator per session: the same real value always receives the same pen
name, dates are shifted (not blanked), and phone numbers keep their shape.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from faker import Faker

# Formats tried when shifting a detected date. Order matters: most specific first.
_DATE_FORMATS = (
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%Y-%m-%d",
    "%B %Y",
    "%Y",
)

_MAX_CANDIDATE_ATTEMPTS = 50


class PenNameError(Exception):
    """Raised when no usable pen name can be generated for a value."""


class PenNameGenerator:
    def __init__(self, seed: int | None = None):
        self._faker = Faker()
        if seed is not None:
            self._faker.seed_instance(seed)
        self._cache: dict[tuple[str, str], str] = {}
        self._used: set[str] = set()
        self._pinned: set[tuple[str, str]] = set()
        # Dates shift by one session-stable delta so intervals stay plausible.
        sign = 1 if self._faker.random_int(0, 1) else -1
        self._date_delta = timedelta(days=sign * self._faker.random_int(30, 400))

    def pen_name_for(self, entity_type: str, original: str, avoid_text: str) -> str:
        key = (entity_type, original)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        for _ in range(_MAX_CANDIDATE_ATTEMPTS):
            candidate = self._generate(entity_type, original)
            if (
                candidate
                and candidate != original
                and candidate not in self._used
                and candidate not in avoid_text
            ):
                self._cache[key] = candidate
                self._used.add(candidate)
                return candidate
        raise PenNameError(f"could not generate a pen name for a {entity_type} value")

    def forget(self, entity_type: str, original: str) -> None:
        """Drop a cached pen name so the next request regenerates it.
        Pinned (user-chosen) pen names are never forgotten."""
        key = (entity_type, original)
        if key in self._pinned:
            return
        pen = self._cache.pop(key, None)
        if pen is not None:
            self._used.discard(pen)

    def pin_pen_name(self, entity_type: str, original: str, pen_name: str) -> None:
        """Set a user-chosen pen name that generation and retries must respect."""
        key = (entity_type, original)
        previous = self._cache.get(key)
        if previous is not None:
            self._used.discard(previous)
        self._cache[key] = pen_name
        self._used.add(pen_name)
        self._pinned.add(key)

    def _generate(self, entity_type: str, original: str) -> str:
        f = self._faker
        if entity_type == "PERSON":
            return f.name()
        if entity_type == "ORGANIZATION":
            return f.company()
        if entity_type == "EMAIL_ADDRESS":
            return f.email()
        if entity_type == "PHONE_NUMBER":
            return self._reshape_digits(original)
        if entity_type == "DATE_TIME":
            shifted = self._shift_date(original)
            return shifted if shifted is not None else f.date(pattern="%B %d, %Y")
        if entity_type == "LOCATION":
            return f.city()
        if entity_type == "URL":
            return f.url()
        if entity_type == "US_SSN":
            return f.ssn()
        if entity_type == "CREDIT_CARD":
            return f.credit_card_number()
        if entity_type == "IBAN_CODE":
            return f.iban()
        if entity_type == "IP_ADDRESS":
            return f.ipv4()
        if entity_type == "NRP":
            return f.country()
        if entity_type == "DONATION_AMOUNT":
            return self._reshape_amount(original)
        if entity_type == "WEALTH_RATING":
            return self._reshape_rating(original)
        if entity_type in ("CONSTITUENT_ID", "FUND_CODE"):
            return self._reshape_alphanumeric(original)
        return f.word().capitalize()

    def _reshape_digits(self, original: str) -> str:
        """Replace every digit, preserving punctuation and grouping."""
        return re.sub(r"\d", lambda _: str(self._faker.random_digit()), original)

    def _reshape_alphanumeric(self, original: str) -> str:
        """Replace letters with letters and digits with digits, keeping length,
        separators, and case pattern (e.g. C-10041 -> C-48822)."""

        def swap(match: re.Match) -> str:
            char = match.group(0)
            if char.isdigit():
                return str(self._faker.random_digit())
            return (
                self._faker.random_uppercase_letter()
                if char.isupper()
                else self._faker.random_lowercase_letter()
            )

        return re.sub(r"[A-Za-z0-9]", swap, original)

    def _reshape_rating(self, original: str) -> str:
        """Capacity bands like "$50K-$100K" keep their $ and K/M/B units, only
        the digits change; letter-only ratings (e.g. "Tier A") reshape letters."""
        if any(c.isdigit() for c in original):
            return self._reshape_digits(original)
        return self._reshape_alphanumeric(original)

    def _reshape_amount(self, original: str) -> str:
        """Replace a currency amount with a different one of similar magnitude,
        preserving the symbol and thousands grouping."""
        match = re.search(r"\d[\d,]*(?:\.\d+)?", original)
        if match is None:
            return self._reshape_digits(original)
        raw = match.group(0)
        has_grouping = "," in raw
        has_cents = "." in raw
        value = float(raw.replace(",", ""))
        factor = self._faker.random_int(60, 175) / 100  # 0.60x .. 1.75x
        new_value = max(1.0, round(value * factor))
        if has_cents:
            rendered = f"{new_value:,.2f}" if has_grouping else f"{new_value:.2f}"
        else:
            rendered = f"{int(new_value):,}" if has_grouping else f"{int(new_value)}"
        return original[: match.start()] + rendered + original[match.end() :]

    def _shift_date(self, original: str) -> str | None:
        for fmt in _DATE_FORMATS:
            try:
                parsed = datetime.strptime(original, fmt)
            except ValueError:
                continue
            shifted = parsed + self._date_delta
            if shifted.strftime(fmt) == original:
                # Coarse formats (e.g. a bare year) can survive a small shift;
                # push a full year further so the rendering actually changes.
                sign = 1 if self._date_delta.days >= 0 else -1
                shifted += timedelta(days=sign * 366)
            out = shifted.strftime(fmt)
            if parsed.strftime(fmt) != original:
                # The original used unpadded day/month; strip the padding zeros.
                out = re.sub(r"(?<!\d)0(\d)", r"\1", out)
            return out
        return None
