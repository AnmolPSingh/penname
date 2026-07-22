"""MCP server contract tests.

The load-bearing rule (CLAUDE.md #4): the reverse tool must NEVER return
restored content into model context — only a success flag and the file path.
The server is also off by default until the user enables it.
"""

from pathlib import Path

import pytest


# -- off by default ---------------------------------------------------------

def test_mcp_disabled_by_default(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PENNAME_CONFIG_DIR", str(tmp_path))
    from penname.mcp import config

    assert config.is_enabled() is False


def test_mcp_enable_then_disable(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PENNAME_CONFIG_DIR", str(tmp_path))
    from penname.mcp import config

    config.set_enabled(True)
    assert config.is_enabled() is True
    config.set_enabled(False)
    assert config.is_enabled() is False


# -- tool logic (thin wrapper over core) ------------------------------------

@pytest.fixture(autouse=True)
def fake_keychain(monkeypatch):
    vault: dict[tuple[str, str], str] = {}
    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda s, a: vault.get((s, a)))
    monkeypatch.setattr(
        keyring, "set_password", lambda s, a, v: vault.__setitem__((s, a), v)
    )


def test_pseudonymize_document_returns_paths_and_counts(tmp_path) -> None:
    from penname.mcp import tools

    source = tmp_path / "letter.txt"
    source.write_text(
        "Dear Margaret Wilson, thank you for your $25,000 gift.", encoding="utf-8"
    )

    result = tools.pseudonymize_document(str(source))

    assert Path(result["pseudonymized_path"]).exists()
    assert Path(result["mapping_path"]).exists()
    assert result["replaced_count"] >= 1
    # counts by type support review without dumping raw donor values
    assert isinstance(result["counts_by_type"], dict)
    assert result["review_required"] is True
    # the pen-named file no longer contains the real donor name
    assert "Margaret Wilson" not in Path(result["pseudonymized_path"]).read_text(
        encoding="utf-8"
    )


def test_reverse_returns_path_and_no_restored_content(tmp_path) -> None:
    from penname.mcp import tools

    source = tmp_path / "letter.txt"
    original = "Dear Margaret Wilson, thank you for your gift."
    source.write_text(original, encoding="utf-8")
    pseudo = tools.pseudonymize_document(str(source))
    pen_text = Path(pseudo["pseudonymized_path"]).read_text(encoding="utf-8")

    dest = tmp_path / "restored.txt"
    result = tools.reverse_to_file(pen_text, pseudo["mapping_path"], str(dest))

    # The result carries a path and a success flag — never the restored text.
    assert result["success"] is True
    assert result["restored_path"] == str(dest)
    serialized = repr(result)
    assert "Margaret Wilson" not in serialized
    assert original not in serialized
    for value in result.values():
        assert "Margaret Wilson" not in str(value)

    # The restoration really happened — on disk, not in the tool result.
    assert dest.read_text(encoding="utf-8") == original
    assert result["restored_count"] >= 1


def test_reverse_reports_bad_mapping_without_crashing(tmp_path) -> None:
    from penname.mcp import tools

    dest = tmp_path / "out.txt"
    result = tools.reverse_to_file("some text", str(tmp_path / "nope.pnmap"), str(dest))
    assert result["success"] is False
    assert "message" in result
    assert not dest.exists()


def test_server_builds_and_registers_tools() -> None:
    from penname.mcp.server import build_server

    server = build_server(require_enabled=False)
    assert server is not None


def test_server_refuses_to_build_when_disabled(tmp_path, monkeypatch) -> None:
    """The off-by-default gate is structural: building the server while the
    feature is off raises, so no caller can bypass main()'s check."""
    monkeypatch.setenv("PENNAME_CONFIG_DIR", str(tmp_path))
    from penname.mcp.server import MCPDisabledError, build_server

    with pytest.raises(MCPDisabledError):
        build_server()


def test_reverse_with_unexpected_error_returns_generic_message(tmp_path, monkeypatch) -> None:
    """A non-allowlisted exception must fail safely with a generic message,
    never echoing its content into the tool result (protects rule 4)."""
    from penname.mcp import tools

    def boom(*_a, **_k):
        raise RuntimeError("SECRET Margaret Wilson leaked in exception text")

    monkeypatch.setattr(tools.MappingStore, "load", boom)
    mapping = tmp_path / "m.pnmap"  # same folder as the output, so the path check passes
    dest = tmp_path / "out.txt"

    result = tools.reverse_to_file("text", str(mapping), str(dest))

    assert result["success"] is False
    assert result["message"] == "An internal error occurred."
    assert "Margaret Wilson" not in repr(result)
    assert not dest.exists()


def test_pseudonymize_roundtrip_failure_is_handled(tmp_path, monkeypatch) -> None:
    """RoundTripError (an expected event) is caught, not propagated as a crash."""
    from penname.core.engine import RoundTripError
    from penname.mcp import tools

    source = tmp_path / "letter.txt"
    source.write_text("Margaret Wilson", encoding="utf-8")

    def boom(*_a, **_k):
        raise RoundTripError("a value could not be pseudonymized reversibly")

    monkeypatch.setattr(tools, "pseudonymize_file", boom)

    result = tools.pseudonymize_document(str(source))
    assert result["success"] is False
    assert "reversibl" in result["message"]
