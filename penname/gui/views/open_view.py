"""Step 1 — open a document."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from penname.gui.flow import SUPPORTED_SUFFIXES
from penname.gui.theme import tokens as t
from penname.gui.widgets import Card

_FILE_FILTER = (
    "Documents (*.txt *.md *.csv *.xlsx *.docx *.pdf);;All files (*)"
)


class OpenView(QWidget):
    file_chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
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
        action_row = QHBoxLayout()
        action_row.setSpacing(t.SPACE_12)
        self.open_button = QPushButton("Choose a file…")
        self.open_button.setProperty("role", "primary")
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.clicked.connect(self._choose_file)
        action_row.addWidget(self.open_button)
        action_row.addStretch(1)
        action_wrap = QWidget()
        action_wrap.setLayout(action_row)
        layout.addWidget(action_wrap)

        self.status = QLabel("")
        self.status.setProperty("role", "subhead")
        self.status.setWordWrap(True)
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
            "and PDFs. A PDF comes back as a Markdown copy; scanned PDFs "
            "(pictures of pages) can't be read yet."
        )
        formats.setProperty("role", "helper")
        formats.setWordWrap(True)
        layout.addWidget(formats)
        layout.addStretch(1)

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open a document", "", _FILE_FILTER)
        if not path:
            return
        if Path(path).suffix.lower() not in SUPPORTED_SUFFIXES:
            self.status.setText(
                "That file type isn't supported yet. Please choose a .docx, "
                ".xlsx, .csv, .txt, or .md file."
            )
            return
        self.file_chosen.emit(path)

    def show_scanning(self, name: str) -> None:
        self.open_button.setEnabled(False)
        self.status.setText(
            f"Reading {name} and looking for sensitive values… "
            "The first scan can take a little while."
        )

    def show_idle(self) -> None:
        self.open_button.setEnabled(True)

    def show_error(self, message: str) -> None:
        self.open_button.setEnabled(True)
        self.status.setText(f"Something went wrong: {message}")
