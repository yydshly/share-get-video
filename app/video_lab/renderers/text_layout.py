"""
Text Layout - Chinese text wrapping and layout utilities for Pillow
"""

import re
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Optional


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


# Highlight patterns for extracting key numbers/keywords
HIGHLIGHT_PATTERNS = [
    # Model names with version: F1, F2, GPT-5, Claude 4, Gemini 2, Llama 3
    (r'(?:GPT|Claude|Gemini|Llama|Mistral)[\s-]?\d+(?:\.\d+)?', 'model_name'),
    (r'(?:F[12]|AlphaFold|Sora|o1|o3|o4)[^a-zA-Z0-9]?', 'model_name'),
    # Percentages: 88.9%, 72%, 16%
    (r'\d+\.?\d*%', 'percentage'),
    # Multipliers: 10倍, 5x, 3X
    (r'\d+\.?\d*[xX倍]', 'multiplier'),
    # Large numbers with units: 10万, 5620亿, 100万, 50亿
    (r'\d+[一-龥]+', 'chinese_number'),
    # Numbers followed by specific words
    (r'\d+\.?\d*(?:名|人|员工|用户|企业|模型|参数|亿|万)', 'number_with_unit'),
    # Decimal numbers > 10: 88.9, 72.5
    (r'\d{2,}\.\d+', 'large_decimal'),
    # Large round numbers: 1000, 5000, 10000
    (r'[1-9]\d{3,}', 'large_integer'),
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

    # Post-process: merge orphan punctuation at end of lines
    lines = _merge_orphan_punctuation(lines, font, max_width, draw)

    return lines


# ─── Punctuation helpers for line merging ────────────────────────────────────────

def _is_terminal_punctuation(c: str) -> bool:
    """Check if character is terminal punctuation that shouldn't be alone on a line."""
    return c in '。，、；：？！""''．'


def _is_hyphen_like(c: str) -> bool:
    """Check if character is punctuation that shouldn't start a line."""
    return c in '-—–_.,;:?!'


def _merge_orphan_punctuation(
    lines: List[str],
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw,
) -> List[str]:
    """
    Post-process wrapped lines to avoid orphaned punctuation at line ends.
    E.g., avoid: "ProReviewer系统在五个质量维度" + "。" where "." is orphaned.
    Also merges hyphen-like chars that start a line back to previous line.
    """
    if len(lines) <= 1:
        return lines

    result = []
    for i, line in enumerate(lines):
        if not line:
            continue

        # Rule 1: If line ends with terminal punctuation AND next line exists AND next line is short, merge
        if i < len(lines) - 1 and line and _is_terminal_punctuation(line[-1]):
            next_line = lines[i + 1]
            if next_line and len(next_line) < 6:
                merged = line + next_line
                bbox = draw.textbbox((0, 0), merged, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    result.append(merged)
                    continue

        # Rule 2: If line starts with hyphen-like char, try to merge with previous
        if i > 0 and line and _is_hyphen_like(line[0]) and result:
            merged = result[-1] + line
            bbox = draw.textbbox((0, 0), merged, font=font)
            if bbox[2] - bbox[0] <= max_width:
                result[-1] = merged
                continue

        result.append(line)

    return result


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


def extract_highlights(text: str) -> List[str]:
    """
    Extract highlight terms from text.
    Recognizes: percentages, multipliers, large numbers, Chinese number phrases.
    Uses 'auto' mode internally.

    Args:
        text: Input text

    Returns:
        List of highlight terms found in text (deduplicated, order of first appearance)
    """
    return extract_highlights_by_mode(text, "auto")


# Highlight patterns for 'numbers' mode - only numeric patterns
NUMBERS_ONLY_PATTERNS = [
    # Percentages: 88.9%, 72%, 16%
    (r'\d+\.?\d*%', 'percentage'),
    # Multipliers: 10倍, 5x, 3X
    (r'\d+\.?\d*[xX倍]', 'multiplier'),
    # Decimal numbers > 10: 88.9, 72.5
    (r'\d{2,}\.\d+', 'large_decimal'),
    # Large round numbers: 1000, 5000, 10000
    (r'[1-9]\d{3,}', 'large_integer'),
]


def extract_highlights_by_mode(text: str, mode: str = "auto") -> List[str]:
    """
    Extract highlight terms from text based on mode.

    Modes:
    - auto: Numbers + percentages + multipliers + Chinese number phrases + large amounts
    - numbers: Only numeric patterns (percentages, multipliers, decimals, large integers)
    - none: Return empty list (no highlight extraction)

    Args:
        text: Input text
        mode: Extraction mode ('auto', 'numbers', 'none')

    Returns:
        List of highlight terms found in text (deduplicated, order of first appearance)
    """
    if not text:
        return []

    if mode == "none":
        return []

    # Select pattern set based on mode
    if mode == "numbers":
        patterns_to_use = NUMBERS_ONLY_PATTERNS
    else:  # auto
        patterns_to_use = HIGHLIGHT_PATTERNS

    found = []
    seen = set()

    for pattern, pattern_type in patterns_to_use:
        for match in re.finditer(pattern, text):
            term = match.group()
            if term not in seen:
                seen.add(term)
                found.append(term)

    return found


def split_lines_with_max_count(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw,
    max_lines: int = 3,
) -> List[str]:
    """
    Split text into lines, limiting to max_lines.
    If text exceeds max_lines, it will be truncated with ellipsis.

    Args:
        text: Input text
        font: Font to use
        max_width: Maximum width per line in pixels
        draw: ImageDraw instance
        max_lines: Maximum number of lines allowed

    Returns:
        List of lines (max max_lines)
    """
    if not text:
        return [""]

    # First wrap the text
    wrapped = wrap_text(text, font, max_width, draw)

    # If within limit, return as-is
    if len(wrapped) <= max_lines:
        return wrapped

    # Truncate the last line to fit
    result = wrapped[:max_lines]
    last_line_idx = max_lines - 1

    # Try to append ellipsis to the last line
    if result:
        last_line = result[last_line_idx]
        truncated = truncate_text(last_line, 15)  # Conservative truncation
        result[last_line_idx] = truncated

    return result


def fit_font_size(
    text: str,
    max_width: int,
    max_height: int,
    font_candidates: Optional[List[int]] = None,
    draw: Optional[ImageDraw.ImageDraw] = None,
) -> int:
    """
    Find the largest font size that fits text within max_width and max_height.

    Args:
        text: Text to fit
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        font_candidates: List of font sizes to try (default: 16-120 even numbers)
        draw: ImageDraw instance (required for measurement)

    Returns:
        Recommended font size that fits
    """
    if not draw:
        return 36  # Default

    if not text:
        return 36

    if font_candidates is None:
        font_candidates = list(range(16, 121, 2))

    # Start from largest and work down
    for size in sorted(font_candidates, reverse=True):
        font, _ = find_chinese_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if text_width <= max_width and text_height <= max_height:
            return size

    # Return smallest candidate if nothing fits
    return font_candidates[-1] if font_candidates else 16


def fit_wrapped_text(
    text: str,
    max_width: int,
    max_height: int,
    draw: ImageDraw.ImageDraw,
    size_max: int = 64,
    size_min: int = 22,
    line_spacing: int = 14,
    step: int = 2,
):
    """在给定区域内，选出能容纳**全部文字（不截断）**的最大字号并换行。

    返回 (font, lines, font_size, line_height, overflow)：
    - 从 size_max 往下试，第一个让"换行后总高度 <= max_height"的字号即采用；
    - 若连最小字号都放不下，返回最小字号的换行结果并 overflow=True（仍包含全部文字，
      不丢内容；由上层据此告警，质量层可感知）。
    """
    text = (text or "").strip()
    if not text:
        font, _ = find_chinese_font(size_min)
        return font, [""], size_min, size_min + line_spacing, False

    last = None
    for size in range(size_max, size_min - 1, -step):
        font, _ = find_chinese_font(size)
        lines = wrap_text(text, font, max_width, draw)
        line_h = get_text_size("测试", font, draw)[1] + line_spacing
        total_h = len(lines) * line_h
        last = (font, lines, size, line_h)
        if total_h <= max_height:
            return font, lines, size, line_h, False

    # 连最小字号都放不下：返回最小字号结果（全文保留），标记 overflow
    font, lines, size, line_h = last
    return font, lines, size, line_h, True


def split_headline_and_detail(text: str) -> Tuple[str, str]:
    """把一句新闻拆成"标题"与"详情"。

    优先按中文/英文冒号切分（"标题：详情"）；无冒号则按第一个句末标点切；
    再无则整句作为标题。
    """
    text = (text or "").strip()
    if not text:
        return "", ""
    for sep in ("：", ":"):
        if sep in text:
            head, _, rest = text.partition(sep)
            head = head.strip()
            rest = rest.strip()
            if head and rest:
                return head, rest
    # 退化：按第一个句末标点
    for i, ch in enumerate(text):
        if ch in "。！？!?" and 4 <= i <= 24:
            return text[: i + 1].strip(), text[i + 1:].strip()
    return text, ""


def wrap_text_by_visual_width(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw,
    min_chars_per_line: int = 5,
) -> List[str]:
    """
    Wrap text with better visual width estimation.
    Tries to balance line lengths and avoid orphan words.

    Args:
        text: Input text
        font: Font to use
        max_width: Maximum width per line
        draw: ImageDraw instance
        min_chars_per_line: Minimum characters before wrapping

    Returns:
        List of wrapped lines
    """
    if not text:
        return [""]

    # First try standard wrapping
    lines = wrap_text(text, font, max_width, draw)

    # Post-process: merge very short lines with previous
    if len(lines) <= 1:
        return lines

    result = []
    for i, line in enumerate(lines):
        # If line is very short and not the first line
        if i > 0 and len(line) < min_chars_per_line and result:
            # Merge with previous line
            result[-1] = result[-1] + line
        else:
            result.append(line)

    # Re-wrap the merged lines to ensure they fit
    final_lines = []
    for line in result:
        if not line:
            continue
        bbox = draw.textbbox((0, 0), line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            final_lines.append(line)
        else:
            # Re-wrap this line
            final_lines.extend(wrap_text(line, font, max_width, draw))

    return final_lines if final_lines else [text]
