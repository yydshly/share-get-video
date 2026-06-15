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


def load_background_image(
    path: str,
    width: int,
    height: int,
    darken: float = 0.55,
) -> Image.Image:
    """Load an AI-generated image, cover-crop to (width,height), darken for legibility.

    darken: 0..1，叠加黑色遮罩的不透明度，越大画面越暗、文字越清晰。
    失败时回退到渐变背景。
    """
    try:
        bg = Image.open(path).convert("RGB")
    except Exception:
        return render_gradient_background(width, height)

    # cover-crop（保持比例铺满，居中裁剪）
    src_w, src_h = bg.size
    scale = max(width / src_w, height / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    bg = bg.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    bg = bg.crop((left, top, left + width, top + height))

    # 暗化遮罩（顶部稍轻、底部更重，利于卡片与文字）
    overlay = Image.new("RGB", (width, height), (0, 0, 0))
    a = int(max(0.0, min(1.0, darken)) * 255)
    bg = Image.blend(bg, overlay, a / 255.0)
    return bg


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
    background_path: str | None = None,
) -> Dict[str, Any]:
    """
    Render enhanced cover frame with:
    - Top label: "AI前沿" + 栏目感
    - Large title (更集中)
    - Hook line (V0.3.6-a2: 增加点击理由)
    - 3 prominent signal tags (V0.3.6-a2: 更大更醒目)
    - Background gradient (or AI image) with decorative elements
    - Date and footer
    """
    width, height = resolution
    if background_path:
        img = load_background_image(background_path, width, height, darken=0.5)
        draw = ImageDraw.Draw(img)
    else:
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

    # Top label - V0.3.6-a2: "AI前沿" + 栏目感
    label_text = "AI前沿"
    bbox = draw.textbbox((0, 0), label_text, font=font_label)
    label_w = bbox[2] - bbox[0]
    draw.text(((width - label_w) // 2, line_y + 30), label_text, font=font_label, fill=COLORS["accent_cyan"])

    # Main title - V0.3.6-a2: 更集中，向上移动
    title_max_width = int(width * 0.88)
    title_lines = split_lines_with_max_count(title, font_title, title_max_width, draw, max_lines=3)
    title_line_h = get_text_size("测试", font_title, draw)[1] + 12
    # V0.3.6-a2: 标题上移，给hook line留空间
    title_start_y = height // 2 - len(title_lines) * title_line_h // 2 - 140

    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, title_start_y + i * title_line_h), line, font=font_title, fill=COLORS["text_primary"])

    # Hook line - V0.3.6-a2: 增加点击理由
    hook_text = subtitle if subtitle else "今天这3件事，值得注意"
    hook_font_size = int(font_size_subtitle * 0.9)
    font_hook, _ = find_chinese_font(hook_font_size)
    hook_y = title_start_y + len(title_lines) * title_line_h + 20
    draw_centered_text(draw, hook_text, hook_y, width, font_hook, COLORS["highlight_yellow"])

    # Signal tags - V0.3.6-a2: 更大更醒目
    tags_y = hook_y + 80  # V0.3.6-a2: 调整位置给hook line腾空间
    tag_spacing = 40       # V0.3.6-a2: 标签间距增大
    total_tags_width = 0
    # V0.3.6-a2: 使用更大的字号
    font_size_tag_larger = int(font_size_tag * 1.25)
    font_tag_larger, _ = find_chinese_font(font_size_tag_larger)
    for tag in tags[:3]:
        style = get_category_style("默认")
        bbox = draw.textbbox((0, 0), tag, font=font_tag_larger)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        padding = 20  # V0.3.6-a2: 更大内边距
        total_tags_width += tw + padding * 2 + tag_spacing

    total_tags_width -= tag_spacing
    current_x = (width - total_tags_width) // 2

    for i, tag in enumerate(tags[:3]):
        style = get_category_style("默认")
        bbox = draw.textbbox((0, 0), tag, font=font_tag_larger)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        padding = 20  # V0.3.6-a2: 更大内边距
        tag_w = tw + padding * 2
        tag_h = th + padding

        # V0.3.6-a2: 更醒目的卡片样式
        draw.rounded_rectangle(
            [(current_x, tags_y - tag_h // 2), (current_x + tag_w, tags_y + tag_h // 2)],
            radius=14,  # V0.3.6-a2: 更大圆角
            fill=style["bg"],
            outline=style["border"],
            width=2,     # V0.3.6-a2: 更粗边框
        )
        draw.text((current_x + padding, tags_y - th // 2 - 2), tag, font=font_tag_larger, fill=style["text"])
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
    Render overview frame showing top 4 key points as compact cards.
    V0.3.6-a2: Converted from text list to card list for better visual focus.
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

    # Title - V0.3.6-a2: 更集中
    title_text = "今日重点"
    title_y = int(height * 0.12)
    draw_centered_text(draw, title_text, title_y, width, font_title, COLORS["highlight_yellow"])

    # Decorative line under title
    line_y = title_y + 70
    draw.rectangle(
        [(width // 4, line_y), (width * 3 // 4, line_y + SPACING["decor_line_height"])],
        fill=COLORS["accent_blue"]
    )

    # Cards layout - V0.3.6-a2: 3条卡片集中在画面中部
    display_items = items[:3]  # V0.3.6-a2: 最多3条，减少空间浪费
    card_margin_h = int(width * 0.08)
    card_width = width - card_margin_h * 2
    card_height = int(height * 0.18)  # V0.3.6-a2: 固定卡片高度
    card_gap = int(height * 0.03)     # V0.3.6-a2: 卡片间距
    cards_start_y = int(height * 0.32)  # V0.3.6-a2: 卡片起始位置

    for i, item in enumerate(display_items):
        card_y = cards_start_y + i * (card_height + card_gap)
        card_x = card_margin_h

        # Card background - V0.3.6-a2: 半透明卡片
        card_bg = blend_colors(COLORS["bg_card"], COLORS["bg_primary"], 0.3)
        draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_width, card_y + card_height)],
            radius=16,
            fill=card_bg,
            outline=COLORS["border_active"],
            width=1,
        )

        # Left accent bar
        accent_bar_w = 6
        draw.rounded_rectangle(
            [(card_x + 16, card_y + 20), (card_x + 16 + accent_bar_w, card_y + card_height - 20)],
            radius=3,
            fill=COLORS["accent_blue"],
        )

        # Index number - V0.3.6-a2: 更醒目
        idx_text = f"{i+1:02d}"
        bbox_idx = draw.textbbox((0, 0), idx_text, font=font_index)
        idx_w = bbox_idx[2] - bbox_idx[0]
        idx_h = bbox_idx[3] - bbox_idx[1]
        idx_x = card_x + 40
        idx_y = card_y + (card_height - idx_h) // 2 - 2
        draw.text((idx_x, idx_y), idx_text, font=font_index, fill=COLORS["accent_blue"])

        # Title text - V0.3.6-a2: 更大，更集中
        title = truncate_text(item.get("title", "未知"), 24)
        title_x = idx_x + idx_w + 30
        avail_title_width = card_width - (title_x - card_x) - 30
        title_lines = split_lines_with_max_count(title, font_item, avail_title_width, draw, max_lines=2)
        line_h = get_text_size("测试", font_item, draw)[1] + 8
        total_text_h = len(title_lines) * line_h
        text_start_y = card_y + (card_height - total_text_h) // 2 - 2
        for j, line in enumerate(title_lines):
            draw.text((title_x, text_start_y + j * line_h), line, font=font_item, fill=COLORS["text_primary"])

    # Footer
    footer_text = "AI前沿 · 每日更新"
    bbox = draw.textbbox((0, 0), footer_text, font=font_index)
    fw = bbox[2] - bbox[0]
    draw.text(((width - fw) // 2, height - 80), footer_text, font=font_index, fill=COLORS["text_dim"])

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
def _draw_lines_with_highlights(
    draw: ImageDraw.ImageDraw,
    lines: List[str],
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    line_h: int,
    base_color: Tuple[int, int, int],
    highlight_color: Tuple[int, int, int],
    emphasis_terms: List[str] | None = None,
) -> int:
    """Draw wrapped lines left-aligned, highlighting explicit terms or auto-extracted numbers.

    V0.3.6-b2: priority = explicit emphasis_terms > auto-extract > none.
    Returns bottom y.
    """
    import re
    text_all = " ".join(lines)
    # V0.3.6-b2: explicit emphasisTerms take priority over auto-extract
    if emphasis_terms:
        highlights = list(dict.fromkeys(e for e in emphasis_terms if e and isinstance(e, str)))
    else:
        highlights = extract_highlights(text_all)
    pattern = "|".join(re.escape(h) for h in highlights) if highlights else None

    cur_y = y
    for line in lines:
        cur_x = x
        if pattern:
            parts = re.split(f"({pattern})", line)
        else:
            parts = [line]
        for part in parts:
            if not part:
                continue
            color = highlight_color if (highlights and part in highlights) else base_color
            draw.text((cur_x, cur_y), part, font=font, fill=color)
            cur_x += draw.textbbox((0, 0), part, font=font)[2] - draw.textbbox((0, 0), part, font=font)[0]
        cur_y += line_h
    return cur_y


def render_keypoint_template(
    index: int,
    total: int,
    category: str,
    title: str,
    body: str,
    source: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
    background_path: str | None = None,
    emphasis_terms: list[str] | None = None,
) -> Dict[str, Any]:
    """
    Render a keypoint card that FILLS the card with auto-fit fonts and never
    truncates content:
    - Header: big index + optional category tag (hidden when default/empty)
    - Headline (`title`): auto-fit large text
    - Detail (`body`): auto-fit body text, fills remaining space
    - V0.3.6-b2: explicit emphasisTerms take priority for highlighting; fallback to auto-extract
    - Numbers are highlighted; placeholder source is dropped
    - background_path: 若提供 AI 生成的背景图，则用其作背景 + 半透明信息卡
    """
    from app.video_lab.renderers.text_layout import fit_wrapped_text

    width, height = resolution

    # Card geometry
    card_x1 = int(width * 0.06)
    card_y1 = int(height * 0.12)
    card_x2 = int(width * 0.94)
    card_y2 = int(height * 0.92)

    if background_path:
        # AI 背景图 + 半透明卡片（图透出来、文字仍清晰）
        base = load_background_image(background_path, width, height, darken=0.45).convert("RGBA")
        card_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cdraw = ImageDraw.Draw(card_layer)
        card_rgb = COLORS["bg_card"]
        cdraw.rounded_rectangle(
            [(card_x1, card_y1), (card_x2, card_y2)],
            radius=20,
            fill=(card_rgb[0], card_rgb[1], card_rgb[2], 205),  # ~80% opaque
            outline=(COLORS["border_active"][0], COLORS["border_active"][1], COLORS["border_active"][2], 255),
            width=2,
        )
        img = Image.alpha_composite(base, card_layer).convert("RGB")
        draw = ImageDraw.Draw(img)
    else:
        img = render_gradient_background(width, height)
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [(card_x1, card_y1), (card_x2, card_y2)],
            radius=20,
            fill=COLORS["bg_card"],
            outline=COLORS["border_active"],
            width=2,
        )

    warnings = []
    scale = width / 1080

    font_size_index = int(FONT_SIZES["keypoint_index"] * scale)
    font_size_category = int(FONT_SIZES["keypoint_category"] * scale)
    font_index, w = find_chinese_font(font_size_index)
    font_category, w2 = find_chinese_font(font_size_category)
    warnings.extend(w)
    warnings.extend(w2)

    inner_x = card_x1 + 50
    inner_w = (card_x2 - card_x1) - 100

    # Header: big index + " / total"
    header_y = card_y1 + 50
    big_idx_text = f"{index:02d}"
    big_idx_font_size = int(FONT_SIZES["highlight_large"] * scale)
    big_idx_font, _w_big = find_chinese_font(big_idx_font_size)
    warnings.extend(_w_big)
    draw.text((inner_x, header_y), big_idx_text, font=big_idx_font, fill=COLORS["accent_blue"])
    idx_w = draw.textbbox((0, 0), big_idx_text, font=big_idx_font)[2]
    draw.text((inner_x + idx_w + 12, header_y + 34), f"/ {total:02d}", font=font_index, fill=COLORS["text_tertiary"])

    # Category tag — only when meaningful
    show_category = bool(category) and category not in ("默认", "default", "")
    if show_category:
        cat_style = get_category_style(category)
        draw_tag(draw, category, card_x2 - 140, header_y + 40, font_category, cat_style)

    # Header divider
    bar_y = header_y + 130
    draw.rectangle([(inner_x, bar_y), (card_x2 - 50, bar_y + 2)], fill=COLORS["border_subtle"])

    # Content region (everything below the divider)
    content_top = bar_y + 44
    content_bottom = card_y2 - 56
    content_h = content_bottom - content_top

    headline = (title or "").strip()
    detail = (body or "").strip()

    # Allocate vertical space: headline gets up to ~45% when detail exists
    if detail:
        headline_box_h = int(content_h * 0.42)
        detail_box_h = content_h - headline_box_h - 30
    else:
        headline_box_h = content_h
        detail_box_h = 0

    # Headline — auto-fit large, minimum 40px for readability on mobile
    h_font, h_lines, h_size, h_line_h, h_overflow = fit_wrapped_text(
        headline, inner_w, headline_box_h, draw,
        size_max=int(80 * scale), size_min=int(40 * scale), line_spacing=int(18 * scale),
    )
    # V0.3.6-b2: pass emphasis_terms for priority highlighting
    end_y = _draw_lines_with_highlights(
        draw, h_lines, inner_x, content_top, h_font, h_line_h,
        COLORS["text_primary"], COLORS["highlight_yellow"],
        emphasis_terms=emphasis_terms,
    )
    if h_overflow:
        warnings.append(f"keypoint {index}: headline overflow (text truncated visually)")

    # Detail — placed right under the headline, fills remaining space
    if detail:
        detail_top = end_y + int(40 * scale)
        avail_h = content_bottom - detail_top
        d_font, d_lines, d_size, d_line_h, d_overflow = fit_wrapped_text(
            detail, inner_w, avail_h, draw,
            size_max=int(52 * scale), size_min=int(28 * scale), line_spacing=int(14 * scale),
        )
        # V0.3.6-b2: pass emphasis_terms for priority highlighting
        _draw_lines_with_highlights(
            draw, d_lines, inner_x, detail_top, d_font, d_line_h,
            COLORS["text_secondary"], COLORS["highlight_yellow"],
            emphasis_terms=emphasis_terms,
        )
        if d_overflow:
            warnings.append(f"keypoint {index}: detail overflow (text truncated visually)")

    # Source — only when it's real (skip placeholder like "依据 1")
    src = (source or "").strip()
    is_placeholder = (not src) or src.replace("依据", "").replace("：", "").replace(":", "").replace(" ", "").isdigit()
    if src and not is_placeholder:
        font_source, w5 = find_chinese_font(int(FONT_SIZES["keypoint_source"] * scale))
        warnings.extend(w5)
        src_lines = wrap_text(truncate_text(src, 60), font_source, inner_w, draw)[:1]
        draw.text((inner_x, card_y2 - 50), src_lines[0], font=font_source, fill=COLORS["text_tertiary"])

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
        "highlights": (emphasis_terms if emphasis_terms else extract_highlights(headline + " " + detail)),
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
