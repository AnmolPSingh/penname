#!/bin/bash
# Build, sign and package Penname for the Mac App Store.
#
#   ./appstore/build-store.sh            signed installer in appstore/export/
#   ./appstore/build-store.sh --upload   also upload it to App Store Connect
#
# The Tauri app is not an Xcode project, so the built .app is wrapped in an
# Xcode archive and handed to `xcodebuild -exportArchive`. Xcode then signs
# it with the team's cloud-managed Apple Distribution certificate, embeds a
# Mac App Store provisioning profile, and signs the installer — no local
# certificates needed. Requires the team's Apple ID in Xcode ▸ Settings ▸
# Accounts.
set -euo pipefail
cd "$(dirname "$0")/.."

TEAM_ID="W4UQ5ADN4D"
BUNDLE_ID="com.philanthropel.penname"
APP="src-tauri/target/release/bundle/macos/Penname.app"
ARCHIVE="appstore/Penname-mac.xcarchive"
DESTINATION="export"
[ "${1:-}" = "--upload" ] && DESTINATION="upload"

npm run sync
CARGO_NET_OFFLINE=true ./node_modules/.bin/tauri build --bundles app

# Ad-hoc sign with the sandbox entitlements: the export step keeps the
# entitlements it finds on the app and adds the team identifiers.
codesign --force --deep --sign - --entitlements src-tauri/entitlements.plist "$APP"

VERSION=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APP/Contents/Info.plist")
BUILD=$(/usr/libexec/PlistBuddy -c "Print :CFBundleVersion" "$APP/Contents/Info.plist")

rm -rf "$ARCHIVE" appstore/export
mkdir -p "$ARCHIVE/Products/Applications"
cp -R "$APP" "$ARCHIVE/Products/Applications/"
cat > "$ARCHIVE/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>ApplicationProperties</key>
	<dict>
		<key>ApplicationPath</key><string>Applications/Penname.app</string>
		<key>Architectures</key><array><string>arm64</string></array>
		<key>CFBundleIdentifier</key><string>$BUNDLE_ID</string>
		<key>CFBundleShortVersionString</key><string>$VERSION</string>
		<key>CFBundleVersion</key><string>$BUILD</string>
		<key>SigningIdentity</key><string>-</string>
		<key>Team</key><string>$TEAM_ID</string>
	</dict>
	<key>ArchiveVersion</key><integer>2</integer>
	<key>CreationDate</key><date>$(date -u +%Y-%m-%dT%H:%M:%SZ)</date>
	<key>Name</key><string>Penname</string>
	<key>SchemeName</key><string>Penname</string>
</dict>
</plist>
PLIST

OPTIONS="$(mktemp -d)/exportOptions.plist"
sed "s#<string>export</string>#<string>$DESTINATION</string>#" appstore/exportOptions.plist > "$OPTIONS"
xcodebuild -exportArchive -archivePath "$ARCHIVE" -exportOptionsPlist "$OPTIONS" \
  -exportPath appstore/export -allowProvisioningUpdates
echo "Done: version $VERSION ($BUILD), destination: $DESTINATION"
