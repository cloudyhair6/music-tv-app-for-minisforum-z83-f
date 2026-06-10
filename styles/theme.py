"""MiniPC Dark Theme - Premium streaming UI aesthetic."""


class Colors:
    """Color palette for the application."""
    BG_PRIMARY = "#0a0e1a"
    BG_SECONDARY = "#111827"
    BG_TERTIARY = "#1a1f36"
    BG_CARD = "rgba(20, 25, 45, 0.85)"
    BG_CARD_HOVER = "rgba(28, 34, 64, 0.95)"
    BG_CARD_SOLID = "#141929"
    ACCENT = "#00d4ff"
    ACCENT_SECONDARY = "#7b61ff"
    ACCENT_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00d4ff, stop:1 #7b61ff)"
    ACCENT_GRADIENT_HOVER = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #33ddff, stop:1 #9580ff)"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#8892b0"
    TEXT_MUTED = "#4a5568"
    SUCCESS = "#00e676"
    WARNING = "#ffa726"
    DANGER = "#ff5252"
    BORDER = "rgba(30, 42, 74, 0.6)"
    BORDER_FOCUS = "rgba(0, 212, 255, 0.6)"
    FOCUS_GLOW = "rgba(0, 212, 255, 0.3)"
    OVERLAY = "rgba(10, 14, 26, 0.85)"
    NAV_BG = "rgba(10, 14, 26, 0.95)"
    SLIDER_TRACK = "#1e2a4a"
    SLIDER_GROOVE = "#0a0e1a"


class Sizes:
    """Size constants — optimised for 1080p projector on Minisforum Z83-F.
    
    Fonts are scaled up for 10-foot UI readability.
    Animations are kept lightweight for the Atom x5-Z8350 GPU.
    """
    NAV_WIDTH = 80
    CARD_RADIUS = 16
    CARD_RADIUS_SM = 12
    BUTTON_RADIUS = 12
    ANIMATION_DURATION = 200   # reduced from 300 for Z83-F perf
    ANIMATION_FAST = 100       # reduced from 150
    ANIMATION_SLOW = 350       # reduced from 500
    SPACING = 20
    SPACING_SM = 10
    SPACING_LG = 28
    SPACING_XL = 40
    FONT_HERO = 64             # 52 → 64 for projector
    FONT_H1 = 44               # 36 → 44
    FONT_H2 = 30               # 24 → 30
    FONT_H3 = 22               # 18 → 22
    FONT_BODY = 20             # 16 → 20
    FONT_SMALL = 17            # 14 → 17
    FONT_TINY = 14             # 12 → 14


def get_global_stylesheet() -> str:
    """Generate the global application stylesheet."""
    return f"""
        * {{
            font-family: 'Segoe UI', 'Arial', sans-serif;
            color: {Colors.TEXT_PRIMARY};
            outline: none;
        }}
        QMainWindow {{
            background-color: {Colors.BG_PRIMARY};
        }}
        QWidget {{
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background: {Colors.BG_SECONDARY};
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.TEXT_MUTED};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Colors.TEXT_SECONDARY};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {Colors.BG_SECONDARY};
            height: 8px;
            margin: 0;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {Colors.TEXT_MUTED};
            min-width: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {Colors.TEXT_SECONDARY};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QLabel {{
            background: transparent;
        }}
        QLineEdit {{
            background: {Colors.BG_SECONDARY};
            border: 1px solid {Colors.BORDER};
            border-radius: {Sizes.CARD_RADIUS_SM}px;
            padding: 10px 16px;
            font-size: {Sizes.FONT_BODY}px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QLineEdit:focus {{
            border: 1px solid {Colors.ACCENT};
        }}
        QPushButton {{
            background: {Colors.BG_TERTIARY};
            border: 1px solid {Colors.BORDER};
            border-radius: {Sizes.BUTTON_RADIUS}px;
            padding: 12px 24px;
            font-size: {Sizes.FONT_BODY}px;
            color: {Colors.TEXT_PRIMARY};
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: {Colors.BG_CARD_HOVER};
            border-color: {Colors.ACCENT};
        }}
        QPushButton:pressed {{
            background: {Colors.BG_SECONDARY};
        }}
        QPushButton:focus {{
            border: 2px solid {Colors.ACCENT};
        }}
        QSlider::groove:horizontal {{
            background: {Colors.SLIDER_GROOVE};
            height: 8px;
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: {Colors.ACCENT};
            width: 22px;
            height: 22px;
            margin: -7px 0;
            border-radius: 11px;
        }}
        QSlider::handle:horizontal:hover {{
            background: #33ddff;
            width: 26px;
            height: 26px;
            margin: -9px 0;
            border-radius: 13px;
        }}
        QSlider::sub-page:horizontal {{
            background: {Colors.ACCENT_GRADIENT};
            border-radius: 4px;
        }}
    """
