#!/usr/bin/env bash
# Build the Penname desktop app locally (macOS / Linux) and print its checksum.
# Windows builds run through the GitHub Actions release workflow.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Building Penname with PyInstaller…"
uv run pyinstaller packaging/penname.spec --noconfirm --distpath dist --workpath build

if [[ "$(uname)" == "Darwin" ]]; then
    APP="dist/Penname.app"
    # Strip extended attributes (e.g. com.apple.provenance) that make Gatekeeper
    # reject the bundle as "damaged", then ad-hoc sign the cleaned bundle.
    xattr -cr "$APP"
    codesign --force --deep --sign - "$APP" || \
        echo "note: ad-hoc signing skipped (unsigned build — see README)."
    ( cd dist && zip -q -r Penname-macos.zip Penname.app )
    ARTIFACT="dist/Penname-macos.zip"
else
    ( cd dist && zip -qr Penname-linux.zip Penname )
    ARTIFACT="dist/Penname-linux.zip"
fi

echo "Built: $ARTIFACT"
if command -v shasum >/dev/null; then
    shasum -a 256 "$ARTIFACT"
else
    sha256sum "$ARTIFACT"
fi
