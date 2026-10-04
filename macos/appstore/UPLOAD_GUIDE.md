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
- App Review. Version 1.0.0 was uploaded and passed Apple's upload checks;
  it has not been reviewed.

## What you need (one-time)

1. The Philanthropel Limited team in Xcode ▸ Settings ▸ Accounts (Admin role).
2. In App Store Connect: the macOS platform on the Penname app record.

No certificates or profiles need creating by hand. Xcode registers the app
ID and uses cloud-managed certificates on first export.

## Build, sign, package, upload

```bash
cd macos
./appstore/build-store.sh            # signed Penname.pkg in appstore/export/
./appstore/build-store.sh --upload   # also uploads to App Store Connect
```

The script builds the app, wraps it in an Xcode archive and lets
`xcodebuild -exportArchive` sign it: the app with "Apple Distribution", the
installer with "3rd Party Mac Developer Installer", with a Mac App Store
profile embedded. Each upload needs a new build number: set
`bundle.macOS.bundleVersion` in `src-tauri/tauri.conf.json` (or raise the
version) before uploading again.

The export prints a warning that no dSYM was found. That only affects how
readable crash reports are.

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

Ready in `macos/appstore/screenshots/`: five at 2880 × 1800, in upload
order (Protect, Review list, Safe copy and key file, Restore with
highlights, How it works). They were rendered from the app's own interface
at Mac window size with a sample letter of invented details; they show the
window's contents without the title bar.
