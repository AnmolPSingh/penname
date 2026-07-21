"""Format dispatch: one entry point for pseudonymizing any supported file."""

from __future__ import annotations

from pathlib import Path

from penname.core.engine import PennameSession
from penname.core.io.csv_io import pseudonymize_csv
from penname.core.io.text import read_document, write_document
from penname.core.types import Mapping

SUPPORTED_SUFFIXES = (".txt", ".md", ".csv", ".xlsx", ".docx", ".pdf")

# Formats that can only be read, never written back in the same format. PDF is
# extraction-only: its pseudonymized output is always Markdown.
READ_ONLY_SUFFIXES = (".pdf",)


def output_suffix_for(source: str | Path) -> str:
    """The suffix a pseudonymized copy of this file should use. Read-only
    inputs (PDF) always export to Markdown."""
    suffix = Path(source).suffix.lower()
    return ".md" if suffix in READ_ONLY_SUFFIXES else suffix


def pseudonymize_file(
    source: str | Path, dest: str | Path, session: PennameSession
) -> Mapping:
    source = Path(source)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return pseudonymize_csv(source, dest, session)
    if suffix == ".xlsx":
        from penname.core.io.xlsx_io import pseudonymize_xlsx

        return pseudonymize_xlsx(source, dest, session)
    if suffix == ".docx":
        from penname.core.io.docx_io import pseudonymize_docx

        return pseudonymize_docx(source, dest, session)
    if suffix == ".pdf":
        from penname.core.io.pdf_io import extract_text

        result = session.pseudonymize(extract_text(source))
        write_document(dest, result.text)  # always Markdown; the PDF is not rewritten
        return result.mapping
    result = session.pseudonymize(read_document(source))
    write_document(dest, result.text)
    return result.mapping
