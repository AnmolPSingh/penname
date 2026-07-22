"""Locate bundled image assets in dev and in the frozen (PyInstaller) app."""

from __future__ import annotations

import sys
from pathlib import Path


def asset_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        bundled = Path(base) / "penname" / "gui" / "assets" / name
        if bundled.exists():
            return str(bundled)
    return str(Path(__file__).parent / "assets" / name)
