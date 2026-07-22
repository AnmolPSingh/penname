"""Review-table model: one row per detected value, nothing destructive.

Unchecking "Change?" keeps the real value — and can be re-checked,
which is this screen's undo. The pen-name column is directly editable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from penname.core.types import Mapping
from penname.core.labels import certainty_label, entity_label

COLUMNS = ("Change?", "Real value", "What it is", "How sure?", "Pen name")
COL_REPLACE, COL_ORIGINAL, COL_TYPE, COL_CERTAINTY, COL_PEN = range(5)


@dataclass(frozen=True)
class ReviewRow:
    original: str
    entity_type: str
    score: float
    pen_name: str
    replace_it: bool = True
    original_pen_name: str = field(default="")

    @property
    def pen_name_edited(self) -> bool:
        return self.pen_name != self.original_pen_name


class ReviewModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[ReviewRow] = []

    # -- population -------------------------------------------------------
    def load_mapping(self, mapping: Mapping) -> None:
        self.beginResetModel()
        self._rows = [
            ReviewRow(
                original=e.original,
                entity_type=e.entity_type,
                score=e.score,
                pen_name=e.pen_name,
                original_pen_name=e.pen_name,
            )
            for e in mapping.entries
        ]
        self.endResetModel()

    def rows(self) -> list[ReviewRow]:
        return list(self._rows)

    # -- Qt model API ------------------------------------------------------
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()
        if role == Qt.CheckStateRole and col == COL_REPLACE:
            return Qt.Checked if row.replace_it else Qt.Unchecked
        if role in (Qt.DisplayRole, Qt.EditRole):
            if col == COL_ORIGINAL:
                return row.original
            if col == COL_TYPE:
                return entity_label(row.entity_type)
            if col == COL_CERTAINTY:
                return certainty_label(row.score)
            if col == COL_PEN:
                return row.pen_name if row.replace_it else "(keeping the real value)"
        if role == Qt.ToolTipRole and col in (COL_ORIGINAL, COL_PEN):
            # Long values are elided in the cell, but the reviewer has to be
            # able to read the whole thing before deciding.
            return row.original if col == COL_ORIGINAL else row.pen_name
        return None

    def flags(self, index: QModelIndex):
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == COL_REPLACE:
            return base | Qt.ItemIsUserCheckable
        if index.column() == COL_PEN and self._rows[index.row()].replace_it:
            return base | Qt.ItemIsEditable
        return base

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        if not index.isValid():
            return False
        row = self._rows[index.row()]
        if index.column() == COL_REPLACE and role == Qt.CheckStateRole:
            self._rows[index.row()] = replace(
                row, replace_it=Qt.CheckState(value) == Qt.Checked
            )
        elif index.column() == COL_PEN and role == Qt.EditRole:
            text = str(value).strip()
            if not text or text == row.original:
                return False  # empty or identical pen names are never accepted
            self._rows[index.row()] = replace(row, pen_name=text)
        else:
            return False
        self.dataChanged.emit(
            self.index(index.row(), 0), self.index(index.row(), len(COLUMNS) - 1)
        )
        return True
