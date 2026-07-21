"""Step 1 — open a document."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from penname.gui.flow import SUPPORTED_SUFFIXES
from penname.gui.theme import tokens as t

_FILE_FILTER = (
    "Documents (*.txt *.md *.csv *.xlsx *.docx *.pdf);;All files (*)"
)


class OpenView(QWidget):
    file_chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE_32, t.SPACE_32, t.SPACE_32, t.SPACE_32)
        layout.setSpacing(t.SPACE_16)

        heading = QLabel("Open a document")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        intro = QLabel(
            "Penname will look for names, dates, contact details, and other "
            "sensitive values, and suggest a pen name for each one.\n\n"
            "Everything happens on this computer. Nothing is sent anywhere."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.open_button = QPushButton("Choose a file…")
        self.open_button.setProperty("role", "primary")
        self.open_button.setMaximumWidth(420)
        self.open_button.clicked.connect(self._choose_file)
        layout.addWidget(self.open_button)

        formats = QLabel(
            "Works with: Word (.docx), Excel (.xlsx), spreadsheets saved as CSV, "
            "plain text (.txt, .md), and PDFs.\n"
            "For a PDF, Penname reads the text and gives you a Markdown copy. "
            "Scanned PDFs (pictures of pages) can't be read yet — please copy "
            "that text into a Word or text file first."
        )
        formats.setProperty("role", "helper")
        formats.setWordWrap(True)
        layout.addWidget(formats)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
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
