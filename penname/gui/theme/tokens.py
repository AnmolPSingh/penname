"""Design tokens from DESIGN.md — the single source of truth for the GUI.

Palette, radii, density and restraint follow DESIGN.md exactly. Type sizes are
lifted one step from the spec's compact web scale (14px UI labels -> 15/16px)
and hit targets are floored at 44px: the audience is older, non-technical
fundraisers, and legibility wins where the two documents disagree. Everything
else — the 900px centred column, 32px section rhythm, 16px card padding, 8px
element gap, 400/500 weights, one teal — is the spec as written.
"""

# Colors (DESIGN.md "Tokens — Colors")
PARCHMENT = "#faf8f5"  # page canvas
SOFT_PAPER = "#fdfbfa"  # card surface, one step above the canvas
WARM_MIST = "#d1d1cd"  # hairline borders
ASH = "#92918b"  # muted helper text
GRAPHITE = "#72706b"  # secondary text, inactive labels
INK = "#27251e"  # primary text, filled buttons
DEEP_TEAL = "#016a71"  # the single accent: active nav, selected, badges
WHITE = "#ffffff"  # text on teal/ink fills only — never a surface

# Sidebar sits a touch off the canvas, per DESIGN.md's "slightly darker
# parchment tone with subtle separation".
SIDEBAR_BG = "#f6f3ef"

# Typography — Inter substitute for pplxSans; weights capped at 500
FONT_FAMILY = '"Inter", "SF Pro Text", -apple-system, "Segoe UI", sans-serif'
TEXT_BADGE = 11
TEXT_MICRO = 12
TEXT_LABEL = 15
TEXT_BODY = 16
TEXT_HEADING = 24
WEIGHT_REGULAR = 400
WEIGHT_MEDIUM = 500

# Spacing (4px base) — DESIGN.md scale
SPACE_4 = 4
SPACE_8 = 8  # element gap
SPACE_12 = 12
SPACE_16 = 16  # card padding
SPACE_24 = 24
SPACE_32 = 32  # section gap

# Shapes — DESIGN.md radii
RADIUS_CARD = 16
RADIUS_INPUT = 12
RADIUS_BUTTON = 6
RADIUS_NAV = 12
RADIUS_PILL = 999

# Layout — DESIGN.md: fixed sidebar + centred column capped at 900px
SIDEBAR_WIDTH = 260
CONTENT_MAX_WIDTH = 900

# Accessibility floor: every interactive control is at least this tall
HIT_TARGET = 44
ROW_HEIGHT = 52  # review-table rows, comfortable for older eyes
