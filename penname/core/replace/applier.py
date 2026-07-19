"""Span-safe replacement and reversal with explicit offset handling.

Replacements are applied end-to-start so earlier offsets never shift — this is
what keeps round trips byte-identical where naive pipelines fail. Reversal is a
single regex pass, so restored real values are never rescanned and clobbered.
"""

from __future__ import annotations

import re

from penname.core.types import Mapping, Span


def select_spans(spans: list[Span]) -> list[Span]:
    """Drop overlapping spans, preferring higher score then longer match."""
    ranked = sorted(spans, key=lambda s: (-s.score, s.start - s.end))
    kept: list[Span] = []
    for span in ranked:
        if all(span.end <= k.start or span.start >= k.end for k in kept):
            kept.append(span)
    return sorted(kept, key=lambda s: s.start)


def apply_replacements(text: str, replacements: list[tuple[Span, str]]) -> str:
    result = text
    for span, pen_name in sorted(replacements, key=lambda r: r[0].start, reverse=True):
        result = result[: span.start] + pen_name + result[span.end :]
    return result


def reverse_text(text: str, mapping: Mapping) -> str:
    if not mapping.entries:
        return text
    lookup = {e.pen_name: e.original for e in mapping.entries}
    # Longest alternative first so a pen name inside a longer one never wins.
    pattern = re.compile(
        "|".join(re.escape(pen) for pen in sorted(lookup, key=len, reverse=True))
    )
    return pattern.sub(lambda m: lookup[m.group(0)], text)
