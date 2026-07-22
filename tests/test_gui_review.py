"""GUI layer: review model behavior, theme integrity, window smoke test."""

from PySide6.QtCore import Qt

from penname.core.types import Mapping, MappingEntry
from penname.gui.models import COL_PEN, COL_REPLACE, ReviewModel
from penname.gui.theme import tokens
from penname.gui.theme.qss import build_stylesheet

MAPPING = Mapping(
    entries=(
        MappingEntry("Margaret Wilson", "Dorothy Fields", "PERSON", 0.9),
        MappingEntry("s.chen@riversidecf.org", "j.m@example.org", "EMAIL_ADDRESS", 1.0),
        MappingEntry("Cleveland", "Springfield", "LOCATION", 0.5),
    )
)


def test_review_model_loads_and_labels(qtbot) -> None:
    model = ReviewModel()
    model.load_mapping(MAPPING)

    assert model.rowCount() == 3
    assert model.data(model.index(0, 1)) == "Margaret Wilson"
    assert model.data(model.index(0, 2)) == "Name"
    assert model.data(model.index(0, 3)) == "Very sure"
    assert model.data(model.index(2, 3)) == "Less sure, check this"
    assert model.data(model.index(0, COL_PEN)) == "Dorothy Fields"


def test_unchecking_keeps_real_value_and_is_reversible(qtbot) -> None:
    model = ReviewModel()
    model.load_mapping(MAPPING)

    index = model.index(0, COL_REPLACE)
    assert model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
    assert model.rows()[0].replace_it is False
    assert model.data(model.index(0, COL_PEN)) == "(keeping the real value)"

    # Undo: re-check restores the pen name.
    assert model.setData(index, Qt.Checked, Qt.CheckStateRole)
    assert model.rows()[0].replace_it is True
    assert model.data(model.index(0, COL_PEN)) == "Dorothy Fields"


def test_pen_name_edits_are_validated(qtbot) -> None:
    model = ReviewModel()
    model.load_mapping(MAPPING)
    index = model.index(0, COL_PEN)

    assert not model.setData(index, "")  # empty rejected
    assert not model.setData(index, "Margaret Wilson")  # identical rejected
    assert model.setData(index, "Eleanor Vance")
    assert model.rows()[0].pen_name == "Eleanor Vance"
    assert model.rows()[0].pen_name_edited


def test_stylesheet_uses_design_tokens_and_correct_language() -> None:
    import re

    qss = build_stylesheet()
    assert tokens.PARCHMENT in qss
    assert tokens.DEEP_TEAL in qss
    assert tokens.INK in qss
    # Check our own wording, not embedded asset paths: the checkout directory
    # may itself contain the banned word (e.g. ".../Document Anonymizer/").
    authored = re.sub(r'url\("[^"]*"\)', "url()", qss)
    assert "anonymiz" not in authored.lower()
    # DESIGN.md: weights capped at 500 — no bold anywhere in the theme.
    assert "font-weight: 600" not in qss and "bold" not in qss


def test_main_window_smoke(qtbot) -> None:
    from penname.gui.app import PAGE_EXPORT, PAGE_OPEN, PAGE_REVIEW, MainWindow

    window = MainWindow()
    qtbot.addWidget(window)

    # Workflow gating: review and export locked until a document is scanned.
    assert window.pages.currentIndex() == PAGE_OPEN
    assert not window.nav_buttons[PAGE_REVIEW].isEnabled()
    assert not window.nav_buttons[PAGE_EXPORT].isEnabled()

    # The mandated disclaimer is on the review screen.
    from penname.gui.views.review_view import BANNER_TEXT

    assert "does not make data anonymous" in BANNER_TEXT
    assert "review before sending" in BANNER_TEXT.lower()


def test_filter_narrows_rows_and_bulk_untick_applies_to_shown_only(qtbot) -> None:
    """A 500-row CRM export is unreviewable without filter + bulk actions."""
    from penname.gui.views.review_view import ReviewView

    view = ReviewView()
    qtbot.addWidget(view)
    view.load_mapping(MAPPING)
    assert view.proxy.rowCount() == 3

    view.filter_box.setText("margaret")
    assert view.proxy.rowCount() == 1

    view._set_all_shown(False)
    rows = view.model.rows()
    assert rows[0].replace_it is False  # the shown row
    assert rows[1].replace_it is True  # hidden rows untouched
    assert rows[2].replace_it is True

    view.filter_box.setText("")
    assert view.proxy.rowCount() == 3


def test_failure_states_use_the_alert_role_not_grey_body_text(qtbot) -> None:
    """Errors must be distinguishable from help text (critique P2)."""
    from penname.gui.views.export_view import ExportView
    from penname.gui.views.open_view import OpenView
    from penname.gui.views.reverse_view import ReverseView

    for view, args in (
        (OpenView(), ("disk is full",)),
        (ExportView(), ("disk is full",)),
        (ReverseView(), ("that key file does not match",)),
    ):
        qtbot.addWidget(view)
        view.show_error(*args)
        assert view.status.property("role") == "error"

    export = ExportView()
    qtbot.addWidget(export)
    export.show_success("out.docx", "out.pnmap", None)
    assert export.status.property("role") == "success"


def test_scanning_shows_progress_and_clears_on_finish(qtbot) -> None:
    from penname.gui.views.open_view import OpenView

    view = OpenView()
    qtbot.addWidget(view)
    assert not view.progress.isVisibleTo(view)

    view.show_scanning("appeal.docx")
    assert view.progress.isVisibleTo(view)
    assert not view.open_button.isEnabled()
    assert "appeal.docx" in view.status.text()

    view.show_idle()
    assert not view.progress.isVisibleTo(view)
    assert view.open_button.isEnabled()


def test_unsupported_file_reports_without_emitting(qtbot) -> None:
    from penname.gui.views.open_view import OpenView

    view = OpenView()
    qtbot.addWidget(view)
    emitted = []
    view.file_chosen.connect(emitted.append)

    view.accept_path("/tmp/photo.heic")
    assert emitted == []
    assert view.status.property("role") == "error"

    view.accept_path("/tmp/appeal.docx")
    assert emitted == ["/tmp/appeal.docx"]
