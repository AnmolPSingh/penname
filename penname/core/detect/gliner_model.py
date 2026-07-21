"""Locate and fetch the bundled GLiNER model.

Runtime resolution is local-only (rule 1). Fetching happens at build/dev time
via ``python -m penname.core.detect.gliner_model`` and is the *only* place a
download occurs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from penname.core.detect.gliner_detector import DEFAULT_MODEL

_ENV_OVERRIDE = "PENNAME_GLINER_MODEL"
_BUNDLE_DIRNAME = "gliner_model"


def _frozen_model_dir() -> Path | None:
    """Inside a PyInstaller bundle, the model ships next to the app."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        return None
    candidate = Path(base) / _BUNDLE_DIRNAME
    return candidate if candidate.is_dir() else None


def resolve_model_path() -> str | None:
    """Return a local path/id the GLiNER loader can use offline, or None if no
    local model is available. Never triggers a download."""
    override = os.environ.get(_ENV_OVERRIDE)
    if override and Path(override).is_dir():
        return override

    frozen = _frozen_model_dir()
    if frozen is not None:
        return str(frozen)

    # Dev/CI: rely on the local Hugging Face cache populated by the fetch step.
    # huggingface_hub ships with GLiNER; if it is absent, no local model exists.
    try:
        from huggingface_hub import try_to_load_from_cache
    except ImportError:
        return None

    cached = try_to_load_from_cache(DEFAULT_MODEL, "gliner_config.json")
    if isinstance(cached, str):
        return DEFAULT_MODEL  # present in the cache; from_pretrained loads offline
    return None


def fetch_model(dest: str | None = None) -> str:
    """Download the model for bundling. Build/dev time only."""
    from gliner import GLiNER

    model = GLiNER.from_pretrained(DEFAULT_MODEL)  # network allowed here
    if dest:
        model.save_pretrained(dest)
        return dest
    return DEFAULT_MODEL


def main() -> int:
    dest = sys.argv[1] if len(sys.argv) > 1 else None
    where = fetch_model(dest)
    print(f"GLiNER model ready: {where}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
