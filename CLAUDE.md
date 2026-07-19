# CLAUDE.md — Penname

## What this project is

**Penname** is an open-source desktop tool for the nonprofit and philanthropy sector. It gives sensitive values in donor documents a pen name — people, organizations, amounts, addresses, wealth ratings, IDs — before the user pastes the document into an LLM, then restores the real values in the LLM's response afterwards. Everything runs locally. Nothing ever leaves the user's machine.

Naming conventions: repo and product name `Penname`, Python package and CLI command `penname`, MCP server name `penname-mcp`.

Read `design.md` in the repo root before making any design or UI decision. It is the source of truth for product and design direction. If `design.md` conflicts with this file on product/UI matters, `design.md` wins. On the non-negotiable rules below, this file wins.

## Non-negotiable rules

1. **No network calls, ever.** No telemetry, no update checks, no model downloads at runtime, no analytics. All models ship bundled. If a dependency phones home, replace it. This is verifiable by users and is the core trust promise.
2. **Never use the word "anonymize" in code, UI, docs, or README.** The correct terms are "pseudonymize" and "de-identify." Under UK/EU GDPR, reversibly pseudonymized data is still personal data. Claiming anonymization is legally wrong and will destroy the project's credibility. The UI must state plainly: "Penname reduces what you share. It does not make data anonymous. Always review before sending."
3. **Detection is imperfect and the product must assume it.** Best local PII detection misses entities routinely (cross-domain F1 around 0.5 in independent benchmarks). Human review is therefore a mandatory step in the workflow, not an option. Never build a "one-click, fully automatic" path that skips review.
4. **The de-pseudonymization MCP tool must never return restored content into model context.** It writes the restored text to a local file and returns only a success flag and the file path. Returning real donor data as a tool result would send it to the model provider and defeat the entire product. This applies to any future API surface as well.
5. **Round-trip integrity is the product.** `pseudonymize(text) → reverse(result) == original` must hold byte-identical. This test exists before any feature work and runs in CI on every commit. Known risk: naive Presidio pipelines fail restoration on ~36% of documents due to span-offset misalignment. Handle offsets explicitly.
6. **The mapping file is the crown jewel.** Encrypted at rest (AES-256-GCM), key stored in the OS keychain (Keychain on macOS, Credential Manager on Windows). Never write mappings to disk in plaintext, including temp files and logs.

## Architecture

Layered. The engine knows nothing about any interface.

```
core/        pseudonymization engine — pure library, no UI imports
  detect/    Presidio analyzer + GLiNER backend + custom recognizers
  replace/   Faker-based consistent replacement, format-preserving
  mapping/   encrypted mapping store, keychain integration
  io/        format readers/writers (csv, xlsx, docx, txt, md; pdf read-only)
gui/         PySide6 desktop app — thin wrapper over core
cli/         thin wrapper over core (used for testing and power users)
mcp/         optional MCP server — thin wrapper over core, off by default
tests/       round-trip suite, format suites, sample donor fixtures
```

GUI, CLI, and MCP call the same core functions. If a feature requires logic inside a wrapper, that logic belongs in core instead.

## Stack

- Python 3.11+, PySide6 for the GUI
- Microsoft Presidio (analyzer + anonymizer modules — library name only; never surface "anonymize" in UI or docs) with GLiNER as the NER backend, bundled locally
- Faker for realistic replacements: consistent within a session/document set (same real value → same pen name), gender- and culture-plausible names, dates shifted not blanked, amounts preserving rough magnitude
- pandas/openpyxl for CSV/XLSX, python-docx for DOCX, pypdf or pdfplumber for PDF text extraction (read-only)
- PyInstaller for packaging; GitHub Actions matrix (windows-latest, macos-latest) builds both artifacts from one codebase per release
- MCP server via the official Python MCP SDK, shipped in v1 but disabled unless the user enables it in settings
- Development discipline: the Ponytail plugin (DietrichGebert/ponytail) is installed in this Claude Code environment. Honor its rules — simplest working solution, standard library first, no speculative abstractions, no unrequested features. When Ponytail's minimalism conflicts with the non-negotiable rules above (encryption, round-trip tests, review step), the non-negotiable rules win; minimalism never justifies skipping a security or integrity requirement.

## Formats

- **In:** CSV, XLSX, DOCX, TXT, MD. PDF is text-extraction only (digital PDFs; no OCR in v1 — scanned PDFs are out of scope, say so in the UI).
- **Out (pseudonymized):** same format as input where feasible (CSV→CSV, XLSX→XLSX, DOCX→DOCX), plus Markdown always available as the LLM-friendly export. PDF input always exports to Markdown; do not attempt PDF rewriting.
- **Reversal input:** arbitrary pasted text (the LLM's response), not the original file. Reversal output is a local file.
- CRM awareness: recognize common export column patterns from Raiser's Edge NXT, Salesforce NPSP, DonorPerfect, Bloomerang, Little Green Light. Column-name templates live in `core/detect/crm_templates/` as data files, not code.

## Sector-specific detection

Beyond standard PII, build custom Presidio recognizers for: donation amounts and gift histories, wealth-screening/capacity ratings, planned-giving and bequest terminology, fund/campaign/appeal codes, constituent IDs. These recognizers are Penname's differentiation; generic detection is not.

## Workflow the GUI must implement

1. Open file → engine detects entities → review screen shows every detected span, its type, and confidence, with one-click add/remove and click-to-edit replacements.
2. User confirms → export pseudonymized file (same format and/or Markdown) + encrypted mapping saved.
3. User pastes into their LLM externally, then pastes the response back into Penname's Reverse tab.
4. Penname restores real values and saves the result to a local file.

Audience is older, non-technical users: large targets, high contrast, plain language, no jargon, no CLI knowledge assumed. Follow `design.md` for specifics.

## Testing priorities (in order)

1. Round-trip byte-identity on text (first milestone; CI-gated)
2. Round-trip on CSV → XLSX → DOCX
3. Consistency: same entity → same pen name across multi-file sessions
4. Mapping encryption: assert no plaintext mapping ever touches disk
5. Detection regression suite on synthetic donor fixtures (never commit real donor data, ever, including in test fixtures or issues)
6. MCP contract test: reverse tool result contains a path and no restored content

## Build order

1. Core engine + round-trip test harness + CSV path, end to end, CLI only
2. XLSX, DOCX, TXT/MD paths
3. Review-screen GUI (PySide6) wrapping the working engine
4. Mapping encryption + keychain
5. CRM templates + sector recognizers
6. MCP server (optional toggle)
7. PDF text-extraction → Markdown
8. Packaging: PyInstaller + GitHub Actions matrix, SHA-256 checksums and build provenance attestation on releases

Do not start a later step while the earlier step's tests are red.

## Distribution constraints

Zero budget. Builds are unsigned; users will see SmartScreen/Gatekeeper warnings. The README includes an illustrated install guide addressing these warnings (maintained by the project owner). Every release publishes SHA-256 checksums and GitHub build provenance. License: Apache-2.0.

## Language rules for all user-facing text

- "Pen name" is the product metaphor: sensitive values get pen names; reversal "takes the pen name off"
- "Pseudonymize," never "anonymize"
- "Reduces the personal data you share," never "makes your data safe" or "no data leaks"
- "Review before sending" appears at every export point
- Plain English throughout; the reader is a fundraiser, not a developer
