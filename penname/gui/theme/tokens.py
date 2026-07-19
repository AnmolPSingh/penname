"""Design tokens from DESIGN.md — the single source of truth for the GUI.

Palette, radii, and restraint follow DESIGN.md exactly. Type sizes and hit
targets are deliberately scaled up from its compact web scale: the audience is
older, non-technical users, and accessibility wins where the documents differ.
"""

# Colors (DESIGN.md "Tokens — Colors")
PARCHMENT = "#faf8f5"  # page canvas
SOFT_PAPER = "#fdfbfa"  # elevated card surface
WARM_MIST = "#d1d1cd"  # hairline borders
ASH = "#92918b"  # muted helper text
GRAPHITE = "#72706b"  # secondary text, inactive labels
INK = "#27251e"  # primary text, filled buttons
DEEP_TEAL = "#016a71"  # the single accent: active/selected states, badges
WHITE = "#ffffff"  # text on teal/ink fills only — never a surface

# Typography — Inter substitute per DESIGN.md; weights capped at 500
FONT_FAMILY = '"Inter", "Segoe UI", "Helvetica Neue", sans-serif'
TEXT_BODY = 16  # px (scaled up from DESIGN.md's 14 for readability)
TEXT_BODY_LG = 18
TEXT_HEADING = 26
TEXT_CAPTION = 13
WEIGHT_REGULAR = 400
WEIGHT_MEDIUM = 500

# Spacing (4px base unit) and shapes
SPACE_4 = 4
SPACE_8 = 8
SPACE_12 = 12
SPACE_16 = 16
SPACE_24 = 24
SPACE_32 = 32
RADIUS_CARD = 16
RADIUS_INPUT = 12
RADIUS_BUTTON = 6
SIDEBAR_WIDTH = 240
CONTENT_MAX_WIDTH = 900

# Accessibility floor: every interactive control is at least this tall
HIT_TARGET = 44
