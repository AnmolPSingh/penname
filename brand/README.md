# Penname — brand assets

The mark is a **fountain-pen nib** (writing → *pen*) above a **deep-teal
signature swash** (signing → *name*). The wordmark reinforces it: **Pen** in ink,
**name** in teal — the name itself is part of the logo.

It's built from the product's design language (see `../DESIGN.md`): warm
parchment, ink text, a single deep-teal accent, flat and restrained.

## Files

| File | Use it for |
|------|------------|
| `penname-logo.svg` | Primary horizontal lockup (mark + wordmark). Docs, site headers, README. |
| `penname-mark.svg` | The mark on its own — transparent background, sits on any colour. |
| `penname-icon.svg` | App-icon form (mark on a parchment rounded square). Favicons, app tiles. |
| `penname-logo-mono.svg` | Single-colour version for stamps, embossing, one-colour print. Set `color` on the parent, or edit the fill. |
| `*.png` | Ready-to-use raster exports, regenerated from the SVGs (see below). |

The SVGs are the source of truth — edit those, then re-export the PNGs.

## Colours (from `DESIGN.md`)

| Token | Hex | Where |
|-------|-----|-------|
| Ink | `#27251E` | The nib, "Pen" |
| Deep Teal | `#016A71` | Signature swash, "name" — the single accent |
| Parchment | `#FAF8F5` | Icon background |
| Warm Mist | `#D1D1CD` | Icon hairline border |

Use **one** teal accent only. Don't introduce new colours.

## Usage

- **Clear space:** keep space equal to the nib's width on all sides.
- **Minimum size:** the mark stays legible down to ~24 px; below that, drop the
  signature swash if it muddies.
- **Do:** place on parchment, white, or a dark ink field (use the mono version in
  parchment/white on dark).
- **Don't:** recolour the nib, add gradients or shadows, stretch it, or set the
  wordmark in a different typeface.

## Typeface

The wordmark is set in **Inter** (Medium/SemiBold), matching the app. For
production exports, **outline the text** so it renders identically everywhere
(the `.svg` currently references the font by name and falls back to a system
sans where Inter isn't installed).

## Regenerating the PNGs

The PNGs are rendered from the SVGs. Any SVG renderer works (Inkscape,
`rsvg-convert`, `cairosvg`, or a browser "export"). Keep the same file names so
the README keeps working.
