"""
Frame Templates - AI Frontier Dark preset template functions
Renders cover, overview, keypoint, and summary frames using Pillow.
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from PIL import Image, ImageDraw, ImageFont

from app.video_lab.renderers.visual_theme import (
    COLORS,
    FONT_SIZES,
    SPACING,
    VISUAL_PRESET,
    TEMPLATE_VERSION,
    get_category_style,
    blend_colors,
)
from app.video_lab.renderers.text_layout import (
    find_chinese_font,
    wrap_text,
    truncate_text,
    split_title_and_body,
    get_text_size,
    extract_highlights,
    split_lines_with_max_count,
    fit_font_size,
)


def render_gradient_background(width: int, height: int) -> Image.Image:
    """Create deep tech gradient background."""
    img = Image.new("RGB", (width, height), COLORS["bg_primary"])
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        if ratio < 0.5:
            t = ratio * 2
            r = int(COLORS["gradient_start"][0] * (1 - t) + COLORS["gradient_mid"][0] * t)
            g = int(COLORS["gradient_start"][1] * (1 - t) + COLORS["gradient_mid"][1] * t)
            b = int(COLORS["gradient_start"][2] * (1 - t) + COLORS["gradient_mid"][2] * t)
        else:
            t = (ratio - 0.5) * 2
            r = int(COLORS["gradient_mid"][0] * (1 - t) + COLORS["gradient_end"][0] * t)
            g = int(COLORS["gradient_mid"][1] * (1 - t) + COLORS["gradient_end"][1] * t)
            b = int(COLORS["gradient_mid"][2] * (1 - t) + COLORS["gradient_end"][2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def draw_decorative_elements(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    """Add subtle decorative elements: corner glows, dots."""
    # Top-left glow
    for i in range(30):
        alpha_ratio = 1 - (i / 30)
        glow_color = blend_colors(COLORS["bg_primary"], COLORS["decor_glow"], alpha_ratio * 0.3)
        draw.ellipse(
            [(0, 0), (80 + i * 4, 80 + i * 4)],
            fill=glow_color
        )

    # Bottom-right glow
    for i in range(25):
        alpha_ratio = 1 - (i / 25)
        glow_color = blend_colors(COLORS["bg_primary"], COLORS["accent_purple"], alpha_ratio * 0.2)
        draw.ellipse(
            [(width - 100 - i * 3, height - 100 - i * 3), (width, height)],
            fill=glow_color
        )

    # Scattered dots
    dot_positions = [
        (width * 0.15, height * 0.12),
        (width * 0.85, height * 0.08),
        (width * 0.9, height * 0.85),
        (width * 0.08, height * 0.88),
    ]
    for x, y in dot_positions:
        draw.ellipse([(x - 3, y - 3), (x + 3, y + 3)], fill=COLORS["decor_dot"])


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_y: int,
    width: int,
    font: ImageFont.FreeTypeFont,
    color: Tuple[int, int, int],
    max_width_ratio: float = 0.85,
) -> int:
    """Draw text centered horizontally, return actual height used."""
    max_text_width = int(width * max_width_ratio)
    lines = wrap_text(text, font, max_text_width, draw)
    line_height = get_text_size("测试", font, draw)[1] + 8
    total_height = len(lines) * line_height
    start_y = center_y - total_height // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        draw.text((x, start_y + i * line_height), line, font=font, fill=color)

    return total_height


def draw_tag(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    center_y: int,
    font: ImageFont.FreeTypeFont,
    style: Dict[str, Tuple[int, int, int]],
) -> Tuple[int, int]:
    """Draw a rounded tag with background. Returns (width, height)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    padding = 16
    tag_w = text_w + padding * 2
    tag_h = text_h + padding

    # Draw rounded rectangle background
    left = center_x - tag_w // 2
    top = center_y - tag_h // 2
    right = center_x + tag_w // 2
    bottom = center_y + tag_h // 2

    draw.rounded_rectangle(
        [(left, top), (right, bottom)],
        radius=8,
        fill=style["bg"],
        outline=style["border"],
        width=1,
    )
    draw.text((center_x - text_w // 2, top + (tag_h - text_h) // 2 - 2), text, font=font, fill=style["text"])

    return (tag_w, tag_h)


# ─────────────────────────────────────────
# Cover Frame Template
# ─────────────────────────────────────────
def render_cover_template(
    title: str,
    subtitle: str,
    tags: List[str],
    date_str: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """
    Render enhanced cover frame with:
    - Top label: "AI Frontier Radar"
    - Large title
    - Subtitle
    - 3 signal tags
    - Background gradient with decorative elements
    - Date and footer
    """
    width, height = resolution
    img = render_gradient_background(width, height)
    draw = ImageDraw.Draw(img)
    draw_decorative_elements(draw, width, height)

    warnings = []

    # Font sizes adjusted for resolution
    font_size_title = int(FONT_SIZES["cover_title"] * (width / 1080))
    font_size_subtitle = int(FONT_SIZES["cover_subtitle"] * (width / 1080))
    font_size_tag = int(FONT_SIZES["cover_tag"] * (width / 1080))
    font_size_label = int(FONT_SIZES["cover_label"] * (width / 1080))

    font_title, w = find_chinese_font(font_size_title)
    font_subtitle, w2 = find_chinese_font(font_size_subtitle)
    font_tag, w3 = find_chinese_font(font_size_tag)
    font_label, w4 = find_chinese_font(font_size_label)
    warnings.extend(w)
    warnings.extend(w2)
    warnings.extend(w3)
    warnings.extend(w4)

    # Top decorative line
    line_y = 120
    draw.rectangle(
        [(width // 4, line_y), (width * 3 // 4, line_y + SPACING["decor_line_height"])],
        fill=COLORS["accent_blue"]
    )

    # Top label
    label_text = "AI Frontier Radar"
    bbox = draw.textbbox((0, 0), label_text, font=font_label)
    label_w = bbox[2] - bbox[0]
    draw.text(((width - label_w) // 2, line_y + 30), label_text, font=font_label, fill=COLORS["accent_cyan"])

    # Main title - split into lines if needed
    title_max_width = int(width * 0.88)
    title_lines = split_lines_with_max_count(title, font_title, title_max_width, draw, max_lines=3)
    title_line_h = get_text_size("测试", font_title, draw)[1] + 12
    title_start_y = height // 2 - len(title_lines) * title_line_h // 2 - 80

    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, title_start_y + i * title_line_h), line, font=font_title, fill=COLORS["text_primary"])

    # Subtitle
    subtitle_y = title_start_y + len(title_lines) * title_line_h + 30
    draw_centered_text(draw, subtitle, subtitle_y, width, font_subtitle, COLORS["text_secondary"])

    # Signal tags
    tags_y = height // 2 + 120
    tag_spacing = 30
    total_tags_width = 0
    tag_sizes = []
    for tag in tags[:3]:
        style = get_category_style("默认")
        bbox = draw.textbbox((0, 0), tag, font=font_tag)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        padding = 16
        tag_sizes.append((tw + padding * 2, th + padding))
        total_tags_width += tw + padding * 2 + tag_spacing

    total_tags_width -= tag_spacing
    current_x = (width - total_tags_width) // 2

    for i, tag in enumerate(tags[:3]):
        style = get_category_style("默认")
        bbox = draw.textbbox((0, 0), tag, font=font_tag)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        padding = 16
        tag_w = tw + padding * 2
        tag_h = th + padding

        draw.rounded_rectangle(
            [(current_x, tags_y - tag_h // 2), (current_x + tag_w, tags_y + tag_h // 2)],
            radius=10,
            fill=style["bg"],
            outline=style["border"],
            width=1,
        )
        draw.text((current_x + padding, tags_y - th // 2 - 2), tag, font=font_tag, fill=style["text"])
        current_x += tag_w + tag_spacing

    # Bottom decorative line
    bottom_line_y = height - 280
    draw.rectangle(
        [(width // 4, bottom_line_y), (width * 3 // 4, bottom_line_y + SPACING["decor_line_height"])],
        fill=COLORS["decor_line"]
    )

    # Date
    if date_str:
        bbox = draw.textbbox((0, 0), date_str, font=font_label)
        dw = bbox[2] - bbox[0]
        draw.text(((width - dw) // 2, bottom_line_y + 25), date_str, font=font_label, fill=COLORS["text_tertiary"])

    # Footer
    footer_text = "Video Capability Lab · AI Frontier Daily"
    bbox = draw.textbbox((0, 0), footer_text, font=font_label)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 120), footer_text, font=font_label, fill=COLORS["text_dim"])

    output_path = frames_dir / "cover.png"
    img.save(output_path, "PNG")

    return {
        "path": output_path,
        "warnings": warnings,
        "template": "cover",
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
    }


# ─────────────────────────────────────────
# Overview Frame Template
# ─────────────────────────────────────────
def render_overview_template(
    items: List[Dict[str, str]],
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """
    Render overview frame showing top 4 key points with indices.
    """
    width, height = resolution
    img = render_gradient_background(width, height)
    draw = ImageDraw.Draw(img)

    warnings = []
    font_size_title = int(FONT_SIZES["overview_title"] * (width / 1080))
    font_size_item = int(FONT_SIZES["overview_item"] * (width / 1080))
    font_size_index = int(FONT_SIZES["overview_index"] * (width / 1080))

    font_title, w = find_chinese_font(font_size_title)
    font_item, w2 = find_chinese_font(font_size_item)
    font_index, w3 = find_chinese_font(font_size_index)
    warnings.extend(w)
    warnings.extend(w2)
    warnings.extend(w3)

    # Title
    title_text = "今日重点"
    draw_centered_text(draw, title_text, height // 5, width, font_title, COLORS["highlight_yellow"])

    # Decorative line under title
    line_y = height // 5 + 60
    draw.rectangle(
        [(width // 4, line_y), (width * 3 // 4, line_y + SPACING["decor_line_height"])],
        fill=COLORS["accent_blue"]
    )

    # Items - show max 4
    display_items = items[:4]
    item_start_y = height // 3
    item_spacing = (height - item_start_y - 200) // max(len(display_items), 1)

    for i, item in enumerate(display_items):
        idx = i + 1
        idx_text = f"{idx:02d}"
        title = truncate_text(item.get("title", "未知"), 20)

        # Index number
        bbox = draw.textbbox((0, 0), idx_text, font=font_index)
        idx_w = bbox[2] - bbox[0]
        draw.text((width // 3 - 80, item_start_y + i * item_spacing), idx_text, font=font_index, fill=COLORS["accent_blue"])

        # Title text
        title_lines = split_lines_with_max_count(title, font_item, int(width * 0.5), draw, max_lines=2)
        for j, line in enumerate(title_lines):
            draw.text((width // 3, item_start_y + i * item_spacing + j * (get_text_size("测试", font_item, draw)[1] + 6)), line, font=font_item, fill=COLORS["text_primary"])

        # Separator line
        if i < len(display_items) - 1:
            sep_y = item_start_y + (i + 1) * item_spacing - 20
            draw.rectangle([(width // 4, sep_y), (width * 3 // 4, sep_y + 1)], fill=COLORS["border_subtle"])

    # Footer
    footer_text = "AI Frontier Radar · 每日更新"
    bbox = draw.textbbox((0, 0), footer_text, font=font_index)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 100), footer_text, font=font_index, fill=COLORS["text_dim"])

    output_path = frames_dir / "overview.png"
    img.save(output_path, "PNG")

    return {
        "path": output_path,
        "warnings": warnings,
        "template": "overview",
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
        "itemCount": len(display_items),
    }


# ─────────────────────────────────────────
# Keypoint Frame Template
# ─────────────────────────────────────────
def render_keypoint_template(
    index: int,
    total: int,
    category: str,
    title: str,
    body: str,
    source: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """
    Render enhanced keypoint frame with:
    - Top index: 01/06
    - Category tag
    - Main title with highlight support
    - Body text
    - Source
    """
    width, height = resolution
    img = render_gradient_background(width, height)
    draw = ImageDraw.Draw(img)

    warnings = []
    font_size_index = int(FONT_SIZES["keypoint_index"] * (width / 1080))
    font_size_category = int(FONT_SIZES["keypoint_category"] * (width / 1080))
    font_size_title = int(FONT_SIZES["keypoint_title"] * (width / 1080))
    font_size_body = int(FONT_SIZES["keypoint_body"] * (width / 1080))
    font_size_source = int(FONT_SIZES["keypoint_source"] * (width / 1080))

    font_index, w = find_chinese_font(font_size_index)
    font_category, w2 = find_chinese_font(font_size_category)
    font_title, w3 = find_chinese_font(font_size_title)
    font_body, w4 = find_chinese_font(font_size_body)
    font_source, w5 = find_chinese_font(font_size_source)
    warnings.extend(w)
    warnings.extend(w2)
    warnings.extend(w3)
    warnings.extend(w4)
    warnings.extend(w5)

    category_style = get_category_style(category)

    # Left side index
    index_text = f"{index:02d}/{total}"
    draw.text((50, 50), index_text, font=font_index, fill=COLORS["accent_blue"])

    # Top decorative bar
    draw.rectangle([(40, 110), (width - 40, 114)], fill=COLORS["border_subtle"])

    # Category tag
    tag_y = 150
    draw_tag(draw, category, width // 2, tag_y, font_category, category_style)

    # Title area - try to show highlights
    title_max_width = int(width * 0.88)
    title_lines = split_lines_with_max_count(title, font_title, title_max_width, draw, max_lines=3)
    title_line_h = get_text_size("测试", font_title, draw)[1] + 10
    title_start_y = 250

    for i, line in enumerate(title_lines):
        # Check if line contains highlight terms and draw differently
        highlights_in_line = extract_highlights(line)
        if highlights_in_line and i == 0:  # Highlight first line's key numbers
            _draw_text_with_highlights(draw, line, (width - title_max_width) // 2, title_start_y + i * title_line_h, font_title)
        else:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            tw = bbox[2] - bbox[0]
            draw.text(((width - tw) // 2, title_start_y + i * title_line_h), line, font=font_title, fill=COLORS["text_primary"])

    # Divider line
    div_y = title_start_y + len(title_lines) * title_line_h + 30
    draw.rectangle([(width // 4, div_y), (width * 3 // 4, div_y + 2)], fill=COLORS["accent_glow_blue"])

    # Body text
    if body:
        body_max_width = int(width * 0.85)
        body_lines = split_lines_with_max_count(body, font_body, body_max_width, draw, max_lines=5)
        body_line_h = get_text_size("测试", font_body, draw)[1] + 8
        body_start_y = div_y + 40

        for i, line in enumerate(body_lines):
            highlights_in_line = extract_highlights(line)
            if highlights_in_line:
                _draw_text_with_highlights(draw, line, (width - body_max_width) // 2, body_start_y + i * body_line_h, font_body, is_body=True)
            else:
                bbox = draw.textbbox((0, 0), line, font=font_body)
                bw = bbox[2] - bbox[0]
                draw.text(((width - bw) // 2, body_start_y + i * body_line_h), line, font=font_body, fill=COLORS["text_secondary"])

    # Source
    if source:
        source_short = truncate_text(source, 70)
        source_max_width = int(width * 0.8)
        source_lines = wrap_text(source_short, font_source, source_max_width, draw)
        source_line_h = get_text_size("测试", font_source, draw)[1] + 4
        source_start_y = height - 280

        for i, line in enumerate(source_lines[:2]):
            bbox = draw.textbbox((0, 0), line, font=font_source)
            sw = bbox[2] - bbox[0]
            draw.text(((width - sw) // 2, source_start_y + i * source_line_h), line, font=font_source, fill=COLORS["text_tertiary"])

    # Bottom tag
    tag_text = "AI Frontier Radar"
    bbox = draw.textbbox((0, 0), tag_text, font=font_source)
    tw = bbox[2] - bbox[0]
    draw.rounded_rectangle(
        [(width // 2 - tw // 2 - 20, height - 100), (width // 2 + tw // 2 + 20, height - 60)],
        radius=8,
        fill=COLORS["tag_background"],
    )
    draw.text(((width - tw) // 2, height - 95), tag_text, font=font_source, fill=COLORS["tag_text"])

    frame_name = f"frame_{index:03d}.png"
    output_path = frames_dir / frame_name
    img.save(output_path, "PNG")

    return {
        "path": output_path,
        "frame_name": frame_name,
        "warnings": warnings,
        "template": "keypoint",
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
        "category": category,
        "highlights": extract_highlights(title + " " + body),
    }


def _draw_text_with_highlights(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    is_body: bool = False,
) -> None:
    """Draw text with highlighted numbers/keywords."""
    import re

    highlights = extract_highlights(text)
    if not highlights:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x, y), text, font=font, fill=COLORS["text_primary"])
        return

    # Pattern to find highlight terms
    pattern = "|".join(re.escape(h) for h in highlights)
    parts = re.split(f"({pattern})", text)

    current_x = x
    for part in parts:
        if not part:
            continue
        if part in highlights:
            bbox = draw.textbbox((0, 0), part, font=font)
            pw = bbox[2] - bbox[0]
            draw.text((current_x, y), part, font=font, fill=COLORS["highlight_yellow"])
            current_x += pw
        else:
            bbox = draw.textbbox((0, 0), part, font=font)
            pw = bbox[2] - bbox[0]
            color = COLORS["text_secondary"] if is_body else COLORS["text_primary"]
            draw.text((current_x, y), part, font=font, fill=color)
            current_x += pw


# ─────────────────────────────────────────
# Summary Frame Template
# ─────────────────────────────────────────
def render_summary_template(
    conclusions: List[str],
    cta: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """
    Render summary frame with conclusions and CTA.
    """
    width, height = resolution
    img = render_gradient_background(width, height)
    draw = ImageDraw.Draw(img)

    warnings = []
    font_size_title = int(FONT_SIZES["summary_title"] * (width / 1080))
    font_size_body = int(FONT_SIZES["summary_body"] * (width / 1080))
    font_size_cta = int(FONT_SIZES["summary_cta"] * (width / 1080))

    font_title, w = find_chinese_font(font_size_title)
    font_body, w2 = find_chinese_font(font_size_body)
    font_cta, w3 = find_chinese_font(font_size_cta)
    warnings.extend(w)
    warnings.extend(w2)
    warnings.extend(w3)

    # Title
    title_text = "本期结论"
    draw_centered_text(draw, title_text, height // 5, width, font_title, COLORS["highlight_yellow"])

    # Decorative line
    line_y = height // 5 + 60
    draw.rectangle(
        [(width // 4, line_y), (width * 3 // 4, line_y + SPACING["decor_line_height"])],
        fill=COLORS["accent_blue"]
    )

    # Conclusions
    conclusion_start_y = height // 3
    conclusion_spacing = 80

    for i, conclusion in enumerate(conclusions[:5]):
        # Index
        idx_text = f"{i + 1}."
        draw.text((width // 3 - 60, conclusion_start_y + i * conclusion_spacing), idx_text, font=font_body, fill=COLORS["accent_cyan"])

        # Text
        text_max_width = int(width * 0.6)
        text_lines = split_lines_with_max_count(conclusion, font_body, text_max_width, draw, max_lines=2)
        for j, line in enumerate(text_lines):
            draw.text((width // 3, conclusion_start_y + i * conclusion_spacing + j * (get_text_size("测试", font_body, draw)[1] + 6)), line, font=font_body, fill=COLORS["text_primary"])

    # CTA
    cta_y = height - 280
    draw.rectangle(
        [(width // 4, cta_y - 20), (width * 3 // 4, cta_y - 15)],
        fill=COLORS["decor_line"]
    )

    cta_max_width = int(width * 0.8)
    cta_lines = split_lines_with_max_count(cta, font_cta, cta_max_width, draw, max_lines=2)
    cta_line_h = get_text_size("测试", font_cta, draw)[1] + 6
    cta_total_h = len(cta_lines) * cta_line_h
    cta_start_y = cta_y + 20

    for i, line in enumerate(cta_lines):
        bbox = draw.textbbox((0, 0), line, font=font_cta)
        cw = bbox[2] - bbox[0]
        draw.text(((width - cw) // 2, cta_start_y + i * cta_line_h), line, font=font_cta, fill=COLORS["text_tertiary"])

    # Footer
    footer_text = "Video Capability Lab · AI Frontier Radar"
    bbox = draw.textbbox((0, 0), footer_text, font=font_cta)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 80), footer_text, font=font_cta, fill=COLORS["text_dim"])

    output_path = frames_dir / "summary.png"
    img.save(output_path, "PNG")

    return {
        "path": output_path,
        "warnings": warnings,
        "template": "summary",
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
        "conclusionCount": len(conclusions[:5]),
    }
