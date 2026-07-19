"""Renders the application stylesheet from tokens. No hex values elsewhere."""

from penname.gui.theme import tokens as t


def build_stylesheet() -> str:
    return f"""
QWidget {{
    background-color: {t.PARCHMENT};
    color: {t.INK};
    font-family: {t.FONT_FAMILY};
    font-size: {t.TEXT_BODY}px;
    font-weight: {t.WEIGHT_REGULAR};
}}

QLabel {{ background: transparent; }}
QLabel[role="heading"] {{
    font-size: {t.TEXT_HEADING}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}
QLabel[role="helper"] {{
    color: {t.GRAPHITE};
    font-size: {t.TEXT_CAPTION}px;
}}
QLabel[role="banner"] {{
    background-color: {t.SOFT_PAPER};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_CARD}px;
    padding: {t.SPACE_16}px;
    font-size: {t.TEXT_BODY_LG}px;
}}

/* Ghost button — the default action style */
QPushButton {{
    background: transparent;
    color: {t.INK};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_BUTTON}px;
    padding: {t.SPACE_8}px {t.SPACE_16}px;
    min-height: {t.HIT_TARGET - 2 * t.SPACE_8}px;
}}
QPushButton:hover {{ background-color: {t.SOFT_PAPER}; }}
QPushButton:focus {{ border: 2px solid {t.DEEP_TEAL}; }}
QPushButton:disabled {{ color: {t.ASH}; border-color: {t.WARM_MIST}; }}

/* Filled primary action — ink on parchment, one per screen */
QPushButton[role="primary"] {{
    background-color: {t.INK};
    color: {t.PARCHMENT};
    border: none;
    border-radius: {t.RADIUS_INPUT}px;
    padding: {t.SPACE_12}px {t.SPACE_24}px;
    font-size: {t.TEXT_BODY_LG}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}
QPushButton[role="primary"]:hover {{ background-color: #000000; }}
QPushButton[role="primary"]:disabled {{ background-color: {t.ASH}; color: {t.PARCHMENT}; }}

/* Sidebar navigation */
QFrame[role="sidebar"] {{
    background-color: {t.SOFT_PAPER};
    border-right: 1px solid {t.WARM_MIST};
}}
QPushButton[role="nav"] {{
    background: transparent;
    color: {t.GRAPHITE};
    border: none;
    border-radius: {t.RADIUS_INPUT}px;
    padding: {t.SPACE_12}px {t.SPACE_16}px;
    text-align: left;
    font-size: {t.TEXT_BODY}px;
}}
QPushButton[role="nav"]:hover {{ color: {t.INK}; }}
QPushButton[role="nav"]:checked {{
    background-color: {t.DEEP_TEAL};
    color: {t.WHITE};
}}
QLabel[role="brand"] {{
    font-size: {t.TEXT_BODY_LG}px;
    font-weight: {t.WEIGHT_MEDIUM};
    background: transparent;
}}

/* Inputs */
QPlainTextEdit, QLineEdit {{
    background-color: {t.SOFT_PAPER};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_INPUT}px;
    padding: {t.SPACE_12}px;
    selection-background-color: {t.DEEP_TEAL};
    selection-color: {t.WHITE};
}}
QPlainTextEdit:focus, QLineEdit:focus {{ border: 2px solid {t.DEEP_TEAL}; }}
QLineEdit {{ min-height: {t.HIT_TARGET - 2 * t.SPACE_12}px; }}

/* Review table */
QTableView {{
    background-color: {t.SOFT_PAPER};
    alternate-background-color: {t.PARCHMENT};
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.RADIUS_CARD}px;
    gridline-color: {t.WARM_MIST};
}}
QTableView::item {{ padding: {t.SPACE_8}px; }}
QTableView::item:selected {{
    background-color: {t.DEEP_TEAL};
    color: {t.WHITE};
}}
QHeaderView::section {{
    background-color: {t.SOFT_PAPER};
    color: {t.GRAPHITE};
    border: none;
    border-bottom: 1px solid {t.WARM_MIST};
    padding: {t.SPACE_12}px;
    font-weight: {t.WEIGHT_MEDIUM};
}}

QScrollBar:vertical {{
    background: transparent;
    width: {t.SPACE_12}px;
}}
QScrollBar::handle:vertical {{
    background: {t.WARM_MIST};
    border-radius: {t.SPACE_4}px;
    min-height: {t.SPACE_32}px;
}}

QCheckBox {{ spacing: {t.SPACE_8}px; min-height: {t.HIT_TARGET}px; }}
QCheckBox::indicator {{
    width: {t.SPACE_24}px;
    height: {t.SPACE_24}px;
    border: 1px solid {t.WARM_MIST};
    border-radius: {t.SPACE_4}px;
    background: {t.SOFT_PAPER};
}}
QCheckBox::indicator:checked {{
    background-color: {t.DEEP_TEAL};
    border-color: {t.DEEP_TEAL};
}}
"""
