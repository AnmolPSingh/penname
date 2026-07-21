"""PDF text extraction (read-only).

Penname never rewrites a PDF. It extracts the text from digital PDFs so the
engine can pseudonymize it; the output is always Markdown. Scanned / image-only
PDFs have no extractable text and are out of scope in v1 — they raise a clear
message rather than silently producing an empty file.
"""

from __future__ import annotations

from pathlib import Path


class PdfReadError(Exception):
    """The PDF could not be opened or read."""


class ScannedPdfError(Exception):
    """The PDF has no extractable text (likely scanned or image-only)."""


def extract_text(path: str | Path) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except (PyPdfError, OSError, ValueError) as exc:
        raise PdfReadError(f"could not read this PDF: {exc}") from exc

    text = "\n\n".join(part.strip() for part in pages if part.strip())
    if not text.strip():
        raise ScannedPdfError(
            "this PDF has no text Penname can read — it looks scanned or "
            "image-only. Scanned PDFs are not supported yet; please copy the "
            "text into a Word or text file first."
        )
    return text
