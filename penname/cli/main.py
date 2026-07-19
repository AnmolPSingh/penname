"""Penname command line — a thin wrapper over the core engine.

Plain language throughout: the reader is a fundraiser, not a developer.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from penname.core.engine import PennameSession, RoundTripError
from penname.core.io.csv_io import pseudonymize_csv
from penname.core.io.text import read_document, write_document
from penname.core.mapping.crypto import MappingFileError
from penname.core.mapping.store import MappingStore
from penname.core.replace.applier import reverse_text

REVIEW_REMINDER = (
    "Review before sending. Penname reduces what you share — "
    "it does not make data anonymous."
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="penname",
        description=(
            "Give sensitive values in a document a pen name before sharing it "
            "with an AI assistant, then take the pen names off afterwards. "
            "Everything stays on your computer."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    pseudo = sub.add_parser(
        "pseudonymize", help="swap sensitive values for pen names"
    )
    pseudo.add_argument(
        "input", help="the document to open (.txt, .md, .csv, .xlsx, or .docx)"
    )
    pseudo.add_argument("-o", "--output", help="where to save the pen-named copy")
    pseudo.add_argument("--mapping", help="where to save the encrypted mapping file")

    reverse = sub.add_parser(
        "reverse", help="take the pen names off an AI assistant's response"
    )
    reverse.add_argument("input", help="a file containing the assistant's response")
    reverse.add_argument("--mapping", required=True, help="the mapping file saved earlier")
    reverse.add_argument("-o", "--output", help="where to save the restored text")
    return parser


def _default_output(source: Path, suffix: str) -> Path:
    return source.with_name(f"{source.stem}{suffix}{source.suffix}")


def _pseudonymize(args: argparse.Namespace) -> int:
    source = Path(args.input)
    if not source.is_file():
        print(f"Could not find the file: {source}", file=sys.stderr)
        return 1

    dest = Path(args.output) if args.output else _default_output(source, ".pen")
    mapping_path = (
        Path(args.mapping) if args.mapping else source.with_suffix(".pnmap")
    )

    session = PennameSession()
    suffix = source.suffix.lower()
    if suffix == ".csv":
        mapping = pseudonymize_csv(source, dest, session)
    elif suffix == ".xlsx":
        from penname.core.io.xlsx_io import pseudonymize_xlsx

        mapping = pseudonymize_xlsx(source, dest, session)
    elif suffix == ".docx":
        from penname.core.io.docx_io import pseudonymize_docx

        mapping = pseudonymize_docx(source, dest, session)
    else:
        result = session.pseudonymize(read_document(source))
        write_document(dest, result.text)
        mapping = result.mapping

    MappingStore().save(mapping, mapping_path)

    count = len(mapping.entries)
    print(f"Gave pen names to {count} value{'s' if count != 1 else ''}.")
    print(f"Saved the pen-named copy to: {dest}")
    print(f"Saved the encrypted mapping to: {mapping_path}")
    print(REVIEW_REMINDER)
    return 0


def _reverse(args: argparse.Namespace) -> int:
    source = Path(args.input)
    if not source.is_file():
        print(f"Could not find the file: {source}", file=sys.stderr)
        return 1

    mapping = MappingStore().load(args.mapping)
    restored = reverse_text(read_document(source), mapping)
    dest = (
        Path(args.output)
        if args.output
        else source.with_name(f"{source.stem}.restored{source.suffix or '.txt'}")
    )
    write_document(dest, restored)
    print(f"Took the pen names off. Saved the restored text to: {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "pseudonymize":
            return _pseudonymize(args)
        return _reverse(args)
    except MappingFileError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except RoundTripError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
