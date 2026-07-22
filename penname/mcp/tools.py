"""MCP tool logic — a thin wrapper over penname.core.

These are plain functions so they can be unit-tested without the MCP
transport. The server module registers them as tools.

CLAUDE.md rule 4 is the load-bearing constraint here: ``reverse_to_file`` must
never return restored donor content into the tool result. It writes the
restored text to a local file and returns only a success flag and the path.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from penname.core.engine import PennameSession, RoundTripError
from penname.core.io.dispatch import output_suffix_for, pseudonymize_file
from penname.core.io.text import write_document
from penname.core.labels import entity_label
from penname.core.mapping.crypto import MappingFileError
from penname.core.mapping.keychain import KeychainError
from penname.core.mapping.store import MappingStore
from penname.core.replace.applier import reverse_text

REVIEW_REMINDER = (
    "Penname reduces what you share; it does not make data anonymous. "
    "Open the pseudonymized file and review every replacement before sharing it."
)

class PathSafetyError(Exception):
    """A requested output path is outside the allowed folder."""


# Exception types whose messages are known to be static and content-free, so
# they are safe to surface to the caller. Anything else gets a generic message
# — never let an unrecognized exception echo donor text into the tool result.
_SAFE_TO_SHOW = (
    MappingFileError,
    RoundTripError,
    KeychainError,
    PathSafetyError,
    OSError,
    ValueError,
)


def _fail(exc: Exception) -> dict:
    message = str(exc) if isinstance(exc, _SAFE_TO_SHOW) else "An internal error occurred."
    return {"success": False, "message": message}


def _safe_write_path(candidate: Path, base: Path, overwrite: bool) -> Path:
    """Confine a write to inside ``base`` and refuse silent overwrites.

    Because the MCP caller (a model) chooses these paths, an unconstrained path
    would let a steered assistant write arbitrary files. Writes are limited to
    the folder of the input/mapping file, and never clobber an existing file
    unless the caller explicitly asks."""
    resolved = candidate.resolve()
    base = base.resolve()
    if base != resolved and base not in resolved.parents:
        raise PathSafetyError(
            "for safety, Penname only writes inside the folder of the file you "
            "gave it. Choose an output path in that folder."
        )
    if resolved.exists() and not overwrite:
        raise PathSafetyError(
            f"{resolved.name} already exists. Pass overwrite=true to replace it."
        )
    return resolved


def pseudonymize_document(
    input_path: str,
    output_path: str | None = None,
    mapping_path: str | None = None,
    overwrite: bool = False,
) -> dict:
    """Pseudonymize a document on disk. Returns the output and mapping paths
    plus counts by type — never the raw pen-named text, and never real values
    beyond what the caller already supplied. Output files are written inside the
    input file's folder only."""
    source = Path(input_path)
    if not source.is_file():
        return {"success": False, "message": f"Could not find the file: {source}"}

    base = source.resolve().parent
    default_dest = source.with_name(f"{source.stem}.pen{output_suffix_for(source)}")
    default_mapping = source.with_suffix(".pnmap")

    try:
        dest = _safe_write_path(
            Path(output_path) if output_path else default_dest, base, overwrite
        )
        mapping_file = _safe_write_path(
            Path(mapping_path) if mapping_path else default_mapping, base, overwrite
        )
        session = PennameSession()
        mapping = pseudonymize_file(source, dest, session)
        MappingStore().save(mapping, mapping_file)
    except Exception as exc:  # fail safe: never let a raw exception reach the model
        return _fail(exc)

    counts = Counter(entity_label(e.entity_type) for e in mapping.entries)
    return {
        "success": True,
        "pseudonymized_path": str(dest),
        "mapping_path": str(mapping_file),
        "replaced_count": len(mapping.entries),
        "counts_by_type": dict(counts),
        "review_required": True,
        "message": REVIEW_REMINDER,
    }


def reverse_to_file(
    response_text: str,
    mapping_path: str,
    output_path: str,
    overwrite: bool = False,
) -> dict:
    """Take the pen names off an assistant's reply and write the restored text
    to a local file. Returns ONLY a success flag, the path, and a count — the
    restored content is never placed in the tool result (CLAUDE.md rule 4). The
    output is written inside the mapping file's folder only."""
    try:
        base = Path(mapping_path).resolve().parent
        dest = _safe_write_path(Path(output_path), base, overwrite)
        mapping = MappingStore().load(mapping_path)
        restored = reverse_text(response_text, mapping)
        write_document(dest, restored)
    except Exception as exc:  # fail safe: a raw exception must never carry content
        return _fail(exc)

    restored_count = sum(1 for e in mapping.entries if e.pen_name in response_text)
    return {
        "success": True,
        "restored_path": str(dest),
        "restored_count": restored_count,
        "message": (
            "Restored text written to the file above. Its contents are kept out "
            "of this response on purpose."
        ),
    }
