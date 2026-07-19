"""Document workflow controller — the only GUI code that talks to the engine.

Scanning runs in a worker thread (the first scan loads the language model and
takes several seconds). All engine logic stays in penname.core; this class
only sequences it.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from penname.core.engine import PennameSession, RoundTripError
from penname.core.io.dispatch import SUPPORTED_SUFFIXES, pseudonymize_file
from penname.core.io.markdown import export_markdown
from penname.core.io.text import write_document
from penname.core.mapping.crypto import MappingFileError
from penname.core.mapping.store import MappingStore
from penname.core.replace.applier import reverse_text
from penname.core.types import Mapping
from penname.gui.models import ReviewRow


class _ScanWorker(QObject):
    finished = Signal(object)  # Mapping
    failed = Signal(str)

    def __init__(self, flow: "DocumentFlow", source: Path):
        super().__init__()
        self._flow = flow
        self._source = source

    def run(self) -> None:
        try:
            # Session creation loads the language model — keep it off the UI
            # thread. Scanning pseudonymizes to a throwaway file (pseudonymized
            # content only — real values never touch the temp directory).
            self._flow._ensure_session()
            with tempfile.TemporaryDirectory(prefix="penname-") as tmp:
                mapping = pseudonymize_file(
                    self._source,
                    Path(tmp) / f"scan{self._source.suffix}",
                    self._flow.session,
                )
            self.finished.emit(mapping)
        except Exception as exc:  # surfaced as a plain-language message
            self.failed.emit(str(exc))


class DocumentFlow(QObject):
    scan_started = Signal(str)  # file name
    scan_finished = Signal(object)  # Mapping
    scan_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session: PennameSession | None = None  # created lazily off-thread
        self.source: Path | None = None
        self._thread: QThread | None = None
        self._worker: _ScanWorker | None = None

    def _ensure_session(self) -> None:
        if self.session is None:
            self.session = PennameSession()

    # -- step 1: open + scan ----------------------------------------------
    def open_document(self, path: str | Path) -> None:
        if self._thread is not None and self._thread.isRunning():
            return  # a scan is already in flight; ignore re-entrant calls
        source = Path(path)
        self.source = source
        self.scan_started.emit(source.name)

        thread = QThread(self)
        worker = _ScanWorker(self, source)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self.scan_finished)
        worker.failed.connect(self.scan_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._worker = worker
        self._thread = thread
        thread.start()

    # -- step 2: apply review decisions -----------------------------------
    def apply_review(self, rows: list[ReviewRow]) -> None:
        assert self.session is not None
        for row in rows:
            if not row.replace_it:
                self.session.ignore_value(row.entity_type, row.original)
            else:
                self.session.unignore_value(row.entity_type, row.original)
                if row.pen_name_edited:
                    self.session.set_pen_name(
                        row.entity_type, row.original, row.pen_name
                    )

    def add_custom_value(self, value: str) -> None:
        assert self.session is not None
        self.session.always_replace(value)

    def rescan(self) -> Mapping:
        """Fast re-run after review changes (pen names are cached)."""
        assert self.source is not None and self.session is not None
        with tempfile.TemporaryDirectory(prefix="penname-") as tmp:
            return pseudonymize_file(
                self.source, Path(tmp) / f"scan{self.source.suffix}", self.session
            )

    # -- step 3: export ----------------------------------------------------
    def export(self, dest: str | Path, also_markdown: bool) -> tuple[Path, Path | None]:
        assert self.source is not None and self.session is not None
        dest = Path(dest)
        mapping = pseudonymize_file(self.source, dest, self.session)
        mapping_path = dest.with_suffix(".pnmap")
        MappingStore().save(mapping, mapping_path)
        markdown_path: Path | None = None
        if also_markdown:
            markdown_path = dest.with_suffix(".md")
            export_markdown(dest, markdown_path)
        return mapping_path, markdown_path

    # -- step 4: reverse ---------------------------------------------------
    @staticmethod
    def reverse_to_file(
        response_text: str, mapping_path: str | Path, dest: str | Path
    ) -> int:
        """Returns how many pen names were taken off. Restored text goes to
        the file only — it is never returned for display."""
        mapping = MappingStore().load(mapping_path)
        restored = reverse_text(response_text, mapping)
        write_document(dest, restored)
        return sum(1 for e in mapping.entries if e.pen_name in response_text)


__all__ = [
    "DocumentFlow",
    "MappingFileError",
    "RoundTripError",
    "SUPPORTED_SUFFIXES",
]
