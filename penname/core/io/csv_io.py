"""CSV path: pseudonymize per cell through one shared session.

Consistency spans the whole file (the same donor in two rows gets one pen
name), and a file-level verification pass guarantees every cell reverses.
"""

from __future__ import annotations

import csv
from pathlib import Path

from penname.core.engine import PennameSession, RoundTripError
from penname.core.replace.applier import reverse_text
from penname.core.types import Mapping, MappingEntry


def pseudonymize_csv(
    source: str | Path,
    dest: str | Path,
    session: PennameSession,
) -> Mapping:
    with open(source, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    entries: dict[tuple[str, str], MappingEntry] = {}
    out_rows: list[list[str]] = []
    # Every row is scanned, including a possible header row: cells without
    # sensitive values pass through unchanged, and skipping row 0 blindly
    # would silently leak real data from headerless files.
    for row in rows:
        out_row = []
        for cell in row:
            result = session.pseudonymize(cell)
            for entry in result.mapping.entries:
                entries[(entry.entity_type, entry.original)] = entry
            out_row.append(result.text)
        out_rows.append(out_row)

    mapping = Mapping(entries=tuple(entries.values()))

    # File-level verification: every cell must reverse under the union mapping,
    # not just under its own cell's entries.
    for original_row, out_row in zip(rows, out_rows):
        for original_cell, out_cell in zip(original_row, out_row):
            if reverse_text(out_cell, mapping) != original_cell:
                raise RoundTripError(
                    "a value in this file could not be pseudonymized reversibly"
                )

    with open(dest, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out_rows)
    return mapping


def reverse_csv(
    source: str | Path, dest: str | Path, mapping: Mapping
) -> None:
    with open(source, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    restored = [[reverse_text(cell, mapping) for cell in row] for row in rows]
    with open(dest, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(restored)
