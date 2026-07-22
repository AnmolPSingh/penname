"""Step 4 — take the pen names off the AI assistant's reply."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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
        layout.setSpacing(t.SPACE_8)

        heading = QLabel("Take the pen names off")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        intro = QLabel(
            "Paste your assistant's reply. Penname puts the real values back and "
            "saves the result on this computer."
        )
        intro.setProperty("role", "subhead")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addSpacing(t.SPACE_16)
        paste_label = QLabel("The assistant's reply")
        paste_label.setProperty("role", "section")
        layout.addWidget(paste_label)
        layout.addSpacing(t.SPACE_4)

        self.response_edit = QPlainTextEdit()
        self.response_edit.setPlaceholderText("Paste the reply here…")
        layout.addWidget(self.response_edit, 1)

        layout.addSpacing(t.SPACE_16)
        key_label = QLabel("The key file")
        key_label.setProperty("role", "section")
        layout.addWidget(key_label)
        layout.addSpacing(t.SPACE_4)

        mapping_row = QHBoxLayout()
        mapping_row.setSpacing(t.SPACE_12)
        self.mapping_button = QPushButton("Choose the key file (.pnmap)…")
        self.mapping_button.setCursor(Qt.PointingHandCursor)
        self.mapping_button.clicked.connect(self._choose_mapping)
        mapping_row.addWidget(self.mapping_button)
        self.mapping_label = QLabel("No key file chosen yet.")
        self.mapping_label.setProperty("role", "helper")
        self.mapping_label.setWordWrap(True)
        mapping_row.addWidget(self.mapping_label, 1)
        mapping_wrap = QWidget()
        mapping_wrap.setLayout(mapping_row)
        layout.addWidget(mapping_wrap)

        layout.addSpacing(t.SPACE_16)
        action_row = QHBoxLayout()
        action_row.setSpacing(t.SPACE_12)
        self.restore_button = QPushButton("Put the real values back…")
        self.restore_button.setProperty("role", "primary")
        self.restore_button.setCursor(Qt.PointingHandCursor)
        self.restore_button.clicked.connect(self._restore)
        action_row.addWidget(self.restore_button)
        action_row.addStretch(1)
        action_wrap = QWidget()
        action_wrap.setLayout(action_row)
        layout.addWidget(action_wrap)

        self.status = QLabel("")
        self.status.setProperty("role", "subhead")
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
            self._show_status(
                "Paste the assistant's reply first, then try again.", "error"
            )
            return
        if not self._mapping_path:
            self._show_status(
                "Choose the key file first. It was saved next to your pen-named "
                "copy and ends in .pnmap.",
                "error",
            )
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save the restored text", "restored.txt"
        )
        if dest:
            self.restore_requested.emit(text, self._mapping_path, dest)

    def _show_status(self, text: str, role: str) -> None:
        self.status.setProperty("role", role)
        self.status.setText(text)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def show_success(self, count: int, dest: str) -> None:
        self._show_status(
            f"Done. Took {count} pen name{'s' if count != 1 else ''} off and "
            f"saved the restored text to:\n{dest}",
            "success",
        )

    def show_error(self, message: str) -> None:
        self._show_status(f"Nothing was restored. {message}", "error")
