# Getting Penname into the Mac App Store

The Mac app is a small native shell (Tauri) around the same Penname web app
that ships on iPhone and iPad. Store text, privacy answers and reviewer notes
are shared with iOS: see `../../ios-native/appstore/`.

## Where things stand

Verified on this Mac with a sandboxed, ad-hoc signed build:

- The app starts under the App Sandbox and loads its bundled pages.
- Protect → encrypt key file → restore returns the original text exactly.
- "Save" buttons write to the user's Downloads folder (never overwriting:
  a second file becomes `penname-key (1).pnmap`).
- No insecure-HTTP exception; `ITSAppUsesNonExemptEncryption` is `false`.

Not yet verified — needs a person at the keyboard or a real signature:

- Choosing a document and a `.pnmap` key file through the Open dialog.
- The Activity log on a properly signed build. It stores an encryption key
  through WebKit, which keeps a "Penname WebCrypto Master Key" item in the
  Keychain. Re-signed test builds trigger a Keychain prompt; a build with
  one stable signature should not. Check this on the first signed build.
- Mac screenshots.

## What you need (one-time)

1. Apple Developer Program membership (the same one covers iOS).
2. In Xcode ▸ Settings ▸ Accounts ▸ Manage Certificates, create:
   - **Apple Distribution** (signs the app)
   - **Mac Installer Distribution** (signs the .pkg)
3. At developer.apple.com ▸ Identifiers: App ID `com.philanthropel.penname`
   with the macOS platform ticked. Using the same ID as the iOS app makes
   them one listing with one purchase.
4. At developer.apple.com ▸ Profiles: a **Mac App Store** provisioning
   profile for that App ID. Save it as
   `macos/src-tauri/embedded.provisionprofile` (do not commit it).
5. In App Store Connect: add the macOS platform to the Penname app record.

## Build, sign, package, upload

Replace `TEAMID` and the certificate names with yours.

```bash
cd macos
npm run sync          # copy the web app from ../ios
npx tauri build --bundles app
```

Add your team to a copy of the entitlements (the two extra keys must match
the provisioning profile):

```xml
<key>com.apple.application-identifier</key>
<string>TEAMID.com.philanthropel.penname</string>
<key>com.apple.developer.team-identifier</key>
<string>TEAMID</string>
```

```bash
APP=src-tauri/target/release/bundle/macos/Penname.app
cp src-tauri/embedded.provisionprofile "$APP/Contents/embedded.provisionprofile"
codesign --force --deep --options runtime \
  --sign "Apple Distribution: Philanthropel Limited (TEAMID)" \
  --entitlements src-tauri/entitlements-store.plist "$APP"
productbuild --component "$APP" /Applications \
  --sign "3rd Party Mac Developer Installer: Philanthropel Limited (TEAMID)" \
  Penname.pkg
```

Upload `Penname.pkg` with the **Transporter** app (free on the Mac App
Store), then pick the build in App Store Connect and submit for review.

## Things a reviewer may ask about

- **"Outgoing connections" entitlement.** The app makes no network
  connections. A sandboxed web view cannot display even its own bundled
  files without this entitlement; without it the window is blank. The app's
  content security policy allows only its own files. Say exactly this in the
  review notes if asked.
- **Downloads folder entitlement.** Used to save the safe copy, the
  encrypted key file, restored text and the Activity CSV.
- **Apple silicon only.** The build is arm64, so the minimum system is
  macOS 12. For Intel Macs, install the `x86_64-apple-darwin` Rust target
  and build with `--target universal-apple-darwin`.

## Screenshots

Mac App Store sizes: 1280×800, 1440×900, 2560×1600 or 2880×1800. Use the
same five screens as iOS: Protect, Review list, Safe copy and key file,
Restore with highlights, Activity.
