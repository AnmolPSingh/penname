"""Qt environment repair for macOS.

On some macOS setups the bundled Qt platform plugins carry extended
attributes (com.apple.provenance) that make Qt's own directory iterator skip
them: POSIX listing sees the files, Qt sees an empty directory, and the app
aborts with "could not find the Qt platform plugin". When that happens, copy
the platform plugins (program code only — never user data) to the system
temp dir *without* metadata and point Qt at the copy. No-op everywhere else.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


def ensure_qt_plugins_reachable() -> None:
    if os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"):
        return
    from PySide6.QtCore import QDir, QLibraryInfo

    platforms = Path(QLibraryInfo.path(QLibraryInfo.PluginsPath)) / "platforms"
    if not platforms.is_dir():
        return
    if len(QDir(str(platforms)).entryList()) > 2:  # more than '.' and '..'
        return
    target = Path(tempfile.mkdtemp(prefix="penname-qt-")) / "platforms"
    # shutil.copy (not copy2): preserving xattrs would re-hide the plugins.
    shutil.copytree(platforms, target, copy_function=shutil.copy)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(target)
