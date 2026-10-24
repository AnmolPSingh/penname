# Getting Penname into the Mac App Store

The Mac app is a small native shell (Tauri) around the same Penname web app
that ships on iPhone and iPad. Store text, privacy answers and reviewer notes
are shared with iOS: see `../../ios-native/appstore/`.

## Where things stand

Verified on this Mac with a sandboxed, ad-hoc signed build:

- The app starts under the App Sandbox and loads its bundled pages.
- Protect → encrypt key file → restore returns the original text exactly.
- Version 1.0.0 only: "Save" buttons wrote straight to the Downloads
  folder. App Review questioned that entitlement (guideline 2.4.5(i)), so
  later builds use a Save dialog instead; see "Not yet verified".
- No insecure-HTTP exception; `ITSAppUsesNonExemptEncryption` is `false`.

Verified on the TestFlight build of 1.0.0 (6 October 2026):

- Choosing a `.pnmap` key file through the Open dialog, and the full
  protect and restore flow.
- The Activity log shows no Keychain prompt on a Mac that has never run a
  test build. WebKit keeps a "Penname WebCrypto Master Key" item in the
  Keychain; an item left by a differently signed test build does prompt,
  and deleting it (`security delete-generic-password -l "Penname WebCrypto
  Master Key"`) clears that.

Verified on a sandboxed, ad-hoc signed build of the Save-dialog version
(9 October 2026), not yet on a store-signed build:

- The Save dialog for the safe copy and the key file, and restoring with a
  key file chosen through the Open dialog.
- The Privacy policy, Help and support, and philanthropel.com links open in
  the default browser.

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
- **User-selected files (read/write).** Open dialog for a document or a key
  file; Save dialog for the safe copy, the encrypted key file, restored text
  and the Activity CSV. There is no Downloads folder entitlement after
  1.0.0.
- **Apple silicon only.** The build is arm64, so the minimum system is
  macOS 12. For Intel Macs, install the `x86_64-apple-darwin` Rust target
  and build with `--target universal-apple-darwin`.

## Screenshots

Ready in `macos/appstore/screenshots/`: five at 2880 × 1800, in upload
order (Protect, Review list, Safe copy and key file, Restore with
highlights, How it works). They were rendered from the app's own interface
at Mac window size with a sample letter of invented details; they show the
window's contents without the title bar.
