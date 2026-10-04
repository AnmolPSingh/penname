# Penname for iOS — installable web app (PWA)

A fully client-side port of the Penname engine that **installs on iPhone and iPad** via
Safari's *Add to Home Screen* — no App Store account, no developer fee, no Gatekeeper
warnings, and the same core promise: **nothing ever leaves the device.**

**UI design language:** component structure from the ["Claude" DESIGN.md](https://github.com/voltagent/awesome-design-md)
spec (`design-md/claude`) — chosen from the 73 analysed design systems — **skinned to the
official Philanthropel brand** extracted from philanthropel.com:

| Token | Value | Use |
|---|---|---|
| Emerald | `#0c3b32` | Primary buttons, active states |
| Emerald deep | `#071c18` | Ink / text · dark output panels |
| Paper | `#f7f5f1` | Canvas |
| Mist | `#f4f2ef` | Cards |
| Amber | `#f2b655` | Brand accent (reserved) |
| Teal / teal-bright | `#1e7a6b` / `#3cc2a4` | Step labels, focus, success |
| Sage | `#a8bda4` | Muted text on dark surfaces |

Type: **Urbanist** (variable 400–800) + **IBM Plex Mono** — both OFL-licensed and bundled
locally in `fonts/`, so the app still makes zero network requests. Screenshots in `screenshots/`.

```
ios/
├── index.html            App shell (3 tabs: Protect / Restore / About)
├── style.css             Brand tokens from tokens.json, iOS-native feel
├── app.js                UI logic (in-memory state only, nothing persisted)
├── engine.js             Faithful JS port of penname/core (see below)
├── sw.js                 Service worker — works fully offline
├── manifest.webmanifest  Install metadata (standalone display, icons)
├── icons/                App icons generated from brand/penname-icon.png
└── test_engine.js        Engine test suite (node test_engine.js)
```

---

## Audit summary (what this is based on)

### What's already strong in the desktop product

- **Clean layering.** GUI, CLI and MCP all sit on one engine API (`PennameSession`);
  nothing below it leaks. This port was possible precisely because the core is a
  pure, UI-free library.
- **Round-trip self-verification** (`engine.py` retries with regenerated pen names
  until `reverse(pseudonymize(text)) == text`). Ported verbatim — it is the single
  most important correctness property of the product.
- **Span-safe replacement** (applied end-to-start) and **longest-first reversal** —
  both ported exactly.
- **Crypto hygiene.** AES-256-GCM with the version byte inside the AAD, so schema
  tampering is cryptographically detected. The mobile format keeps this property.
- **Honest, plain-language compliance copy** — the "does not make you compliant"
  framing is rare and correct.

### Gaps identified (and how this release addresses them)

| # | Finding | Impact | Action taken here |
|---|---|---|---|
| 1 | **No mobile story at all** — macOS (Apple Silicon only) + Windows desktop builds. Nonprofit staff increasingly work from phones/iPads, and "paste into AI" happens on mobile. | Entire class of users excluded | This PWA: installs on iOS home screen, works offline, zero install friction |
| 2 | **Install friction on Mac** — Terminal `xattr` step, Apple Silicon only. Every step loses users. | Support burden, abandoned installs | PWA installs in two taps; no warnings, works on every device |
| 3 | **Heavy runtime deps** — spaCy `en_core_web_lg` (~590 MB model) + Presidio; GLiNER (PyTorch) can't even ship in releases. | 2 GB release ceiling, slow first launch, Intel excluded | Dependency-free detector set tuned for donor documents (emails, phones, amounts, dates, addresses, orgs, IDs, fund codes, name heuristics + noise filter). Lower recall than spaCy — mitigated by the review screen, which the product already treats as the safety net |
| 4 | **Key-loss risk** — desktop `.pnmap` key lives in the OS keychain; lose the keychain entry and the mapping is unrecoverable, with no user-chosen fallback. | Unrestorable documents | Mobile `.pnmap` (v2) is passphrase-derived (PBKDF2-SHA256, 310k iterations → AES-256-GCM). The passphrase is the recovery path — and is memorable |
| 5 | **Reversal collision risk** — `reverse_text` replaces pen names anywhere in the AI reply; a pen name that coincidentally appears in new AI text would be wrongly restored. | Edge-case data corruption | Restore now matches whole tokens for reshaped forms, never treats a stand-in followed by more digits as a match, avoids round amount stand-ins, and highlights every value it puts back so the user can check it. Reshaped forms an AI writes (first name only, surname only, upper case, reworded dates) are restored; ambiguous ones are left alone and reported |
| 6 | **Format coverage** — desktop reads .docx/.xlsx/PDF; mobile reads pasted text, .txt/.md/.csv. | Feature gap, not a blocker | Documented below; .docx/.xlsx can be added later with client-side parsers (mammoth, SheetJS) if wanted |
| 7 | **US-centric date handling** in the generator. | Non-US users get odd shifts | Port supports US, UK, ISO and numeric formats; abbreviation style preserved |

### Recommended next steps for the desktop product (out of scope here)

1. Ship a notarised macOS build (Apple Developer Program ~$99/yr removes the Terminal step entirely).
2. Add a passphrase fallback for desktop `.pnmap` v1 files (keychain + passphrase dual unlock).
3. Consider whole-word reversal matching to close gap #5.
4. Add a fuzz target for the round-trip property in CI (this port includes one — easy to mirror in pytest).

---

## What the mobile app does

The full Penname loop, on-device:

1. **Open** — paste a document or choose a `.txt` / `.md` / `.csv` file.
2. **Check the list** — every detected detail with type, confidence and an editable
   stand-in. Untick anything, search, tick/untick shown, add values Penname missed.
3. **Save & share** — the safe copy (copy / iOS share sheet / save file) plus an
   **encrypted key file (`.pnmap`)** protected by a passphrase you choose.
4. **Restore** — paste the AI reply, choose the key file, enter the passphrase, and
   the real details come back. Never shared, never persisted.

Session consistency (same real value → same pen name across documents), format-aware
generation (dates shift, amounts keep magnitude and grouping, phones keep their shape,
IDs keep their pattern) and round-trip self-verification all behave as on desktop.

### Key-file format note

Mobile `.pnmap` files use framing `PNMAP | 0x02 | salt(16) | iv(12) | AES-GCM ciphertext`
with the passphrase-derived key (PBKDF2-SHA256, 310,000 iterations). Desktop v1 files
(keychain-held key) are **not** interchangeable yet — the app detects a v1 file and says
so plainly. The mapping JSON schema inside is identical to desktop (`version: 1` entries),
so interop is a small, deliberate follow-up.

---

## Install on iPhone / iPad

The app must be served over **HTTPS** (or localhost) for the install prompt and service
worker to work — this is an iOS/Safari requirement, not a product one.

1. Open the hosted URL in **Safari** (any HTTPS host works: GitHub Pages, Netlify, Cloudflare Pages, your own server).
2. Tap the **Share** button (□↑).
3. Tap **Add to Home Screen**, then **Add**.
4. Penname now launches full-screen from its own icon, works offline, and keeps no state between sessions.

### Deploy in one minute (GitHub Pages)

```bash
# from the repo root
git add ios/
git commit -m "Add Penname for iOS (installable PWA)"
git push
# then: Settings → Pages → Deploy from branch → main → / (root), or use a subpath
```

Or any static host:

```bash
cd ios && npx netlify-cli deploy --dir . --prod    # Netlify
cd ios && npx wrangler pages deploy .              # Cloudflare Pages
```

### Run it locally right now

```bash
cd ios && python3 -m http.server 8080
# open http://localhost:8080 — install works from localhost in Safari too
```

---

## The native iOS project — already generated (`../ios-native/`)

The Capacitor native shell has been **built for you**. `ios-native/` contains a real
Xcode project with the app bundled, pods installed and the icon set:

```
ios-native/
├── capacitor.config.json   appId com.philanthropel.penname · appName Penname
├── package.json            Capacitor 8.5 + `npm run sync` to refresh web assets
├── www/                    Copy of this web app (index, engine, fonts, icons)
└── ios/App/
    ├── App.xcodeproj       ← open this in Xcode
    ├── App/App/public/     Bundled web assets (served locally by the app)
    ├── App/Assets.xcassets/AppIcon.appiconset/  Penname 1024px icon installed
    └── App/Podfile         iOS 15.0 target (Capacitor 8 requirement), pods installed
```

### To ship it (you need Xcode — it is installed on this Mac)

1. Open the workspace: `open ios-native/ios/App/App.xcworkspace`
   (first time only, if `xcodebuild` complains, run
   `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`)
2. Select the **App** target → **Signing & Capabilities** → choose your **Team**
   (your Apple Developer account) and confirm the bundle ID `com.philanthropel.penname`.
3. **Product → Archive**, then **Distribute App** → App Store Connect (or TestFlight).
4. In App Store Connect: add the privacy label — **"Data Not Collected"** (the app makes
   no network connections), screenshots from `ios/screenshots/`, and a review note saying
   all processing happens on-device.

To update the web app inside the native shell after editing `ios/`:

```bash
cd ios-native && npm run sync
```

**App Store notes:** Capacitor 8 requires **iOS 15+**. A wrapped web app must show real
functionality (guideline 4.2) — the on-device crypto, file export/share and offline
support satisfy this. Review typically passes quickly for offline utilities.

What you *don't* need Xcode for: everything in `ios/` already runs and installs via
Safari Add to Home Screen — use that while the App Store version is in review.

---
## Testing

```bash
cd ios && node test_engine.js
```

26 assertions covering: detection of every entity class, round-trip integrity,
cross-document consistency, review actions (ignore / pin / custom values), the
desktop-compatible mapping schema, encryption round-trip + wrong-passphrase rejection,
AI-reply restoration, and a **200-document fuzz** asserting the round-trip property
always holds.

---

## Privacy model

- No server, no analytics, no network calls — the service worker only caches the app's own files.
- All state lives in memory; closing the app erases everything.
- The key file is encrypted with AES-256-GCM before it is ever written to disk.
- The only data a user ever shares is the safe copy — when they choose to paste it.

*Code Apache-2.0. "Penname" and "Philanthropel" are trademarks of Philanthropel Limited. © 2026 Philanthropel Limited.*