"""Format dispatch: one entry point for pseudonymizing any supported file."""

from __future__ import annotations

from pathlib import Path

from penname.core.engine import PennameSession
from penname.core.io.csv_io import pseudonymize_csv
from penname.core.io.text import read_document, write_document
from penname.core.types import Mapping

SUPPORTED_SUFFIXES = (".txt", ".md", ".csv", ".xlsx", ".docx")


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
    result = session.pseudonymize(read_document(source))
    write_document(dest, result.text)
    return result.mapping
