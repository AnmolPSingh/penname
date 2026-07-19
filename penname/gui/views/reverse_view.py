"""Step 4 — take the pen names off the AI assistant's reply."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from penname.gui.theme import tokens as t


class ReverseView(QWidget):
    restore_requested = Signal(str, str, str)  # response text, mapping path, dest path

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE_32, t.SPACE_32, t.SPACE_32, t.SPACE_32)
        layout.setSpacing(t.SPACE_16)

        heading = QLabel("Take the pen names off")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        intro = QLabel(
            "Paste your AI assistant's reply below. Penname will put the real "
            "values back and save the result as a file on this computer."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.response_edit = QPlainTextEdit()
        self.response_edit.setPlaceholderText("Paste the assistant's reply here…")
        layout.addWidget(self.response_edit, 1)

        mapping_row = QHBoxLayout()
        mapping_row.setSpacing(t.SPACE_12)
        self.mapping_button = QPushButton("Choose the mapping file (.pnmap)…")
        self.mapping_button.clicked.connect(self._choose_mapping)
        mapping_row.addWidget(self.mapping_button)
        self.mapping_label = QLabel("No mapping file chosen yet.")
        self.mapping_label.setProperty("role", "helper")
        mapping_row.addWidget(self.mapping_label, 1)
        layout.addLayout(mapping_row)

        self.restore_button = QPushButton("Put the real values back and save…")
        self.restore_button.setProperty("role", "primary")
        self.restore_button.setMaximumWidth(420)
        self.restore_button.clicked.connect(self._restore)
        layout.addWidget(self.restore_button)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self._mapping_path = ""

    def set_mapping_path(self, path: str) -> None:
        self._mapping_path = path
        self.mapping_label.setText(f"Using: {path}")

    def _choose_mapping(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose the mapping file", "", "Penname mapping (*.pnmap)"
        )
        if path:
            self.set_mapping_path(path)

    def _restore(self) -> None:
        text = self.response_edit.toPlainText()
        if not text.strip():
            self.status.setText("Paste the assistant's reply first, then try again.")
            return
        if not self._mapping_path:
            self.status.setText(
                "Choose the mapping file first — it was saved next to your "
                "pen-named copy and ends in .pnmap."
            )
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save the restored text", "restored.txt"
        )
        if dest:
            self.restore_requested.emit(text, self._mapping_path, dest)

    def show_success(self, count: int, dest: str) -> None:
        self.status.setText(
            f"Done — took {count} pen name{'s' if count != 1 else ''} off and "
            f"saved the restored text to:\n{dest}"
        )

    def show_error(self, message: str) -> None:
        self.status.setText(f"Something went wrong: {message}")
