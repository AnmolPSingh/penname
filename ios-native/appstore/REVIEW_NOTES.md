# App Store Connect — answers and review notes

Paste-ready text for the parts of App Store Connect that are not in
APP_METADATA.md. `[CONFIRM]` marks details only you can supply.

## App Review Information

**Sign-in required:** No. The app has no accounts.

**Contact:** [CONFIRM: name, phone, email of the person Apple should contact]

**Notes for the reviewer** (paste into "Notes"):

> Penname is an offline utility for nonprofit staff. It replaces private
> details in a document with realistic stand-ins before the user pastes the
> document into an AI assistant, then restores the real details in the
> assistant's reply. It needs no account and makes no network connections.
>
> To try it:
> 1. Protect tab: paste this sample and tap "Find private details".
>    Dear Margaret Wilson, thank you for your gift of £2,500 on 5 January
>    2024. We will write to margaret@example.org or call 020 7946 0958.
> 2. Review the list, then tap "Create the safe copy".
> 3. Under "The key file", enter a passphrase twice (8+ characters) and tap
>    "Save key file". Choose "Save to Files" in the share sheet.
> 4. Tap "Copy safe copy". Open the Restore tab and paste it into "Your
>    assistant's reply".
> 5. Tap "Choose .pnmap file", pick the file saved in step 3, enter the
>    passphrase and tap "Bring the real details back". The original text
>    returns, with each restored detail highlighted.
>
> All processing is on the device: detection, replacement, AES-256-GCM
> encryption of the key file (WebCrypto), and an encrypted, metadata-only
> activity log. The interface is built with web technology inside a native
> shell; the app's function (document processing, on-device encryption, file
> export through the share sheet, an activity log) is not a website and is
> not available at any URL.

## App Privacy ("nutrition label")

- **Do you or your third-party partners collect data from this app?** No.
- Result shown on the store: **Data Not Collected**.

This matches `PrivacyInfo.xcprivacy`: no tracking, no tracking domains, no
collected data types; UserDefaults declared with reason CA92.1.

## Export compliance

- **Does your app use encryption?** Yes.
- **Does it qualify for an exemption?** Yes — it uses only standard
  encryption provided by the operating system (AES-GCM and PBKDF2 through
  WebCrypto) to protect the user's own data.
- `ITSAppUsesNonExemptEncryption` is `false` in Info.plist, so App Store
  Connect will not ask on each upload.

## Age rating

All content questions: None. No web access, no user-generated content shared
with others, no gambling, no contests. Expected rating: 4+.

## Pricing and availability

- Price: Free. No in-app purchases.
- [CONFIRM: countries — all, or UK/EU/US only at first]

## Content rights

The app contains no third-party content. Fonts (Urbanist, IBM Plex Mono) are
bundled under the SIL Open Font License.

## Screenshots to upload

Ready in `ios-native/appstore/screenshots/`, taken from build 2 on the
simulators with a sample donor letter (all names and details are invented):

- `iphone-6.9/` — 1320 × 2868, for the iPhone 6.9" slot
- `ipad-13/` — 2064 × 2752, for the iPad 13" slot

Five in each, in this order: 01 Protect, 02 Review list, 03 Safe copy and
key file, 04 Restore with highlights, 05 How it works.

## Likely review questions

- **Guideline 4.2 (minimum functionality).** The reviewer notes above
  explain that this is an offline tool, not a wrapped website. If asked,
  point to on-device encryption, file export and the activity log.
- **Guideline 5.1.1 (privacy).** The privacy policy URL must describe the
  app, not only the website — see WEBSITE_TEXT.md.
- **Guideline 2.3 (accurate metadata).** The description says the app does
  not make an organisation GDPR compliant; keep that sentence.
