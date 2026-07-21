"""PDF path: read-only text extraction from digital PDFs, exported to Markdown.

Penname never rewrites a PDF. It extracts the text, pseudonymizes it, and the
output is always Markdown. Scanned PDFs (no extractable text) are out of scope
in v1 and must fail with a clear, plain-language message.
"""

from pathlib import Path

import pytest
from fpdf import FPDF

from penname.core.engine import PennameSession
from penname.core.io.dispatch import pseudonymize_file
from penname.core.io.pdf_io import ScannedPdfError, extract_text


def _make_pdf(path: Path, lines: list[str]) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.write(8, line + "\n")
    pdf.output(str(path))


@pytest.fixture
def donor_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "appeal.pdf"
    _make_pdf(
        path,
        [
            "Dear Margaret Wilson,",
            "Thank you for your gift of $25,000 to the Riverside Community Foundation.",
            "Please contact Sarah Chen at s.chen@riversidecf.org with any questions.",
        ],
    )
    return path


def test_extract_text_from_digital_pdf(donor_pdf: Path) -> None:
    text = extract_text(donor_pdf)
    assert "Margaret Wilson" in text
    assert "s.chen@riversidecf.org" in text


def test_scanned_pdf_raises_clear_error(tmp_path: Path) -> None:
    # A PDF with no extractable text stands in for a scanned/image-only PDF.
    blank = tmp_path / "scanned.pdf"
    pdf = FPDF()
    pdf.add_page()  # no text drawn
    pdf.output(str(blank))

    with pytest.raises(ScannedPdfError) as exc:
        extract_text(blank)
    assert "scanned" in str(exc.value).lower()


def test_pdf_pseudonymized_and_reversible(donor_pdf: Path, tmp_path: Path) -> None:
    dest = tmp_path / "appeal.pen.md"
    session = PennameSession()

    mapping = pseudonymize_file(donor_pdf, dest, session)

    out = dest.read_text(encoding="utf-8")
    assert "Margaret Wilson" not in out
    assert "s.chen@riversidecf.org" not in out
    assert mapping.entries
    # extracted text round-trips: reversing the pseudonymized markdown restores
    # exactly the text that was extracted from the PDF
    extracted = extract_text(donor_pdf)
    assert session.reverse(out, mapping) == extracted


def test_pdf_is_in_supported_suffixes() -> None:
    from penname.core.io.dispatch import SUPPORTED_SUFFIXES

    assert ".pdf" in SUPPORTED_SUFFIXES


def test_output_suffix_for_pdf_is_markdown() -> None:
    from penname.core.io.dispatch import output_suffix_for

    assert output_suffix_for("appeal.pdf") == ".md"
    assert output_suffix_for("appeal.PDF") == ".md"
    assert output_suffix_for("donors.csv") == ".csv"  # writable formats unchanged
    assert output_suffix_for("letter.docx") == ".docx"


def test_cli_pdf_exports_markdown(donor_pdf: Path, tmp_path: Path, monkeypatch) -> None:
    vault: dict = {}
    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda s, a: vault.get((s, a)))
    monkeypatch.setattr(keyring, "set_password", lambda s, a, v: vault.__setitem__((s, a), v))

    from penname.cli.main import main

    out = tmp_path / "appeal.pen.md"
    mapping = tmp_path / "appeal.pnmap"
    code = main(
        ["pseudonymize", str(donor_pdf), "-o", str(out), "--mapping", str(mapping), "--yes"]
    )
    assert code == 0
    assert out.exists()
    assert "Margaret Wilson" not in out.read_text(encoding="utf-8")
