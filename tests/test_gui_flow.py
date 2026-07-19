"""DocumentFlow: the GUI's end-to-end path — scan, review, export, reverse."""

from dataclasses import replace
from pathlib import Path

import pytest

from penname.gui.flow import DocumentFlow

FIXTURE = Path(__file__).parent / "fixtures" / "donor_letter_1.txt"


@pytest.fixture(autouse=True)
def fake_keychain(monkeypatch):
    vault: dict[tuple[str, str], str] = {}
    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda s, a: vault.get((s, a)))
    monkeypatch.setattr(
        keyring, "set_password", lambda s, a, v: vault.__setitem__((s, a), v)
    )


def test_flow_scan_review_export_reverse(qtbot, tmp_path: Path) -> None:
    flow = DocumentFlow()

    # 1. Open + scan (worker thread; first scan loads the language model)
    with qtbot.waitSignal(flow.scan_finished, timeout=120_000) as blocker:
        flow.open_document(FIXTURE)
    mapping = blocker.args[0]
    assert mapping.entries

    # 2. Review: keep one value real, rename another, add a missed one
    from penname.gui.models import ReviewModel

    model = ReviewModel()
    model.load_mapping(mapping)
    rows = model.rows()
    rows[0] = replace(rows[0], replace_it=False)
    flow.apply_review(rows)
    flow.add_custom_value("Director of Development")
    refreshed = flow.rescan()
    kept = rows[0].original
    assert all(e.original != kept for e in refreshed.entries)
    assert any(e.original == "Director of Development" for e in refreshed.entries)

    # 3. Export: pen-named copy + encrypted mapping + markdown
    dest = tmp_path / "letter.pen.txt"
    mapping_path, markdown_path = flow.export(dest, also_markdown=True)
    assert dest.exists() and mapping_path.exists() and markdown_path.exists()
    exported = dest.read_text(encoding="utf-8")
    assert "Director of Development" not in exported
    assert kept in exported  # the value the user chose to keep

    # 4. Reverse: an "LLM reply" quoting the pen-named text is fully restored
    restored_path = tmp_path / "restored.txt"
    count = flow.reverse_to_file(exported, mapping_path, restored_path)
    assert count > 0
    assert restored_path.read_bytes() == FIXTURE.read_bytes()


def test_scan_failure_is_reported_plainly(qtbot) -> None:
    flow = DocumentFlow()
    with qtbot.waitSignal(flow.scan_failed, timeout=120_000) as blocker:
        flow.open_document(Path("/nonexistent/nope.txt"))
    assert blocker.args[0]
