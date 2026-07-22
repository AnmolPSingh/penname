"""Shared UI components from DESIGN.md: cards, pill chips, centred column."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from penname.gui.theme import tokens as t


class Card(QFrame):
    """Soft Paper surface, 16px radius, hairline border, 16px padding."""

    def __init__(self, title: str, body: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE_16, t.SPACE_16, t.SPACE_16, t.SPACE_16)
        layout.setSpacing(t.SPACE_4)

        title_label = QLabel(title)
        title_label.setProperty("role", "cardtitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        if body:
            body_label = QLabel(body)
            body_label.setProperty("role", "cardbody")
            body_label.setWordWrap(True)
            layout.addWidget(body_label)


def centered_column(inner: QWidget, max_width: int = t.CONTENT_MAX_WIDTH) -> QWidget:
    """Cap content at the spec's 900px and centre it on the canvas.

    The inner column must expand to fill that width (not shrink to its size
    hint), otherwise the content huddles in the middle and the canvas reads
    as dead space."""
    inner.setMaximumWidth(max_width)
    inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    wrapper = QWidget()
    row = QHBoxLayout(wrapper)
    row.setContentsMargins(0, 0, 0, 0)
    row.addStretch(0)
    row.addWidget(inner, 1)
    row.addStretch(0)
    return wrapper


class PillDelegate(QStyledItemDelegate):
    """Draws a cell's text as a pill chip (DESIGN.md 'Pill Chip').

    Near-transparent fill, ink text, hairline Warm Mist outline, full radius.
    Teal stays reserved for active navigation, so chips here are neutral."""

    def paint(self, painter: QPainter, option, index) -> None:
        text = index.data(Qt.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # cell background (the table's own surface)
        painter.fillRect(option.rect, QColor(t.SOFT_PAPER))

        font = QFont(painter.font())
        font.setPixelSize(t.TEXT_MICRO)
        font.setWeight(QFont.Medium)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        pad_x, pad_y = t.SPACE_12, t.SPACE_4
        width = metrics.horizontalAdvance(text) + pad_x * 2
        height = metrics.height() + pad_y * 2
        x = option.rect.left() + t.SPACE_8
        y = option.rect.center().y() - height / 2
        pill = QRectF(x, y, width, height)

        painter.setPen(QPen(QColor(t.WARM_MIST), 1))
        painter.setBrush(QColor(t.PARCHMENT))
        painter.drawRoundedRect(pill, height / 2, height / 2)

        painter.setPen(QColor(t.INK))
        painter.drawText(pill, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), t.ROW_HEIGHT))
        return size
