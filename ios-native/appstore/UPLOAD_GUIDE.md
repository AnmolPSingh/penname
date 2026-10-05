# Getting Penname into the App Store — exact steps

Before submitting, three things are still open:
- **Run it on a simulator or device once.** Saving the key file now goes
  through the iOS share sheet ("Save to Files"); that path has been tested
  in a browser with a stubbed share sheet, not yet inside the native shell.
- **Install the iOS platform** (Xcode ▸ Settings ▸ Components). Without it
  `xcodebuild` cannot build, archive or run a simulator on this Mac.
- **Your Apple Developer Program identity** — no signing certificate exists
  on this Mac (`security find-identity` reports 0).

These steps take ~30 minutes once you have an Apple Developer account.

## 1. One-time account setup (you)
1. Enroll in the Apple Developer Program: https://developer.apple.com/programs
   ($99/year). Business accounts need a D-U-N-S number (Philanthropel Ltd).
2. On this Mac: open Xcode ▸ Settings ▸ Accounts ▸ add your Apple ID.
3. Note your **Team ID** and put it in `appstore/exportOptions.plist`.

## 2. Set the signing team on the project (once)
Open the workspace:
```
open /Users/guzel/Desktop/penname/ios-native/ios/App/App.xcworkspace
```
Select the **App** target ▸ Signing & Capabilities ▸ tick "Automatically
manage signing" ▸ choose your team ▸ do the same for the Release row.
Xcode then creates the App Store provisioning profile automatically.

## 3. Before you submit — external prerequisites
- **Privacy policy**: https://philanthropel.com/privacy is live and has a
  Penname section.
- **Support page**: https://philanthropel.com/penname/support is live.
- **App Store Connect record**: create app "Penname" with bundle ID
  com.philanthropel.penname, fill name/subtitle/description/keywords/
  screenshots from APP_METADATA.md.

## 4. Archive and upload (pick one)
**Easiest — Xcode:**
1. Product ▸ Destination ▸ Any iOS Device (arm64)
2. Product ▸ Archive
3. In the Organizer: Distribute App ▸ App Store Connect ▸ Upload

**CLI alternative:**
```bash
cd /Users/guzel/Desktop/penname/ios-native/ios/App
xcodebuild archive -workspace App.xcworkspace -scheme App \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath ../../appstore/Penname.xcarchive
xcodebuild -exportArchive -archivePath ../../appstore/Penname.xcarchive \
  -exportOptionsPlist ../../appstore/exportOptions.plist \
  -exportPath ../../appstore
# then upload the produced .ipa via Xcode Organizer or:
xcrun altool --upload-app -f ../../appstore/*.ipa \
  -u your@apple.id -p "@keychain:AC_PASSWORD"   # or App Store Connect API key
```

## 5. Already done for you (code side)
- Bundle ID `com.philanthropel.penname`, version 1.0.0 (build 1), iOS 15+
- iPhone + iPad (TARGETED_DEVICE_FAMILY = 1,2), all iPad orientations
- App icon 1024×1024, opaque (no alpha — App Store requirement)
- `PrivacyInfo.xcprivacy` (no tracking, no data collection, UserDefaults
  CA92.1) bundled in the app — verified present in a Release build
- `ITSAppUsesNonExemptEncryption=false` (standard AES-256, data-at-rest)
- Legacy `armv7` device capability removed, `arm64` required
- LaunchScreen.storyboard present; no ATS exceptions; no permissions needed
  (no camera/location/mic — nothing to explain in the privacy report)
