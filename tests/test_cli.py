"""CLI contract: pseudonymize and reverse, plain language, no restored text on stdout."""

from pathlib import Path

import pytest

from penname.cli.main import main

FIXTURE = Path(__file__).parent / "fixtures" / "donor_letter_1.txt"
CSV_FIXTURE = Path(__file__).parent / "fixtures" / "donors.csv"


@pytest.fixture(autouse=True)
def fake_keychain(monkeypatch):
    """CLI tests must never touch the real OS keychain."""
    vault: dict[tuple[str, str], str] = {}
    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda s, a: vault.get((s, a)))
    monkeypatch.setattr(
        keyring, "set_password", lambda s, a, v: vault.__setitem__((s, a), v)
    )


def test_pseudonymize_then_reverse_text(tmp_path: Path, capsys) -> None:
    out = tmp_path / "letter.pen.txt"
    mapping_path = tmp_path / "letter.pnmap"
    restored = tmp_path / "restored.txt"

    assert main(
        ["pseudonymize", str(FIXTURE), "-o", str(out), "--mapping", str(mapping_path)]
    ) == 0
    stdout = capsys.readouterr().out
    assert "Review before sending" in stdout
    assert "pen name" in stdout.lower()
    assert out.exists() and mapping_path.exists()
    assert out.read_bytes() != FIXTURE.read_bytes()

    # Simulate pasting the pseudonymized file back as an "LLM response".
    assert main(
        ["reverse", str(out), "--mapping", str(mapping_path), "-o", str(restored)]
    ) == 0
    stdout = capsys.readouterr().out
    assert restored.read_bytes() == FIXTURE.read_bytes()
    # Restored content stays out of the terminal; only the path is announced.
    assert "Margaret Wilson" not in stdout


def test_pseudonymize_csv(tmp_path: Path) -> None:
    out = tmp_path / "donors.pen.csv"
    mapping_path = tmp_path / "donors.pnmap"

    assert main(
        ["pseudonymize", str(CSV_FIXTURE), "-o", str(out), "--mapping", str(mapping_path)]
    ) == 0
    assert out.exists()
    assert b"Margaret Wilson" not in out.read_bytes()


def test_missing_input_is_a_clear_error(tmp_path: Path, capsys) -> None:
    assert main(["pseudonymize", str(tmp_path / "nope.txt")]) == 1
    assert "could not find" in capsys.readouterr().err.lower()


def test_never_says_the_a_word(tmp_path: Path, capsys) -> None:
    """"Pseudonymize", never "anonymize" — the required disclaimer's "does not
    make data anonymous" phrasing is the only permitted use of the root."""
    out = tmp_path / "letter.pen.txt"
    main(["pseudonymize", str(FIXTURE), "-o", str(out), "--mapping", str(tmp_path / "m.pnmap")])
    captured = capsys.readouterr()
    assert "anonymiz" not in (captured.out + captured.err).lower()
