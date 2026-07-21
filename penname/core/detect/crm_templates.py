"""CRM column-name templates.

Known donor-CRM exports (Raiser's Edge NXT, Salesforce NPSP, DonorPerfect,
Bloomerang, Little Green Light) use recognizable column headers. When a file's
header row matches one, we can pseudonymize a whole column by what the header
says it holds — catching values (IDs, amounts, fund codes) that would not
trigger content-based detection on their own.

Templates are data files in ``crm_templates/``; this module only loads and
matches them.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent / "crm_templates"


def _normalize(header: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace/underscores."""
    cleaned = re.sub(r"[^a-z0-9]+", " ", header.lower())
    return cleaned.strip()


@lru_cache(maxsize=1)
def load_column_types() -> dict[str, str]:
    """Merge every template into one normalized column-name -> entity map."""
    merged: dict[str, str] = {}
    for path in sorted(_TEMPLATE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for column, entity_type in data.get("columns", {}).items():
            merged[_normalize(column)] = entity_type
    return merged


def match_header(header_row: list[str]) -> dict[int, str]:
    """Map column index -> entity type for header cells matching a template.

    Raw match, no threshold: an empty result means no cell matched. Callers
    that must decide whether a row *is* a header should use
    :func:`header_column_types`, which guards against coincidental matches."""
    column_types = load_column_types()
    matches: dict[int, str] = {}
    for index, cell in enumerate(header_row):
        entity_type = column_types.get(_normalize(cell))
        if entity_type is not None:
            matches[index] = entity_type
    return matches


def header_column_types(row: list[str]) -> dict[int, str]:
    """Column-index -> entity map, but only if the row is *confidently* a CRM
    header: at least half of its non-empty cells match a template.

    This stops a single coincidental match (e.g. a data row whose one cell
    happens to read "Fund") from being mistaken for a header and skipped —
    which would silently leak that row's real values."""
    matches = match_header(row)
    non_empty = sum(1 for cell in row if cell and cell.strip())
    if not matches or non_empty == 0:
        return {}
    if len(matches) * 2 < non_empty:  # fewer than half matched -> not a header
        return {}
    return matches
