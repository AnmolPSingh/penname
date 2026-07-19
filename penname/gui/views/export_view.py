"""Step 3 — export the pen-named copy and the encrypted mapping."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from penname.gui.theme import tokens as t

REVIEW_REMINDER = (
    "Review before sending. Penname reduces what you share — "
    "it does not make data anonymous."
)


class ExportView(QWidget):
    export_requested = Signal(str, bool)  # destination path, also_markdown

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE_32, t.SPACE_32, t.SPACE_32, t.SPACE_32)
        layout.setSpacing(t.SPACE_16)

        heading = QLabel("Save the pen-named copy")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        intro = QLabel(
            "Penname will save two files side by side:\n"
            "•  a copy of your document with pen names in place of the real values\n"
            "•  an encrypted mapping file (.pnmap) that lets Penname put the real "
            "values back later. Keep it — you'll need it for the last step."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.markdown_check = QCheckBox(
            "Also save a plain-text Markdown copy (easiest to paste into an AI assistant)"
        )
        self.markdown_check.setChecked(True)
        layout.addWidget(self.markdown_check)

        self.export_button = QPushButton("Choose where to save…")
        self.export_button.setProperty("role", "primary")
        self.export_button.setMaximumWidth(420)
        self.export_button.clicked.connect(self._choose_destination)
        layout.addWidget(self.export_button)

        reminder = QLabel(REVIEW_REMINDER)
        reminder.setProperty("role", "banner")
        reminder.setWordWrap(True)
        layout.addWidget(reminder)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(1)

        self._suggested_name = ""

    def set_source_name(self, name: str) -> None:
        stem, dot, suffix = name.rpartition(".")
        self._suggested_name = f"{stem}.pen.{suffix}" if dot else f"{name}.pen"

    def _choose_destination(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save the pen-named copy", self._suggested_name
        )
        if path:
            self.export_requested.emit(path, self.markdown_check.isChecked())

    def show_success(self, dest: str, mapping_path: str, markdown_path: str | None) -> None:
        lines = [
            f"Saved the pen-named copy to:  {dest}",
            f"Saved the encrypted mapping to:  {mapping_path}",
        ]
        if markdown_path:
            lines.append(f"Saved the Markdown copy to:  {markdown_path}")
        lines.append("")
        lines.append(
            "Next: paste the pen-named copy into your AI assistant. When you have "
            "its reply, come back and use “Take the pen names off”."
        )
        self.status.setText("\n".join(lines))

    def show_error(self, message: str) -> None:
        self.status.setText(f"Something went wrong: {message}")


def default_directory(source: Path | None) -> str:
    return str(source.parent) if source else ""
