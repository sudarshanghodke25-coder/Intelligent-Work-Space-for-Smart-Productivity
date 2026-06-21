"""
Aurex Theme — Centralized design tokens.
Deep-space nebula glassmorphism aesthetic.
"""


def blend_color(hex_color: str, alpha: float, bg: str = "#1a1730") -> str:
    """
    Blend a hex color at a given alpha (0.0-1.0) against a background color.
    Returns a solid 6-digit hex color simulating the alpha effect.
    Useful because tkinter does not support 8-digit hex alpha colors.
    """
    fg_r = int(hex_color[1:3], 16)
    fg_g = int(hex_color[3:5], 16)
    fg_b = int(hex_color[5:7], 16)
    bg_r = int(bg[1:3], 16)
    bg_g = int(bg[3:5], 16)
    bg_b = int(bg[5:7], 16)
    r = int(fg_r * alpha + bg_r * (1 - alpha))
    g = int(fg_g * alpha + bg_g * (1 - alpha))
    b = int(fg_b * alpha + bg_b * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Color Palette ──────────────────────────────────────────────────────────

class Colors:
    # Base backgrounds
    BG_DEEPSPACE = "#0a0a1e"
    BG_SIDEBAR = "#0f0d1a"
    BG_DOCK = "#110f1f"

    # Glass card
    GLASS_FILL = "#1a1730"
    GLASS_FILL_LIGHT = "#221f38"
    GLASS_FILL_HOVER = "#252240"
    GLASS_BORDER = "#3a3a4a"
    GLASS_BORDER_BRIGHT = "#4a4a5e"

    # Accent purple
    ACCENT_PRIMARY = "#7c3aed"
    ACCENT_GLOW = "#a855f7"
    ACCENT_HOVER = "#8b5cf6"
    ACCENT_MUTED = "#6d28d9"
    ACCENT_SUBTLE = "#241a3d"   # 20% opacity purple blended on dark bg

    # Text
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#9ca3af"
    TEXT_MUTED = "#6b7280"
    TEXT_DIM = "#4b5563"

    # Status colors
    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"

    # Category tag colors
    TAG_MEETING = "#3b82f6"
    TAG_WORK = "#22c55e"
    TAG_PERSONAL = "#f59e0b"
    TAG_BREAK = "#8b5cf6"

    # Priority badge colors
    PRIORITY_HIGH = "#ef4444"
    PRIORITY_MEDIUM = "#f59e0b"
    PRIORITY_LOW = "#22c55e"

    # Chart palette
    CHART_GREEN = "#22c55e"
    CHART_AMBER = "#f59e0b"
    CHART_RED = "#ef4444"
    CHART_PURPLE = "#8b5cf6"
    CHART_BLUE = "#3b82f6"
    CHART_CYAN = "#06b6d4"

    # Input fields
    ENTRY_BG = "#15132a"
    ENTRY_BORDER = "#2e2e3e"
    ENTRY_FOCUS_BORDER = "#7c3aed"

    # Transparent
    TRANSPARENT = "transparent"


# ── Font Definitions ───────────────────────────────────────────────────────

FONT_FAMILY = "Segoe UI"

class Fonts:
    """Font tuples: (family, size, weight)"""
    BRAND = (FONT_FAMILY, 22, "bold")
    TITLE = (FONT_FAMILY, 20, "bold")
    HEADING = (FONT_FAMILY, 16, "bold")
    SUBHEADING = (FONT_FAMILY, 14, "bold")
    BODY = (FONT_FAMILY, 13, "normal")
    BODY_BOLD = (FONT_FAMILY, 13, "bold")
    SMALL = (FONT_FAMILY, 11, "normal")
    SMALL_BOLD = (FONT_FAMILY, 11, "bold")
    CAPTION = (FONT_FAMILY, 10, "normal")
    MENU_ITEM = (FONT_FAMILY, 13, "normal")
    MENU_ITEM_ACTIVE = (FONT_FAMILY, 13, "bold")
    BUTTON = (FONT_FAMILY, 14, "bold")
    ENTRY = (FONT_FAMILY, 13, "normal")


# ── Dimensions ─────────────────────────────────────────────────────────────

class Dims:
    # Layout
    SIDEBAR_WIDTH = 240
    DOCK_HEIGHT = 56
    CARD_CORNER = 16
    CARD_BORDER = 1
    CARD_PAD = 14

    # Auth
    AUTH_CARD_W = 440
    AUTH_CARD_H = 520

    # Sidebar
    MENU_ITEM_HEIGHT = 40
    PROFILE_CARD_H = 70
    SIDEBAR_PAD_X = 16

    # Entry fields
    ENTRY_HEIGHT = 42
    ENTRY_CORNER = 10

    # Buttons
    BTN_HEIGHT = 44
    BTN_CORNER = 12
    PILL_HEIGHT = 32
    PILL_CORNER = 16

    # Dock
    DOCK_ENTRY_HEIGHT = 40
    DOCK_BTN_SIZE = 38

    # Charts
    DONUT_SIZE = 140
    DONUT_THICKNESS = 22
    BAR_GAP = 8
