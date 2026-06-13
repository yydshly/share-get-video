"""
Text Layout - Chinese text wrapping and layout utilities for Pillow
"""

from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple


# System font search order for Chinese
FONT_CANDIDATES = [
    # Windows
    "C:/Windows/Fonts/msyh.ttc",      # Microsoft YaHei
    "C:/Windows/Fonts/simhei.ttf",      # SimHei
    "C:/Windows/Fonts/simsun.ttc",     # SimSun
    "C:/Windows/Fonts/arial.ttf",       # Arial (fallback)
    # Linux
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def find_chinese_font(font_size: int = 36) -> Tuple[ImageFont.FreeTypeFont, List[str]]:
    """
    Find an available font that supports Chinese.
    Returns (font, warnings).
    """
    warnings = []
    for font_path in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(font_path, font_size)
            return font, warnings
        except (OSError, IOError):
            continue

    # Fallback to default
    warnings.append(f"No Chinese font found. Using default font. Chinese characters may not render correctly.")
    try:
        font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    return font, warnings


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """
    Wrap Chinese text to fit within max_width pixels.
    Returns list of lines.
    """
    if not text:
        return [""]

    lines = []
    current_line = ""

    # Estimate characters that fit based on average character width
    # For 1080px width at font_size ~36, roughly 20-25 chars per line
    avg_char_width = int(font.size * 0.6)

    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    if not lines:
        lines = [text]

    return lines


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, adding ellipsis if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + "…"


def split_title_and_body(full_text: str, max_title_chars: int = 30) -> Tuple[str, str]:
    """
    Split text into title and body.
    Title is first N chars, body is the rest.
    """
    if len(full_text) <= max_title_chars:
        return full_text, ""

    title = full_text[:max_title_chars]
    body = full_text[max_title_chars:]
    return title, body


def get_text_size(text: str, font: ImageFont.FreeTypeFont, draw: ImageDraw.ImageDraw) -> Tuple[int, int]:
    """Get width and height of text in pixels."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def center_text_in_region(
    text: str,
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
    region_width: int,
    region_height: int,
) -> Tuple[int, int]:
    """
    Calculate x,y to center text in a region.
    Returns (x, y) top-left coordinate.
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (region_width - text_width) // 2
    y = (region_height - text_height) // 2
    return x, y
