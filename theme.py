"""
Aurex Design System — Centralized theme, typography, and animation tokens.
Premium Desktop UI/UX (Notion/Cursor inspired).
"""

def blend_color(hex_color, alpha: float, bg = "#0F172A"):
    """Simulate CSS rgba() by blending a hex color with a background color. Supports CTk tuples."""
    if isinstance(hex_color, tuple) or isinstance(hex_color, list):
        bg_light = bg[0] if isinstance(bg, (tuple, list)) else bg
        bg_dark = bg[1] if isinstance(bg, (tuple, list)) else bg
        return (
            blend_color(hex_color[0], alpha, bg_light),
            blend_color(hex_color[1], alpha, bg_dark)
        )
    if isinstance(bg, (tuple, list)):
        return (
            blend_color(hex_color, alpha, bg[0]),
            blend_color(hex_color, alpha, bg[1])
        )
        
    try:
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
    except:
        return hex_color

class Colors:
    """AUREX Master Color Palette"""
    # Backgrounds
    BG_PRIMARY = ("#F3F4F6", "#050816")
    BG_SECONDARY = ("#FFFFFF", "#09101D")
    BG_SIDEBAR = ("#FFFFFF", "#050816")
    
    # Cards & Containers
    CARD_BG = ("#FFFFFF", "#101A30")
    CARD_HOVER = ("#F9FAFB", "#1B2845")
    CARD_FLOATING = ("#FFFFFF", "#14213D")
    
    # Borders & Lines
    BORDER_SUBTLE = ("#E5E7EB", "#222F4D")
    BORDER_HOVER = ("#D1D5DB", "#3B4A6F")
    BORDER_ACTIVE = ("#8B5CF6", "#8B5CF6")
    
    # Accents
    ACCENT_PRIMARY = ("#8B5CF6", "#8B5CF6")
    ACCENT_HOVER = ("#EC4899", "#EC4899")
    ACCENT_ACTIVE = ("#4F8BFF", "#4F8BFF")
    ACCENT_PRESSED = ("#22D3EE", "#22D3EE")
    ACCENT_GOLD = ("#FBBF24", "#FBBF24")
    ACCENT_SUBTLE = ("#E0E7FF", "#1C1B3A")
    
    # Status & Utility
    SUCCESS = ("#10B981", "#22C55E")
    SUCCESS_HOVER = ("#059669", "#34D399")
    WARNING = ("#F59E0B", "#FBBF24")
    WARNING_HOVER = ("#D97706", "#FCD34D")
    ERROR = ("#EF4444", "#EF4444")
    ERROR_HOVER = ("#DC2626", "#F87171")
    INFO = ("#3B82F6", "#4F8BFF")
    
    # Typography
    TEXT_PRIMARY = ("#111827", "#FFFFFF")
    TEXT_SECONDARY = ("#4B5563", "#B7C4E0")
    TEXT_MUTED = ("#9CA3AF", "#7383A8")
    TEXT_DISABLED = ("#D1D5DB", "#4E5C7C")
    
    # Input Fields
    INPUT_BG = ("#F9FAFB", "#0B1120")
    INPUT_BORDER = ("#E5E7EB", "#222F4D")
    INPUT_FOCUS = ("#8B5CF6", "#8B5CF6")
    
    # Transparent
    TRANSPARENT = "transparent"

    # --- LEGACY ALIASES (For backwards compatibility during phased redesign) ---
    BG_DEEPSPACE = BG_PRIMARY
    GLASS_FILL = CARD_BG
    GLASS_FILL_LIGHT = CARD_HOVER
    GLASS_FILL_HOVER = CARD_HOVER
    GLASS_BORDER = BORDER_SUBTLE
    GLASS_BORDER_BRIGHT = BORDER_HOVER
    ACCENT = ACCENT_PRIMARY
    ACCENT_MUTED = ACCENT_SUBTLE
    ACCENT_GLOW = ACCENT_ACTIVE
    CHART_GREEN = SUCCESS
    CHART_AMBER = WARNING
    CHART_RED = ERROR
    CHART_PURPLE = ACCENT_PRIMARY
    CHART_BLUE = INFO
    CHART_CYAN = ("#0891b2", "#06b6d4")
    TEXT_DIM = TEXT_DISABLED
    ENTRY_BG = INPUT_BG
    ENTRY_BORDER = INPUT_BORDER
    ENTRY_FOCUS_BORDER = INPUT_FOCUS
    TAG_MEETING = INFO
    TAG_WORK = SUCCESS
    TAG_PERSONAL = WARNING
    TAG_BREAK = ACCENT_PRIMARY
    PRIORITY_HIGH = ERROR
    PRIORITY_MEDIUM = WARNING
    PRIORITY_LOW = SUCCESS


FONT_FAMILY = "Sora"
BODY_FONT_FAMILY = "Inter"

class Fonts:
    """Typography Design System"""
    TITLE = (FONT_FAMILY, 24, "bold")
    HEADING = (FONT_FAMILY, 18, "bold")
    SUBHEADING = (FONT_FAMILY, 14, "bold")
    BODY = (BODY_FONT_FAMILY, 13)
    BODY_BOLD = (BODY_FONT_FAMILY, 13, "bold")
    CAPTION = (BODY_FONT_FAMILY, 11)
    BUTTON = (BODY_FONT_FAMILY, 13, "bold")
    SMALL = (BODY_FONT_FAMILY, 12)
    BRAND = (FONT_FAMILY, 20, "bold")
    MENU_ITEM = (BODY_FONT_FAMILY, 13, "bold")
    MENU_ITEM_ACTIVE = (BODY_FONT_FAMILY, 13, "bold")
    SMALL_BOLD = (BODY_FONT_FAMILY, 12, "bold")
    ENTRY = (BODY_FONT_FAMILY, 13)

class Dims:
    """Standardized Dimensions & Spacing"""
    SIDEBAR_WIDTH = 260
    RADIUS_S = 6
    RADIUS_M = 12
    RADIUS_L = 18
    MAIN_PAD_X = 24
    MAIN_PAD_Y = 24
    
    # Restored variables
    CARD_PAD = 16
    RADIUS_CARD = 16
    RADIUS_PILL = 24
    RADIUS_BUTTON = 8
    RADIUS_INPUT = 8
    BORDER_WIDTH = 1
    BTN_HEIGHT = 42
    BTN_CORNER = 8
    ENTRY_HEIGHT = 42
    ENTRY_CORNER = 8
    INPUT_HEIGHT = 42
    AUTH_CARD_H = 500
    PILL_CORNER = 16
    PILL_HEIGHT = 32
    BUTTON_HEIGHT_LARGE = 48
