"""Frozen-app entry point for the Penname desktop GUI.

A tiny wrapper so PyInstaller has a concrete script to analyze; all logic lives
in penname.gui.app.

Run with ``--self-test`` to verify the frozen bundle can detect and reverse a
value fully offline (used as the CI smoke test of the built binary). This
loads the bundled spaCy model, so it proves the model shipped correctly.
"""

import sys


def _self_test() -> int:
    from penname.core.engine import PennameSession

    sample = "Thank you, Margaret Wilson, for your $25,000 gift."
    session = PennameSession()
    result = session.pseudonymize(sample)
    restored = session.reverse(result.text, result.mapping)
    ok = restored == sample and result.text != sample and result.mapping.entries
    print("self-test:", "OK" if ok else "FAILED")
    print("  detected", len(result.mapping.entries), "value(s)")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    from penname.gui.app import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
