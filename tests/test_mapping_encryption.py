"""The mapping file is the crown jewel: no plaintext ever touches disk."""

import secrets
from pathlib import Path

import pytest

from penname.core.mapping.store import MappingStore
from penname.core.types import Mapping, MappingEntry

ORIGINALS = ["Margaret Wilson", "s.chen@riversidecf.org", "(415) 555-0123"]


def _mapping() -> Mapping:
    return Mapping(
        entries=(
            MappingEntry(ORIGINALS[0], "Dorothy Fields", "PERSON"),
            MappingEntry(ORIGINALS[1], "j.miller@example.org", "EMAIL_ADDRESS"),
            MappingEntry(ORIGINALS[2], "(202) 555-0876", "PHONE_NUMBER"),
        )
    )


def test_saved_mapping_contains_no_plaintext(tmp_path: Path) -> None:
    store = MappingStore(key=secrets.token_bytes(32))
    target = tmp_path / "letter.pnmap"

    store.save(_mapping(), target)

    blob = target.read_bytes()
    for original in ORIGINALS:
        assert original.encode("utf-8") not in blob
    assert b"pen_name" not in blob  # not even the JSON structure is visible


def test_save_load_round_trip(tmp_path: Path) -> None:
    key = secrets.token_bytes(32)
    target = tmp_path / "letter.pnmap"
    mapping = _mapping()

    MappingStore(key=key).save(mapping, target)
    loaded = MappingStore(key=key).load(target)

    assert loaded == mapping


def test_wrong_key_fails_loudly(tmp_path: Path) -> None:
    target = tmp_path / "letter.pnmap"
    MappingStore(key=secrets.token_bytes(32)).save(_mapping(), target)

    with pytest.raises(Exception):
        MappingStore(key=secrets.token_bytes(32)).load(target)


def test_corrupted_file_fails_loudly(tmp_path: Path) -> None:
    key = secrets.token_bytes(32)
    target = tmp_path / "letter.pnmap"
    MappingStore(key=key).save(_mapping(), target)

    blob = bytearray(target.read_bytes())
    blob[-1] ^= 0xFF
    target.write_bytes(bytes(blob))

    with pytest.raises(Exception):
        MappingStore(key=key).load(target)


def test_default_key_comes_from_keychain(monkeypatch, tmp_path: Path) -> None:
    """Without an explicit key, the store creates/reuses one via the OS keychain."""
    vault: dict[tuple[str, str], str] = {}

    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda s, a: vault.get((s, a)))
    monkeypatch.setattr(
        keyring, "set_password", lambda s, a, v: vault.__setitem__((s, a), v)
    )

    target = tmp_path / "letter.pnmap"
    MappingStore().save(_mapping(), target)

    assert len(vault) == 1  # a key was created in the keychain
    loaded = MappingStore().load(target)  # and a fresh store finds the same key
    assert loaded == _mapping()
    assert len(vault) == 1  # reused, not recreated


def test_guard_refuses_insecure_keyring_backends() -> None:
    """Rule 6: the mapping key must live in a real OS keychain.

    This is the control that stops Penname writing an encryption key into a
    plaintext file when no keychain exists. It had no coverage until the CI
    matrix failed on it, so it is pinned here.
    """
    import keyring
    import keyring.backends.fail
    import pytest

    from penname.core.mapping.keychain import KeychainError, get_or_create_key

    previous = keyring.get_keyring()
    try:
        keyring.set_keyring(keyring.backends.fail.Keyring())
        with pytest.raises(KeychainError, match="no secure keychain"):
            get_or_create_key()
    finally:
        keyring.set_keyring(previous)
