"""Step 1 — open a document."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from penname.gui.flow import SUPPORTED_SUFFIXES
from penname.gui.theme import tokens as t
from penname.gui.widgets import Card

_FILE_FILTER = "Documents (*.txt *.md *.csv *.xlsx *.docx *.pdf);;All files (*)"

# The first scan loads the language model, which can take half a minute on an
# older machine. Silence reads as "it has frozen", so the wait narrates itself.
_STAGE_DELAY_MS = 4000
_UNSUPPORTED = (
    "Penname can't read that kind of file yet. Please choose a Word, Excel, "
    "CSV, text, or PDF file."
)


class OpenView(QWidget):
    file_chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE_32, t.SPACE_32, t.SPACE_32, t.SPACE_32)
        layout.setSpacing(t.SPACE_8)

        heading = QLabel("Open a document")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        intro = QLabel(
            "Penname finds the sensitive values and suggests a pen name for each "
            "one. Everything happens on this computer."
        )
        intro.setProperty("role", "subhead")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addSpacing(t.SPACE_24)
        layout.addWidget(self._build_drop_zone())

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate: the length is unknowable
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        layout.addSpacing(t.SPACE_12)
        layout.addWidget(self.progress)

        self.status = QLabel("")
        self.status.setProperty("role", "subhead")
        self.status.setWordWrap(True)
        self.status.setVisible(False)
        layout.addWidget(self.status)

        layout.addSpacing(t.SPACE_32)
        what = QLabel("What Penname looks for")
        what.setProperty("role", "section")
        layout.addWidget(what)
        layout.addSpacing(t.SPACE_8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(t.SPACE_12)
        grid.setVerticalSpacing(t.SPACE_12)
        cards = [
            ("Names & organisations", "Donors, staff, trustees, and the groups they belong to."),
            ("Contact details", "Email addresses, phone numbers, and postal addresses."),
            ("Gifts & wealth", "Gift amounts, giving histories, and capacity ratings."),
            ("Codes & IDs", "Constituent IDs, fund, campaign, and appeal codes."),
        ]
        for i, (title, body) in enumerate(cards):
            grid.addWidget(Card(title, body), i // 2, i % 2)
        grid_wrap = QWidget()
        grid_wrap.setLayout(grid)
        layout.addWidget(grid_wrap)

        layout.addSpacing(t.SPACE_16)
        formats = QLabel(
            "Works with Word (.docx), Excel (.xlsx), CSV, plain text (.txt, .md), "
            "and PDFs. A PDF comes back as a Markdown copy. Scanned PDFs "
            "(pictures of pages) can't be read yet."
        )
        formats.setProperty("role", "helper")
        formats.setWordWrap(True)
        layout.addWidget(formats)
        layout.addStretch(1)

        self._stage_timer = QTimer(self)
        self._stage_timer.setInterval(_STAGE_DELAY_MS)
        self._stage_timer.timeout.connect(self._next_stage)
        self._stages: list[str] = []

    def _build_drop_zone(self) -> QFrame:
        zone = QFrame()
        zone.setProperty("role", "drop")
        zone.setProperty("dragging", "false")
        inner = QVBoxLayout(zone)
        inner.setContentsMargins(t.SPACE_24, t.SPACE_24, t.SPACE_24, t.SPACE_24)
        inner.setSpacing(t.SPACE_12)

        self.drop_label = QLabel("Drag a document here")
        self.drop_label.setProperty("role", "cardtitle")
        inner.addWidget(self.drop_label)

        row = QHBoxLayout()
        row.setSpacing(t.SPACE_12)
        self.open_button = QPushButton("Choose a file…")
        self.open_button.setProperty("role", "primary")
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.clicked.connect(self._choose_file)
        row.addWidget(self.open_button)
        or_label = QLabel("or browse your computer")
        or_label.setProperty("role", "helper")
        row.addWidget(or_label)
        row.addStretch(1)
        row_wrap = QWidget()
        row_wrap.setProperty("role", "plain")  # otherwise it paints the canvas
        row_wrap.setLayout(row)
        inner.addWidget(row_wrap)

        self._drop_zone = zone
        return zone

    # -- drag and drop -----------------------------------------------------
    @staticmethod
    def dropped_path(event) -> str | None:
        """The single local file being dragged, or None if it isn't one."""
        mime = event.mimeData()
        if not mime.hasUrls():
            return None
        urls = [u for u in mime.urls() if u.isLocalFile()]
        if len(urls) != 1:
            return None
        return urls[0].toLocalFile()

    def _set_dragging(self, dragging: bool) -> None:
        self._drop_zone.setProperty("dragging", "true" if dragging else "false")
        self._drop_zone.style().unpolish(self._drop_zone)
        self._drop_zone.style().polish(self._drop_zone)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self.open_button.isEnabled() and self.dropped_path(event):
            event.acceptProposedAction()
            self._set_dragging(True)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._set_dragging(False)

    def dropEvent(self, event) -> None:  # noqa: N802
        self._set_dragging(False)
        path = self.dropped_path(event)
        if path and self.open_button.isEnabled():
            event.acceptProposedAction()
            self.accept_path(path)

    # -- opening -----------------------------------------------------------
    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open a document", "", _FILE_FILTER)
        if path:
            self.accept_path(path)

    def accept_path(self, path: str) -> None:
        """Validate, then hand off. Shared by the picker, drops, and the window."""
        if Path(path).suffix.lower() not in SUPPORTED_SUFFIXES:
            self.show_error(_UNSUPPORTED)
            return
        self.file_chosen.emit(path)

    # -- states ------------------------------------------------------------
    def _show_status(self, text: str, role: str) -> None:
        self.status.setProperty("role", role)
        self.status.setText(text)
        self.status.setVisible(True)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def show_scanning(self, name: str) -> None:
        self.open_button.setEnabled(False)
        self.drop_label.setText(f"Reading {name}")
        self.progress.setVisible(True)
        self._stages = [
            f"Opening {name}.",
            "Getting ready. The first document of the day takes longer, because "
            "Penname is loading its language model.",
            f"Looking through {name} for names, contact details, gifts, and codes.",
            "Still working. A long document can take a minute or two.",
        ]
        self._next_stage()
        self._stage_timer.start()

    def _next_stage(self) -> None:
        if not self._stages:
            self._stage_timer.stop()
            return
        self._show_status(self._stages.pop(0), "subhead")

    def _stop_scanning(self) -> None:
        self._stage_timer.stop()
        self._stages = []
        self.progress.setVisible(False)
        self.open_button.setEnabled(True)
        self.drop_label.setText("Drag a document here")

    def show_idle(self) -> None:
        self._stop_scanning()
        self.status.setVisible(False)

    def show_error(self, message: str) -> None:
        self._stop_scanning()
        self._show_status(message, "error")
