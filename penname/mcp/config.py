"""MCP server settings. Off by default — the user must opt in.

The setting lives in a small JSON file under the user's config directory so
both the desktop app and the ``penname-mcp`` command agree on it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def config_dir() -> Path:
    override = os.environ.get("PENNAME_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".penname"


def _settings_path() -> Path:
    return config_dir() / "settings.json"


def _read() -> dict:
    path = _settings_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def is_enabled() -> bool:
    """Whether the MCP server is allowed to run. Defaults to False."""
    return bool(_read().get("mcp_enabled", False))


def set_enabled(enabled: bool) -> None:
    settings = _read()
    settings["mcp_enabled"] = bool(enabled)
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """`python -m penname.mcp.config [enable|disable|status]`."""
    import sys

    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else "status"
    if command == "enable":
        set_enabled(True)
        print("Penname MCP server enabled.")
    elif command == "disable":
        set_enabled(False)
        print("Penname MCP server disabled.")
    elif command == "status":
        print("enabled" if is_enabled() else "disabled (off by default)")
    else:
        print(f"Unknown command: {command}. Use enable, disable, or status.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
