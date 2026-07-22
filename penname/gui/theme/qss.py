"""Renders the application stylesheet from tokens. No hex values elsewhere.

Follows DESIGN.md: parchment canvas, Soft Paper cards, hairline Warm Mist
borders, one teal reserved for active/selected states, weights capped at 500,
strictly flat (Qt has no box-shadow, so the spec's single 1px shadow is
expressed as the hairline border it already pairs with).
"""

from penname.gui.assets import asset_path
from penname.gui.theme import tokens as t


def build_stylesheet() -> str:
    # QSS needs forward slashes even on Windows.
    check_on = asset_path("check-on.png").replace("\\", "/")
    return f"""
QWidget {{
    background-color: {t.PARCHMENT};
    color: {t.INK};
    font-family: {t.FONT_FAMILY};
    font-size: {t.TEXT_BODY}px;
    font-weight: {t.WEIGHT_REGULAR};
}}

/* ---- typography roles ---- */
QLabel {{ background: transparent; }}
QLabel[role="heading"] {{
    font-size: {t.TEXT_HEADING}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}
QLabel[role="subhead"] {{
    color: {t.GRAPHITE};
    font-size: {t.TEXT_LABEL}px;
}}
QLabel[role="helper"] {{
    color: {t.GRAPHITE};
    font-size: {t.TEXT_MICRO}px;
}}
QLabel[role="section"] {{           /* sidebar group heading */
    color: {t.GRAPHITE};
    font-size: {t.TEXT_MICRO}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}
QLabel[role="brand"] {{
    font-size: {t.TEXT_BODY}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}
QLabel[role="cardtitle"] {{
    font-size: {t.TEXT_LABEL}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}
QLabel[role="cardbody"] {{
    color: {t.GRAPHITE};
    font-size: {t.TEXT_MICRO}px;
}}

/* ---- card: Soft Paper, 16px radius, hairline ---- */
QFrame[role="card"] {{
    background-color: {t.SOFT_PAPER};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_CARD}px;
}}
QFrame[role="card"] QLabel {{ background: transparent; }}

/* notice: a card that carries the review/disclaimer message */
QLabel[role="notice"] {{
    background-color: {t.SOFT_PAPER};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_CARD}px;
    padding: {t.SPACE_16}px;
    font-size: {t.TEXT_LABEL}px;
}}

/* ---- ghost button: low emphasis ---- */
QPushButton {{
    background: transparent;
    color: {t.GRAPHITE};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_BUTTON}px;
    padding: {t.SPACE_12}px {t.SPACE_16}px;
    font-size: {t.TEXT_LABEL}px;
    min-height: {t.HIT_TARGET - 2 * t.SPACE_12}px;
}}
QPushButton:hover {{ color: {t.INK}; background-color: {t.SOFT_PAPER}; }}
QPushButton:pressed {{ background-color: {t.WARM_MIST}; }}
QPushButton:focus {{ border: 1px solid {t.DEEP_TEAL}; }}
QPushButton:disabled {{ color: {t.WARM_MIST}; border-color: {t.WARM_MIST}; }}

/* ---- filled action button: the only filled style ---- */
QPushButton[role="primary"] {{
    background-color: {t.INK};
    color: {t.PARCHMENT};
    border: none;
    border-radius: {t.RADIUS_INPUT}px;
    padding: {t.SPACE_12}px {t.SPACE_24}px;
    font-size: {t.TEXT_LABEL}px;
    font-weight: {t.WEIGHT_MEDIUM};
    min-height: {t.HIT_TARGET - 2 * t.SPACE_12}px;
}}
QPushButton[role="primary"]:hover {{ background-color: #17150f; }}
QPushButton[role="primary"]:pressed {{ background-color: #000000; }}
QPushButton[role="primary"]:focus {{ border: 1px solid {t.DEEP_TEAL}; }}
QPushButton[role="primary"]:disabled {{ background-color: {t.WARM_MIST}; color: {t.SOFT_PAPER}; }}

/* ---- sidebar ---- */
QFrame[role="sidebar"] {{
    background-color: {t.SIDEBAR_BG};
    border: none;
    border-right: 1px solid {t.WARM_MIST};
}}
QFrame[role="sidebar"] QWidget {{ background: transparent; }}
QPushButton[role="nav"] {{
    background: transparent;
    color: {t.GRAPHITE};
    border: none;
    border-radius: {t.RADIUS_NAV}px;
    padding: {t.SPACE_12}px {t.SPACE_12}px;
    text-align: left;
    font-size: {t.TEXT_LABEL}px;
    min-height: {t.HIT_TARGET - 2 * t.SPACE_12}px;
}}
QPushButton[role="nav"]:hover {{ color: {t.INK}; background-color: {t.SOFT_PAPER}; }}
QPushButton[role="nav"]:checked {{
    background-color: {t.DEEP_TEAL};
    color: {t.WHITE};
}}
QPushButton[role="nav"]:disabled {{ color: {t.WARM_MIST}; background: transparent; }}

/* ---- inputs ---- */
QPlainTextEdit, QLineEdit {{
    background-color: {t.SOFT_PAPER};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_INPUT}px;
    padding: {t.SPACE_12}px;
    font-size: {t.TEXT_BODY}px;
    selection-background-color: {t.DEEP_TEAL};
    selection-color: {t.WHITE};
}}
QPlainTextEdit:focus, QLineEdit:focus {{ border: 1px solid {t.DEEP_TEAL}; }}
QLineEdit {{ min-height: {t.HIT_TARGET - 2 * t.SPACE_12}px; }}

/* ---- review table: a sheet on the canvas, not a grid ---- */
QTableView {{
    background-color: {t.SOFT_PAPER};
    alternate-background-color: {t.SOFT_PAPER};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_CARD}px;
    gridline-color: transparent;
    font-size: {t.TEXT_LABEL}px;
    outline: none;
}}
QTableView::item {{
    padding: {t.SPACE_12}px {t.SPACE_8}px;
    border-bottom: 1px solid {t.WARM_MIST};
}}
QTableView::item:selected {{
    background-color: {t.SOFT_PAPER};
    color: {t.INK};
}}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{
    background-color: {t.SOFT_PAPER};
    color: {t.GRAPHITE};
    border: none;
    border-bottom: 1px solid {t.WARM_MIST};
    padding: {t.SPACE_12}px {t.SPACE_8}px;
    font-size: {t.TEXT_MICRO}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}
QTableCornerButton::section {{ background: {t.SOFT_PAPER}; border: none; }}

QScrollBar:vertical {{ background: transparent; width: {t.SPACE_12}px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {t.WARM_MIST};
    border-radius: {t.SPACE_4}px;
    min-height: {t.SPACE_32}px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---- checkbox ---- */
QCheckBox {{ spacing: {t.SPACE_12}px; min-height: {t.HIT_TARGET}px; font-size: {t.TEXT_LABEL}px; }}
QCheckBox::indicator {{
    width: {t.SPACE_24}px;
    height: {t.SPACE_24}px;
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.SPACE_4}px;
    background: {t.SOFT_PAPER};
}}
QCheckBox::indicator:checked {{
    /* teal box with a clear tick — a filled square alone doesn't read as "on" */
    border-color: {t.DEEP_TEAL};
    image: url("{check_on}");
}}
QCheckBox::indicator:hover {{ border-color: {t.DEEP_TEAL}; }}
"""
