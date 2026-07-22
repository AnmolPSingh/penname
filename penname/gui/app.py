"""Penname desktop app — window shell, sidebar navigation, view wiring.

Thin wrapper over penname.core via DocumentFlow. No engine logic lives here.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from penname.gui.assets import asset_path
from penname.gui.flow import DocumentFlow
from penname.gui.theme import tokens as t
from penname.gui.theme.qss import build_stylesheet
from penname.gui.views.about_view import AboutView
from penname.gui.views.export_view import ExportView
from penname.gui.views.open_view import OpenView
from penname.gui.views.review_view import ReviewView
from penname.gui.views.reverse_view import ReverseView

NAV_ITEMS = ("1.  Open", "2.  Review", "3.  Export", "Take pen names off")
PAGE_OPEN, PAGE_REVIEW, PAGE_EXPORT, PAGE_REVERSE, PAGE_ABOUT = range(5)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Penname")
        self.setWindowIcon(QIcon(asset_path("penname-icon.png")))
        self.resize(1100, 720)

        self.flow = DocumentFlow(self)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        root.addWidget(self._build_sidebar())

        self.pages = QStackedWidget()
        self.open_view = OpenView()
        self.review_view = ReviewView()
        self.export_view = ExportView()
        self.reverse_view = ReverseView()
        self.about_view = AboutView()
        for view in (
            self.open_view,
            self.review_view,
            self.export_view,
            self.reverse_view,
            self.about_view,
        ):
            self.pages.addWidget(view)
        root.addWidget(self.pages, 1)

        self._wire()
        self._set_step_enabled(PAGE_REVIEW, False)
        self._set_step_enabled(PAGE_EXPORT, False)
        self._go_to(PAGE_OPEN)

    # -- chrome ------------------------------------------------------------
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setProperty("role", "sidebar")
        sidebar.setFixedWidth(t.SIDEBAR_WIDTH)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(t.SPACE_16, t.SPACE_24, t.SPACE_16, t.SPACE_24)
        layout.setSpacing(t.SPACE_8)

        brand = QLabel("Penname")
        brand.setProperty("role", "brand")
        layout.addWidget(brand)

        tagline = QLabel("Pen names for sensitive values")
        tagline.setProperty("role", "helper")
        tagline.setWordWrap(True)
        layout.addWidget(tagline)
        layout.addSpacing(t.SPACE_24)

        self.nav_group = QButtonGroup(self)
        self.nav_buttons: list[QPushButton] = []
        for i, label in enumerate(NAV_ITEMS):
            button = QPushButton(label)
            button.setProperty("role", "nav")
            button.setCheckable(True)
            button.setMinimumHeight(t.HIT_TARGET)
            button.setCursor(Qt.PointingHandCursor)
            self.nav_group.addButton(button, i)
            self.nav_buttons.append(button)
            layout.addWidget(button)
        self.nav_group.idClicked.connect(self._go_to)

        layout.addStretch(1)

        about_button = QPushButton("About Penname")
        about_button.setProperty("role", "nav")
        about_button.setCursor(Qt.PointingHandCursor)
        about_button.clicked.connect(lambda: self._go_to(PAGE_ABOUT))
        layout.addWidget(about_button)

        offline = QLabel("Everything stays on this computer.")
        offline.setProperty("role", "helper")
        offline.setWordWrap(True)
        layout.addWidget(offline)

        # Attribution: a free, open-source tool by Philanthropel.
        credit = QHBoxLayout()
        credit.setSpacing(t.SPACE_8)
        credit.setContentsMargins(0, t.SPACE_8, 0, 0)
        mark = QLabel()
        pm = QPixmap(asset_path("philanthropel-mnemonic.png"))
        if not pm.isNull():
            mark.setPixmap(pm.scaledToHeight(18, Qt.SmoothTransformation))
        credit.addWidget(mark)
        by = QLabel("by Philanthropel")
        by.setProperty("role", "helper")
        credit.addWidget(by)
        credit.addStretch(1)
        credit_row = QWidget()
        credit_row.setLayout(credit)
        layout.addWidget(credit_row)
        return sidebar

    # -- wiring ------------------------------------------------------------
    def _wire(self) -> None:
        self.open_view.file_chosen.connect(self.flow.open_document)
        self.flow.scan_started.connect(self.open_view.show_scanning)
        self.flow.scan_finished.connect(self._on_scan_finished)
        self.flow.scan_failed.connect(self.open_view.show_error)

        self.review_view.value_added.connect(self._on_value_added)
        self.review_view.continue_clicked.connect(self._on_review_done)

        self.export_view.export_requested.connect(self._on_export)
        self.reverse_view.restore_requested.connect(self._on_restore)

    def _go_to(self, page: int) -> None:
        self.pages.setCurrentIndex(page)
        if page < len(self.nav_buttons):  # About has no numbered nav button
            self.nav_buttons[page].setChecked(True)

    def _set_step_enabled(self, page: int, enabled: bool) -> None:
        self.nav_buttons[page].setEnabled(enabled)

    # -- handlers ----------------------------------------------------------
    def _on_scan_finished(self, mapping) -> None:
        self.open_view.show_idle()
        self.review_view.load_mapping(mapping)
        if self.flow.source is not None:
            self.export_view.set_source_name(self.flow.source.name)
        self._set_step_enabled(PAGE_REVIEW, True)
        self._go_to(PAGE_REVIEW)

    def _on_value_added(self, value: str) -> None:
        try:
            self.flow.add_custom_value(value)
            self.review_view.load_mapping(self.flow.rescan())
        except Exception as exc:
            self.review_view.count_label.setText(f"Could not add that value: {exc}")

    def _on_review_done(self) -> None:
        try:
            self.flow.apply_review(self.review_view.model.rows())
            self.review_view.load_mapping(self.flow.rescan())
        except ValueError as exc:
            self.review_view.count_label.setText(str(exc))
            return
        except Exception as exc:
            self.review_view.count_label.setText(
                f"One of the pen names cannot be used: {exc}"
            )
            return
        self._set_step_enabled(PAGE_EXPORT, True)
        self._go_to(PAGE_EXPORT)

    def _on_export(self, dest: str, also_markdown: bool) -> None:
        try:
            mapping_path, markdown_path = self.flow.export(dest, also_markdown)
        except Exception as exc:
            self.export_view.show_error(str(exc))
            return
        self.export_view.show_success(
            dest, str(mapping_path), str(markdown_path) if markdown_path else None
        )
        self.reverse_view.set_mapping_path(str(mapping_path))

    def _on_restore(self, response_text: str, mapping_path: str, dest: str) -> None:
        try:
            count = self.flow.reverse_to_file(response_text, mapping_path, dest)
        except Exception as exc:
            self.reverse_view.show_error(str(exc))
            return
        self.reverse_view.show_success(count, dest)


def main() -> int:
    from penname.gui.qt_env import ensure_qt_plugins_reachable

    ensure_qt_plugins_reachable()
    app = QApplication(sys.argv)
    app.setApplicationName("Penname")
    app.setStyleSheet(build_stylesheet())
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
