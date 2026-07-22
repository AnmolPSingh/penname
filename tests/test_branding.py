"""Philanthropel branding, version, and license/trademark attribution."""

from pathlib import Path

import penname

ROOT = Path(__file__).resolve().parent.parent


def test_version_is_2() -> None:
    assert penname.__version__ == "2.0.0"


def test_attribution_constants() -> None:
    assert penname.COMPANY == "Philanthropel Limited"
    assert "Philanthropel Limited" in penname.COPYRIGHT
    assert "nonprofits" in penname.TAGLINE and "Philanthropel" in penname.TAGLINE
    assert "Apache-2.0" in penname.LICENSE_LINE
    assert "trademark" in penname.LICENSE_LINE.lower()


def test_license_names_philanthropel() -> None:
    assert "Copyright 2026 Philanthropel Limited" in (ROOT / "LICENSE").read_text()


def test_notice_reserves_trademarks() -> None:
    notice = (ROOT / "NOTICE").read_text()
    assert "Philanthropel Limited" in notice
    assert "TRADEMARKS" in notice
    assert "Apache" in notice


def test_readme_keeps_open_source_and_credits_philanthropel() -> None:
    readme = (ROOT / "README.md").read_text()
    assert "open-source" in readme or "open source" in readme
    assert "Philanthropel" in readme
    assert "trademark" in readme.lower()


def test_about_view_shows_version_and_copyright(qtbot) -> None:
    from PySide6.QtWidgets import QLabel

    from penname.gui.views.about_view import AboutView

    view = AboutView()
    qtbot.addWidget(view)
    joined = " ".join(w.text() for w in view.findChildren(QLabel))
    assert "2.0.0" in joined
    assert "Philanthropel Limited" in joined


def test_main_window_has_about_page(qtbot) -> None:
    from penname.gui.app import PAGE_ABOUT, MainWindow

    window = MainWindow()
    qtbot.addWidget(window)
    window._go_to(PAGE_ABOUT)
    assert window.pages.currentIndex() == PAGE_ABOUT
