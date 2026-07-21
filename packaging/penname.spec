# PyInstaller spec for Penname — builds the desktop GUI as a one-folder app.
#
# Everything the app needs is bundled so it runs fully offline with no runtime
# downloads (non-negotiable rule 1): the spaCy model, Presidio's analyzer data,
# our CRM templates, and PySide6. Build with:
#
#     uv run pyinstaller packaging/penname.spec --noconfirm
#
# Produces dist/Penname/ (a self-contained folder). Unsigned — users will see
# Gatekeeper/SmartScreen warnings; the README documents how to open it.

import os

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_submodules,
)

# The project root (parent of this spec's packaging/ dir), so PyInstaller finds
# the penname source directly and does not depend on the editable install.
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

datas = []
binaries = []
hiddenimports = []

# Bundle the large dependencies whole (code + data files + submodules).
for package in ("en_core_web_lg", "presidio_analyzer", "spacy", "thinc", "faker"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Collect the whole penname package explicitly: the entry point imports it
# lazily (inside functions), which PyInstaller's static analysis would miss.
hiddenimports += collect_submodules("penname")

# Our own data files that live beside the code (CRM column templates).
datas += collect_data_files("penname", includes=["**/*.json"])

block_cipher = None

a = Analysis(
    [os.path.join(SPECPATH, "entry_gui.py")],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "fpdf"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Penname",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI app, no terminal window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Penname",
)

# On macOS, wrap the folder as a .app bundle.
app = BUNDLE(
    coll,
    name="Penname.app",
    icon=None,
    bundle_identifier="org.penname.desktop",
    info_plist={
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.productivity",
    },
)
