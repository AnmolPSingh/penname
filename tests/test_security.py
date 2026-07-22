"""Security hardening: input limits, zip-bomb guard, XML hardening, MCP paths."""

import zipfile
from pathlib import Path

import pytest


# -- input size / zip-bomb guards -------------------------------------------

def test_oversized_file_is_refused(tmp_path, monkeypatch) -> None:
    from penname.core.engine import PennameSession
    from penname.core.io import dispatch, limits

    monkeypatch.setattr(limits, "MAX_FILE_BYTES", 10)  # tiny ceiling for the test
    big = tmp_path / "big.txt"
    big.write_text("x" * 100, encoding="utf-8")

    with pytest.raises(limits.InputTooLargeError):
        dispatch.pseudonymize_file(big, tmp_path / "out.txt", PennameSession())


def test_zip_bomb_xlsx_is_refused(tmp_path, monkeypatch) -> None:
    from penname.core.io import limits
    from penname.core.io.xlsx_io import pseudonymize_xlsx

    monkeypatch.setattr(limits, "MAX_UNCOMPRESSED_BYTES", 1000)
    bomb = tmp_path / "bomb.xlsx"
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/worksheets/sheet1.xml", b"A" * 100_000)  # expands hugely

    from penname.core.engine import PennameSession

    with pytest.raises(limits.InputTooLargeError):
        pseudonymize_xlsx(bomb, tmp_path / "out.xlsx", PennameSession())


def test_openpyxl_xml_is_hardened() -> None:
    """defusedxml must be active so XLSX parsing resists XXE / entity bombs."""
    import openpyxl

    assert openpyxl.DEFUSEDXML is True


# -- MCP path safety --------------------------------------------------------

@pytest.fixture(autouse=True)
def fake_keychain(monkeypatch):
    vault: dict = {}
    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda s, a: vault.get((s, a)))
    monkeypatch.setattr(keyring, "set_password", lambda s, a, v: vault.__setitem__((s, a), v))


def test_mcp_refuses_output_outside_input_folder(tmp_path) -> None:
    from penname.mcp import tools

    src = tmp_path / "work" / "letter.txt"
    src.parent.mkdir()
    src.write_text("Dear Margaret Wilson", encoding="utf-8")
    outside = tmp_path / "escape.txt"  # sibling of the work folder, not inside it

    result = tools.pseudonymize_document(str(src), output_path=str(outside))
    assert result["success"] is False
    assert "folder" in result["message"].lower()
    assert not outside.exists()


def test_mcp_refuses_silent_overwrite(tmp_path) -> None:
    from penname.mcp import tools

    src = tmp_path / "letter.txt"
    src.write_text("Dear Margaret Wilson", encoding="utf-8")
    existing = tmp_path / "letter.pen.txt"
    existing.write_text("do not clobber", encoding="utf-8")

    result = tools.pseudonymize_document(str(src), output_path=str(existing))
    assert result["success"] is False
    assert "already exists" in result["message"].lower()
    assert existing.read_text(encoding="utf-8") == "do not clobber"

    # with overwrite it proceeds
    ok = tools.pseudonymize_document(str(src), output_path=str(existing), overwrite=True)
    assert ok["success"] is True


def test_mcp_reverse_confines_output_to_mapping_folder(tmp_path) -> None:
    from penname.mcp import tools

    src = tmp_path / "work" / "letter.txt"
    src.parent.mkdir()
    src.write_text("Dear Margaret Wilson, thanks.", encoding="utf-8")
    pseudo = tools.pseudonymize_document(str(src))
    assert pseudo["success"]

    outside = tmp_path / "escape.txt"
    bad = tools.reverse_to_file("hello", pseudo["mapping_path"], str(outside))
    assert bad["success"] is False
    assert not outside.exists()
