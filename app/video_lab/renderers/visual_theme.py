"""
Visual Theme - AI Frontier Dark preset constants
Defines colors, typography, spacing, shadows, and decorative elements.
"""

from typing import Tuple, Dict, Any

# ─────────────────────────────────────────
# Color Palette - AI Frontier Dark
# ─────────────────────────────────────────
COLORS: Dict[str, Tuple[int, int, int]] = {
    # Backgrounds
    "bg_primary": (12, 12, 30),
    "bg_secondary": (20, 20, 50),
    "bg_card": (25, 30, 65),
    "bg_card_hover": (30, 35, 75),

    # Gradients (top → bottom)
    "gradient_start": (20, 20, 55),
    "gradient_mid": (15, 15, 40),
    "gradient_end": (8, 8, 25),

    # Text
    "text_primary": (255, 255, 255),
    "text_secondary": (185, 195, 215),
    "text_tertiary": (130, 140, 165),
    "text_dim": (90, 100, 125),

    # Accent - Blue/Purple tech feel
    "accent_blue": (80, 140, 255),
    "accent_purple": (140, 100, 255),
    "accent_cyan": (80, 220, 220),
    "accent_glow_blue": (120, 170, 255),

    # Highlight - Key numbers/keywords
    "highlight_yellow": (255, 215, 60),
    "highlight_cyan": (80, 220, 220),
    "highlight_orange": (255, 160, 60),
    "highlight_green": (80, 220, 140),

    # Tags
    "tag_background": (40, 55, 115),
    "tag_border": (60, 90, 180),
    "tag_text": (160, 190, 255),

    # Decorative
    "decor_line": (60, 80, 150),
    "decor_glow": (100, 150, 255),
    "decor_dot": (80, 140, 255),

    # Borders
    "border_subtle": (35, 45, 85),
    "border_active": (80, 130, 220),
}

# ─────────────────────────────────────────
# Typography - Font Sizes
# ─────────────────────────────────────────
# V0.3.6-a: Increased for better mobile readability.
# Main titles: 56-72px, body: 30-40px, subtitles: 28-34px
FONT_SIZES: Dict[str, int] = {
    "cover_title": 72,
    "cover_subtitle": 32,
    "cover_tag": 22,
    "cover_label": 20,

    "overview_title": 48,
    "overview_item": 28,
    "overview_index": 40,

    "keypoint_index": 36,
    "keypoint_category": 20,
    "keypoint_title": 48,
    "keypoint_body": 34,
    "keypoint_source": 20,

    "summary_title": 48,
    "summary_body": 32,
    "summary_cta": 24,

    "highlight": 44,
    "highlight_large": 56,

    "tag": 18,
    "footer": 18,
}

# ─────────────────────────────────────────
# Spacing & Layout
# ─────────────────────────────────────────
SPACING: Dict[str, int] = {
    # Margins
    "margin_horizontal": 60,
    "margin_vertical": 80,

    # Card padding
    "card_padding": 40,
    "card_radius": 16,

    # Line heights
    "line_height_title": 1.3,
    "line_height_body": 1.6,

    # Element gaps
    "gap_small": 12,
    "gap_medium": 24,
    "gap_large": 40,
    "gap_xlarge": 60,

    # Decorative
    "decor_line_height": 3,
    "decor_glow_radius": 120,
}

# ─────────────────────────────────────────
# Resolution Presets
# ─────────────────────────────────────────
RESOLUTION_PRESETS: Dict[str, Tuple[int, int]] = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
}

# ─────────────────────────────────────────
# Category Colors
# ─────────────────────────────────────────
CATEGORY_COLORS: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    "安全": {"bg": (60, 20, 30), "text": (255, 140, 140), "border": (180, 60, 80)},
    "研究": {"bg": (20, 50, 70), "text": (100, 180, 255), "border": (40, 120, 200)},
    "应用": {"bg": (20, 60, 40), "text": (100, 220, 160), "border": (40, 160, 100)},
    "工具": {"bg": (50, 40, 70), "text": (180, 140, 255), "border": (140, 100, 220)},
    "企业": {"bg": (60, 50, 20), "text": (255, 200, 100), "border": (200, 160, 40)},
    "技术": {"bg": (30, 30, 60), "text": (140, 160, 220), "border": (80, 100, 160)},
    "默认": {"bg": (40, 55, 115), "text": (160, 190, 255), "border": (60, 90, 180)},
}

# ─────────────────────────────────────────
# Template Version
# ─────────────────────────────────────────
TEMPLATE_VERSION = "v0.2.4"
VISUAL_PRESET = "ai_frontier_dark"
TRANSITION_TYPE = "fade"
TRANSITION_FRAMES_DEFAULT = 4  # Number of intermediate fade frames


def get_category_style(category: str) -> Dict[str, Tuple[int, int, int]]:
    """Get color style for a given category."""
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["默认"])


def blend_colors(color1: Tuple[int, int, int], color2: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
    """Blend two colors with given ratio (0.0 = color1, 1.0 = color2)."""
    r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
    g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
    b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
