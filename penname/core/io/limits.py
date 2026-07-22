"""Guards against resource-exhaustion from untrusted input files.

Donor documents often arrive from outside parties, so a malformed or malicious
file must not be able to exhaust memory/disk before Penname's review step. These
checks run before any parser touches the file.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

# A plain file (csv/txt/md/pdf, or the on-disk size of xlsx/docx) larger than
# this is refused before parsing.
MAX_FILE_BYTES = 200 * 1024 * 1024  # 200 MB

# For zip-based formats (xlsx, docx), refuse when the total *uncompressed* size
# is implausibly large, or when the compression ratio looks like a zip bomb.
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 500 MB
MAX_COMPRESSION_RATIO = 100
_RATIO_MIN_BYTES = 50 * 1024 * 1024  # only judge ratio once output is sizeable


class InputTooLargeError(Exception):
    """The input file is too large or looks like a decompression bomb."""


def _human(n: int) -> str:
    return f"{n / (1024 * 1024):.0f} MB"


def check_file_size(path: str | Path) -> None:
    size = Path(path).stat().st_size
    if size > MAX_FILE_BYTES:
        raise InputTooLargeError(
            f"this file is very large ({_human(size)}). Penname handles files up "
            f"to {_human(MAX_FILE_BYTES)}; please split it or reduce it first."
        )


def check_zip_bomb(path: str | Path) -> None:
    """xlsx/docx are zip containers; make sure they don't expand absurdly."""
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            total = sum(i.file_size for i in infos)
            packed = sum(i.compress_size for i in infos) or 1
    except zipfile.BadZipFile as exc:
        raise InputTooLargeError("this file is not a valid Office document.") from exc

    if total > MAX_UNCOMPRESSED_BYTES:
        raise InputTooLargeError(
            f"this document expands to {_human(total)}, which is too large to open "
            "safely. It may be corrupted."
        )
    if total > _RATIO_MIN_BYTES and total / packed > MAX_COMPRESSION_RATIO:
        raise InputTooLargeError(
            "this document expands far more than expected and may be corrupted or "
            "unsafe, so Penname did not open it."
        )
