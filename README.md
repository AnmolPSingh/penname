# Penname

**Give sensitive values in your donor documents a pen name before you share them with an AI assistant — then take the pen names off afterwards.**

Penname is a free, open-source tool for fundraisers and nonprofit teams. It runs
entirely on your own computer. Nothing you open in Penname ever leaves your machine —
no internet connection is used, ever.

## What it does

1. **Open a document** (CSV, Excel, Word, or plain text). Penname finds names,
   organizations, amounts, addresses, and other sensitive values.
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

## For developers

```bash
uv sync          # install dependencies (Python 3.11+)
uv run pytest    # run the test suite — round-trip integrity is the gate
uv run penname pseudonymize letter.txt -o letter.pen.txt --mapping letter.pnmap
uv run penname reverse response.txt --mapping letter.pnmap -o restored.txt
```

Licensed under Apache-2.0.
