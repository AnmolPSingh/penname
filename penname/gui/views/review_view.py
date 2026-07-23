"""Step 2 — the mandatory review screen. The heart of the app."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from penname.gui.models import COL_ORIGINAL, COL_REPLACE, COL_TYPE, ReviewModel
from penname.gui.theme import tokens as t
from penname.gui.widgets import PillDelegate

#: At or above this, a value matched a pattern rather than being guessed at.
_CERTAIN = 0.85

BANNER_TEXT = (
    "Penname reduces what you share. It does not make data anonymous. "
    "Always review before sending.\n"
    "Check every row below. Untick anything that should keep its real value, "
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
        # A filter over every column, so typing "Gift" narrows to gift amounts
        # and typing a donor's name finds every row mentioning them. Long CRM
        # exports are unreviewable without it.
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        layout.addWidget(self._build_filter_row())

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setAlternatingRowColors(False)  # flat sheet, not a zebra grid
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setItemDelegateForColumn(COL_TYPE, PillDelegate(self.table))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_TYPE, QHeaderView.ResizeToContents)  # pills
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # "How sure?"
        header.setHighlightSections(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(t.ROW_HEIGHT)
        layout.addWidget(self.table, 1)

        self.count_label = QLabel("")
        self.count_label.setProperty("role", "helper")
        self.count_label.setWordWrap(True)
        layout.addWidget(self.count_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(t.SPACE_12)

        add_button = QPushButton("Add something Penname missed…")
        add_button.clicked.connect(self._add_value)
        buttons.addWidget(add_button)
        buttons.addStretch(1)

        self.continue_button = QPushButton("Looks good, continue to export")
        self.continue_button.setProperty("role", "primary")
        self.continue_button.clicked.connect(self.continue_clicked)
        buttons.addWidget(self.continue_button)
        layout.addLayout(buttons)

    def _build_filter_row(self) -> QWidget:
        row = QHBoxLayout()
        row.setSpacing(t.SPACE_12)

        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("Search these values, or a type like Gift amount")
        self.filter_box.setClearButtonEnabled(True)
        self.filter_box.textChanged.connect(self._on_filter_changed)
        row.addWidget(self.filter_box, 1)

        self.tick_all_button = QPushButton("Tick all shown")
        self.tick_all_button.clicked.connect(lambda: self._set_all_shown(True))
        row.addWidget(self.tick_all_button)

        self.untick_all_button = QPushButton("Untick all shown")
        self.untick_all_button.clicked.connect(lambda: self._set_all_shown(False))
        row.addWidget(self.untick_all_button)

        wrap = QWidget()
        wrap.setLayout(row)
        return wrap

    def _on_filter_changed(self, text: str) -> None:
        self.proxy.setFilterFixedString(text)
        self._update_count()

    def _set_all_shown(self, replace: bool) -> None:
        """Bulk-apply to the rows currently visible, which is what the filter is
        for: narrow to one type, then decide about all of it at once."""
        state = Qt.Checked if replace else Qt.Unchecked
        for proxy_row in range(self.proxy.rowCount()):
            source = self.proxy.mapToSource(self.proxy.index(proxy_row, COL_REPLACE))
            self.model.setData(source, state, Qt.CheckStateRole)

    def load_mapping(self, mapping) -> None:
        self.model.load_mapping(mapping)
        self._update_count()
        if self.proxy.rowCount() > 0:
            self.table.setCurrentIndex(self.proxy.index(0, COL_ORIGINAL))

    def _update_count(self) -> None:
        rows = self.model.rows()
        total = len(rows)
        shown = self.proxy.rowCount()
        # A pattern match (an email address, a code) is a fact. A name is the
        # language model's opinion. Saying so tells the reader where to look.
        certain = sum(1 for row in rows if row.score >= _CERTAIN)
        guessed = total - certain

        parts = [f"Found {total} value{'s' if total != 1 else ''} that may be sensitive."]
        if shown != total:
            parts.append(f"Showing {shown} of them.")
        if certain:
            parts.append(
                f"{certain} matched a known pattern, like an email address or a code."
            )
        if guessed:
            parts.append(
                f"{guessed} {'is' if guessed == 1 else 'are'} the language model's "
                "best guess, so check those first."
            )
        parts.append(
            "No tool catches everything. Please read your document once more "
            "before you share it."
        )
        self.count_label.setText(" ".join(parts))

    def _add_value(self) -> None:
        text, ok = QInputDialog.getText(
            self,
            "Add a value",
            "Type the exact text that should get a pen name\n"
            "(for example a fund code or a nickname):",
        )
        if ok and text.strip():
            self.value_added.emit(text.strip())
