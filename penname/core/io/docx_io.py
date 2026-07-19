"""DOCX path: paragraph-level pseudonymization, run-aware.

Detected values can cross styled runs, so each changed paragraph is rewritten
as a single run carrying the paragraph's first-run formatting. Unchanged
paragraphs keep their runs untouched.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

from penname.core.engine import PennameSession, RoundTripError
from penname.core.replace.applier import reverse_text
from penname.core.types import Mapping, MappingEntry


def _iter_paragraphs(doc: Document):
    yield from doc.paragraphs
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs


def _rewrite(paragraph: Paragraph, new_text: str) -> None:
    first_run_style = paragraph.runs[0].style if paragraph.runs else None
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)
    run = paragraph.add_run(new_text)
    if first_run_style is not None:
        run.style = first_run_style


def pseudonymize_docx(
    source: str | Path, dest: str | Path, session: PennameSession
) -> Mapping:
    doc = Document(str(source))
    entries: dict[tuple[str, str], MappingEntry] = {}
    replaced: list[tuple[str, str]] = []

    for paragraph in _iter_paragraphs(doc):
        text = paragraph.text
        if not text.strip():
            continue
        result = session.pseudonymize(text)
        for entry in result.mapping.entries:
            entries[(entry.entity_type, entry.original)] = entry
        if result.text != text:
            replaced.append((text, result.text))
            _rewrite(paragraph, result.text)

    mapping = Mapping(entries=tuple(entries.values()))
    for original, pseudonymized in replaced:
        if reverse_text(pseudonymized, mapping) != original:
            raise RoundTripError(
                "a value in this document could not be pseudonymized reversibly"
            )

    doc.save(str(dest))
    return mapping
