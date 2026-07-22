"""Step 2 — the mandatory review screen. The heart of the app."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from penname.gui.models import COL_ORIGINAL, COL_TYPE, ReviewModel
from penname.gui.theme import tokens as t
from penname.gui.widgets import PillDelegate

BANNER_TEXT = (
    "Penname reduces what you share. It does not make data anonymous. "
    "Always review before sending.\n"
    "Check every row below — untick anything that should keep its real value, "
    "and click a pen name to change it."
)


class ReviewView(QWidget):
    continue_clicked = Signal()
    value_added = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE_32, t.SPACE_32, t.SPACE_32, t.SPACE_32)
        layout.setSpacing(t.SPACE_16)

        heading = QLabel("Review the pen names")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        banner = QLabel(BANNER_TEXT)
        banner.setProperty("role", "notice")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addSpacing(t.SPACE_8)

        self.model = ReviewModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(False)  # flat sheet, not a zebra grid
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setItemDelegateForColumn(COL_TYPE, PillDelegate(self.table))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # "How sure?"
        header.setHighlightSections(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(t.ROW_HEIGHT)
        layout.addWidget(self.table, 1)

        self.count_label = QLabel("")
        self.count_label.setProperty("role", "helper")
        layout.addWidget(self.count_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(t.SPACE_12)

        add_button = QPushButton("Add something Penname missed…")
        add_button.clicked.connect(self._add_value)
        buttons.addWidget(add_button)
        buttons.addStretch(1)

        self.continue_button = QPushButton("Looks good — continue to export")
        self.continue_button.setProperty("role", "primary")
        self.continue_button.clicked.connect(self.continue_clicked)
        buttons.addWidget(self.continue_button)
        layout.addLayout(buttons)

    def load_mapping(self, mapping) -> None:
        self.model.load_mapping(mapping)
        n = self.model.rowCount()
        self.count_label.setText(
            f"Found {n} value{'s' if n != 1 else ''} that may be sensitive. "
            "No tool catches everything — please read your document once more "
            "before sharing it."
        )
        if self.model.rowCount() > 0:
            self.table.setCurrentIndex(self.model.index(0, COL_ORIGINAL))

    def _add_value(self) -> None:
        text, ok = QInputDialog.getText(
            self,
            "Add a value",
            "Type the exact text that should get a pen name\n"
            "(for example a fund code or a nickname):",
        )
        if ok and text.strip():
            self.value_added.emit(text.strip())
