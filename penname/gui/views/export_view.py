"""Step 3 — export the pen-named copy and the encrypted mapping."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from penname.gui.theme import tokens as t
from penname.gui.widgets import Card

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
        layout.setSpacing(t.SPACE_8)

        heading = QLabel("Save the pen-named copy")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        intro = QLabel("Penname saves two files side by side.")
        intro.setProperty("role", "subhead")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addSpacing(t.SPACE_16)
        grid = QGridLayout()
        grid.setHorizontalSpacing(t.SPACE_12)
        grid.setVerticalSpacing(t.SPACE_12)
        grid.addWidget(
            Card(
                "Your pen-named copy",
                "The document with pen names in place of the real values. This is "
                "the one you paste into your AI assistant.",
            ),
            0,
            0,
        )
        grid.addWidget(
            Card(
                "The key file (.pnmap)",
                "Encrypted, and kept on this computer. Keep it safe — you need it "
                "for the last step, to put the real values back.",
            ),
            0,
            1,
        )
        grid_wrap = QWidget()
        grid_wrap.setLayout(grid)
        layout.addWidget(grid_wrap)

        layout.addSpacing(t.SPACE_16)
        self.markdown_check = QCheckBox(
            "Also save a plain-text Markdown copy (easiest to paste into an AI assistant)"
        )
        self.markdown_check.setChecked(True)
        layout.addWidget(self.markdown_check)

        layout.addSpacing(t.SPACE_8)
        action_row = QHBoxLayout()
        action_row.setSpacing(t.SPACE_12)
        self.export_button = QPushButton("Choose where to save…")
        self.export_button.setProperty("role", "primary")
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.clicked.connect(self._choose_destination)
        action_row.addWidget(self.export_button)
        action_row.addStretch(1)
        action_wrap = QWidget()
        action_wrap.setLayout(action_row)
        layout.addWidget(action_wrap)

        layout.addSpacing(t.SPACE_16)
        reminder = QLabel(REVIEW_REMINDER)
        reminder.setProperty("role", "notice")
        reminder.setWordWrap(True)
        layout.addWidget(reminder)

        self.status = QLabel("")
        self.status.setProperty("role", "subhead")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(1)

        self._suggested_name = ""

    def set_source_name(self, name: str) -> None:
        from penname.core.io.dispatch import output_suffix_for

        stem, dot, _ = name.rpartition(".")
        # PDF (and other read-only inputs) export to Markdown, so suggest .md.
        out_suffix = output_suffix_for(name).lstrip(".")
        self._suggested_name = f"{stem}.pen.{out_suffix}" if dot else f"{name}.pen"

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
