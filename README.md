# Penname

**Give sensitive values in your donor documents a pen name before you share them with an AI assistant — then take the pen names off afterwards.**

Penname is a free, open-source tool for fundraisers and nonprofit teams. It runs
entirely on your own computer. Nothing you open in Penname ever leaves your machine —
no internet connection is used, ever.

## What it does

1. **Open a document** (CSV, Excel, Word, plain text, or PDF). Penname finds
   names, organizations, amounts, addresses, and other sensitive values. For a
   PDF, Penname reads the text and hands you a Markdown copy (scanned/image-only
   PDFs aren't supported yet).
2. **Review the list.** You decide what gets a pen name. Add anything Penname
   missed, remove anything it got wrong, and edit any pen name you like.
   **This review step matters — no tool catches everything.**
3. **Export and share.** Save a copy where every sensitive value has been swapped
   for a realistic pen name, and paste *that* into your AI assistant.
4. **Take the pen names off.** Paste the assistant's response back into Penname,
   and it restores the real values and saves the result as a file on your computer.

## What Penname does *not* do

Penname **pseudonymizes** your documents — it reduces the personal data you share.
It does **not** make data anonymous, and it will not catch every sensitive value.
Under UK/EU GDPR, pseudonymized data is still personal data.
**Always review before sending.**

## Privacy promises

- **No network calls, ever.** No telemetry, no update checks, no cloud processing.
  All language models ship inside the app.
- **Your mapping file is encrypted.** The file that links pen names back to real
  values is encrypted (AES-256-GCM) with a key kept in your operating system's
  keychain. It is never written to disk unprotected.

## Installing the app

Download the file for your computer from the latest
[release](../../releases): `Penname-macos.zip` or `Penname-windows.zip`.

Penname is a free project with no budget for the code-signing certificates that
stop the operating system from warning about new apps. The app is safe — you can
verify it yourself (see "Verifying your download" below) — but you will see a
warning the first time you open it. Here is how to get past it:

**macOS.** Unzip, drag `Penname.app` to your Applications folder. The first time,
**right-click the app and choose "Open"**, then click "Open" in the dialog.
(Double-clicking shows a warning with no easy way through; right-click → Open
does not.) You only need to do this once.

**Windows.** Unzip the folder and run `Penname.exe`. Windows SmartScreen may say
"Windows protected your PC" — click **"More info"**, then **"Run anyway"**.

### Verifying your download

Every release lists a **SHA-256 checksum** next to each file and a **build
provenance attestation** proving the file was built by this repository's release
workflow. To check the file you downloaded matches:

```bash
# macOS
shasum -a 256 Penname-macos.zip
# Windows (PowerShell)
Get-FileHash Penname-windows.zip -Algorithm SHA256
```

Compare the result to the `.sha256` file published with the release.

## For developers

```bash
uv sync          # install dependencies (Python 3.11+)
uv run pytest    # run the test suite — round-trip integrity is the gate
uv run penname pseudonymize letter.txt -o letter.pen.txt --mapping letter.pnmap
uv run penname reverse response.txt --mapping letter.pnmap -o restored.txt
```

> If your project folder path contains a space, `uv`'s editable install writes a
> `.pth` the interpreter skips, so the `penname` command may report
> "No module named 'penname'". Run `uv run python -m penname …` instead, or
> clone to a path without spaces. Installed releases and CI are unaffected.

### Building the desktop app

```bash
bash packaging/build_app.sh    # macOS/Linux: builds dist/, prints the SHA-256
```

The build bundles the spaCy model, Presidio, and the CRM templates so the app
runs fully offline. Releases for macOS and Windows are built automatically by
`.github/workflows/release.yml` on every `v*` tag, with checksums and provenance.

### Optional MCP server (off by default)

Penname ships an MCP server so a local AI agent can pseudonymize documents and
take pen names off replies. It is **disabled by default** — turn it on
explicitly:

```bash
python -m penname.mcp.config enable    # opt in (writes ~/.penname/settings.json)
penname-mcp                            # starts the server over stdio
```

It exposes two tools: `pseudonymize_document` (returns file paths and counts,
never raw content) and `reverse_to_file` (writes the restored text to a local
file and returns **only** a success flag and the path — restored donor data is
never returned into the model's context).

Licensed under Apache-2.0.
