import os

# GUI tests run headless everywhere (local runs and CI).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from penname.gui.qt_env import ensure_qt_plugins_reachable
except ImportError:  # PySide6 not installed (core-only environments)
    pass
else:
    ensure_qt_plugins_reachable()
