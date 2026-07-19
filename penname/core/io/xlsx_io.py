"""XLSX path: pseudonymize text cells across all sheets via one shared session.

Formulas pass through verbatim (they are flagged for the user's review in the
GUI, not rewritten), and non-text values are never touched.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from penname.core.engine import PennameSession, RoundTripError
from penname.core.replace.applier import reverse_text
from penname.core.types import Mapping, MappingEntry


def pseudonymize_xlsx(
    source: str | Path, dest: str | Path, session: PennameSession
) -> Mapping:
    workbook = load_workbook(source)
    entries: dict[tuple[str, str], MappingEntry] = {}
    replaced: list[tuple[str, str]] = []  # (original, pseudonymized) per changed cell

    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows():
            for cell in row:
                value = cell.value
                if not isinstance(value, str) or value.startswith("="):
                    continue
                result = session.pseudonymize(value)
                for entry in result.mapping.entries:
                    entries[(entry.entity_type, entry.original)] = entry
                if result.text != value:
                    replaced.append((value, result.text))
                    cell.value = result.text

    mapping = Mapping(entries=tuple(entries.values()))
    for original, pseudonymized in replaced:
        if reverse_text(pseudonymized, mapping) != original:
            raise RoundTripError(
                "a value in this workbook could not be pseudonymized reversibly"
            )

    workbook.save(dest)
    return mapping
