"""DOCX path: paragraph- and table-aware pseudonymization, text-level round trip."""

from pathlib import Path

import pytest
from docx import Document

from penname.core.engine import PennameSession
from penname.core.io.docx_io import pseudonymize_docx
from penname.core.replace.applier import reverse_text


@pytest.fixture
def document_path(tmp_path: Path) -> Path:
    doc = Document()
    doc.add_heading("Stewardship Notes", level=1)
    p = doc.add_paragraph("Met with ")
    p.add_run("Robert Castellano").bold = True  # entity split across styled runs
    p.add_run(" at his home in Santa Fe on June 3, 2025.")
    doc.add_paragraph(
        "Follow up with his daughter Maria Castellano-Reyes at (505) 555-0177."
    )
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Donor"
    table.cell(0, 1).text = "Email"
    table.cell(1, 0).text = "Priya Raghunathan"
    table.cell(1, 1).text = "priya.r@fastmail.com"

    path = tmp_path / "notes.docx"
    doc.save(path)
    return path


def _all_texts(doc: Document) -> list[str]:
    texts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                texts.extend(p.text for p in cell.paragraphs)
    return texts


def test_docx_text_round_trips(document_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "notes.pen.docx"
    mapping = pseudonymize_docx(document_path, out, PennameSession())

    original_texts = _all_texts(Document(str(document_path)))
    pen_texts = _all_texts(Document(str(out)))
    assert len(pen_texts) == len(original_texts)

    for original, pen in zip(original_texts, pen_texts):
        assert reverse_text(pen, mapping) == original


def test_docx_structure_preserved_and_names_replaced(
    document_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / "notes.pen.docx"
    pseudonymize_docx(document_path, out, PennameSession())

    original = Document(str(document_path))
    pen = Document(str(out))
    assert len(pen.paragraphs) == len(original.paragraphs)
    assert len(pen.tables) == len(original.tables)

    joined = "\n".join(_all_texts(pen))
    assert "Robert Castellano" not in joined  # even though split across runs
    assert "priya.r@fastmail.com" not in joined
