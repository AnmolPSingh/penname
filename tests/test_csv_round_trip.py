"""CSV path: per-cell pseudonymization through one session, cell-level round trip."""

import csv
from pathlib import Path

from penname.core.engine import PennameSession
from penname.core.io.csv_io import pseudonymize_csv
from penname.core.replace.applier import reverse_text

FIXTURE = Path(__file__).parent / "fixtures" / "donors.csv"


def _rows(path: Path) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_csv_cells_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "donors.pen.csv"
    session = PennameSession()

    mapping = pseudonymize_csv(FIXTURE, out, session)

    original_rows = _rows(FIXTURE)
    pen_rows = _rows(out)
    assert len(pen_rows) == len(original_rows)

    for orig_row, pen_row in zip(original_rows, pen_rows):
        assert len(pen_row) == len(orig_row)
        for orig_cell, pen_cell in zip(orig_row, pen_row):
            assert reverse_text(pen_cell, mapping) == orig_cell


def test_csv_header_passes_through_and_names_are_replaced(tmp_path: Path) -> None:
    out = tmp_path / "donors.pen.csv"

    pseudonymize_csv(FIXTURE, out, PennameSession())

    original_rows = _rows(FIXTURE)
    pen_rows = _rows(out)
    assert pen_rows[0] == original_rows[0]  # header untouched
    flat = [cell for row in pen_rows[1:] for cell in row]
    assert "Margaret Wilson" not in flat
    assert "m.wilson@homemail.com" not in flat


def test_csv_repeated_value_gets_one_pen_name(tmp_path: Path) -> None:
    """Margaret Wilson appears in two rows; both must show the same pen name."""
    out = tmp_path / "donors.pen.csv"

    pseudonymize_csv(FIXTURE, out, PennameSession())

    pen_rows = _rows(out)
    name_cells = [row[1] for row in pen_rows[1:]]
    assert name_cells[0] == name_cells[3]
