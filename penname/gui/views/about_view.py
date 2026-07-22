"""About screen — product identity, version, and Philanthropel attribution."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from penname import COPYRIGHT, DISCLAIMER, LICENSE_LINE, TAGLINE, __version__
from penname.gui.assets import asset_path
from penname.gui.theme import tokens as t


def _pixmap(name: str, height: int) -> QPixmap:
    pm = QPixmap(asset_path(name))
    if pm.isNull():
        return pm
    return pm.scaledToHeight(height, Qt.SmoothTransformation)


class AboutView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE_32, t.SPACE_32, t.SPACE_32, t.SPACE_32)
        layout.setSpacing(t.SPACE_12)

        heading = QLabel("About Penname")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)

        icon = QLabel()
        icon.setPixmap(_pixmap("penname-icon.png", 96))
        layout.addSpacing(t.SPACE_8)
        layout.addWidget(icon)

        name = QLabel(f"Penname {__version__}")
        name.setProperty("role", "brand")
        layout.addWidget(name)

        tagline = QLabel(TAGLINE)
        tagline.setWordWrap(True)
        layout.addWidget(tagline)

        layout.addSpacing(t.SPACE_32)
        by = QLabel("Made by")
        by.setProperty("role", "section")
        layout.addWidget(by)
        layout.addSpacing(t.SPACE_8)

        philan = QLabel()
        philan.setPixmap(_pixmap("philanthropel-logo.png", 30))
        layout.addWidget(philan)

        layout.addSpacing(t.SPACE_8)
        copyright_label = QLabel(COPYRIGHT)
        copyright_label.setProperty("role", "subhead")
        layout.addWidget(copyright_label)

        license_label = QLabel(LICENSE_LINE)
        license_label.setProperty("role", "helper")
        license_label.setWordWrap(True)
        layout.addWidget(license_label)

        disclaimer = QLabel(DISCLAIMER)
        disclaimer.setProperty("role", "banner")
        disclaimer.setWordWrap(True)
        layout.addSpacing(t.SPACE_8)
        layout.addWidget(disclaimer)

        offline = QLabel("Everything stays on this computer. No internet is ever used.")
        offline.setProperty("role", "helper")
        offline.setWordWrap(True)
        layout.addSpacing(t.SPACE_8)
        layout.addWidget(offline)

        layout.addStretch(1)
