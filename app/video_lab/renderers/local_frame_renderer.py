"""
Local Frame Renderer - 使用 Pillow 生成信息卡片 PNG 帧
V0.2.4: 使用 AI Frontier Dark 视觉模板
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from app.video_lab.renderers.text_layout import (
    find_chinese_font,
    wrap_text,
    truncate_text,
    split_title_and_body,
    split_headline_and_detail,
    get_text_size,
    extract_highlights_by_mode,
    fit_wrapped_text,
    split_lines_with_max_count,
)
from app.video_lab.renderers.visual_theme import (
    TEMPLATE_VERSION,
    VISUAL_PRESET,
    TRANSITION_TYPE,
    TRANSITION_FRAMES_DEFAULT,
    COLORS,
    FONT_SIZES,
    SPACING,
)
from app.video_lab.renderers.frame_templates import (
    render_gradient_background,
    render_cover_template,
    render_overview_template,
    render_keypoint_template,
    render_summary_template,
    draw_decorative_elements,
    draw_centered_text,
)
from app.video_lab.renderers.transition_composer import (
    generate_fade_frames,
    build_frame_sequence_with_transitions,
)


# ─────────────────────────────────────────
# Legacy colors for backward compatibility
# ─────────────────────────────────────────
LEGACY_COLORS = {
    "background": (15, 15, 35),
    "background_secondary": (25, 25, 60),
    "primary": (255, 255, 255),
    "secondary": (180, 190, 210),
    "accent": (99, 155, 255),
    "accent_glow": (130, 180, 255),
    "highlight": (255, 220, 80),
    "tag_bg": (40, 60, 120),
    "gradient_top": (20, 20, 50),
    "gradient_bottom": (10, 10, 30),
}


def render_gradient_background_legacy(width: int, height: int) -> Image.Image:
    """Create legacy gradient background for backward compatibility."""
    img = Image.new("RGB", (width, height), LEGACY_COLORS["background"])
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(LEGACY_COLORS["gradient_top"][0] * (1 - ratio) + LEGACY_COLORS["gradient_bottom"][0] * ratio)
        g = int(LEGACY_COLORS["gradient_top"][1] * (1 - ratio) + LEGACY_COLORS["gradient_bottom"][1] * ratio)
        b = int(LEGACY_COLORS["gradient_top"][2] * (1 - ratio) + LEGACY_COLORS["gradient_bottom"][2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def draw_centered_text_legacy(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_y: int,
    width: int,
    font: ImageFont.FreeTypeFont,
    color: Tuple[int, int, int],
    max_width_ratio: float = 0.85,
) -> int:
    """Legacy centered text drawing."""
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


def _is_report_source_bound_style(style_params: dict) -> bool:
    return (
        isinstance(style_params, dict)
        and style_params.get("sourceBound") is True
        and style_params.get("generationMode") == "information_summary"
        and style_params.get("inputProfile") == "report_overview_items"
        and isinstance(style_params.get("informationSummaryPlan"), dict)
    )


def _first_sentence(text: str, max_len: int = 46) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    first = text
    for sep in ("。", "！", "？", "\n"):
        if sep in first:
            first = first.split(sep, 1)[0] + (sep if sep in "。！？" else "")
            break
    return truncate_text(first, max_len)


def _render_report_text_frame(
    *,
    frame_name: str,
    title: str,
    body: str,
    frames_dir: Path,
    resolution: Tuple[int, int],
    eyebrow: str = "",
    footer: str = "",
    background_path: str | None = None,
) -> dict:
    width, height = resolution
    if background_path:
        from app.video_lab.renderers.frame_templates import load_background_image
        img = load_background_image(background_path, width, height, darken=0.5)
    else:
        img = render_gradient_background(width, height)
        draw = ImageDraw.Draw(img)
        draw_decorative_elements(draw, width, height)
    draw = ImageDraw.Draw(img)

    warnings: list[str] = []
    scale = width / 1080
    font_eyebrow, w1 = find_chinese_font(int(28 * scale))
    font_title, w2 = find_chinese_font(int(58 * scale))
    font_body_base, w3 = find_chinese_font(int(38 * scale))
    font_footer, w4 = find_chinese_font(int(24 * scale))
    warnings.extend(w1 + w2 + w3 + w4)

    card_x1 = int(width * 0.07)
    card_y1 = int(height * 0.12)
    card_x2 = int(width * 0.93)
    card_y2 = int(height * 0.90)
    inner_x = card_x1 + int(48 * scale)
    inner_w = (card_x2 - card_x1) - int(96 * scale)

    draw.rounded_rectangle(
        [(card_x1, card_y1), (card_x2, card_y2)],
        radius=int(22 * scale),
        fill=COLORS["bg_card"],
        outline=COLORS["border_active"],
        width=2,
    )

    y = card_y1 + int(46 * scale)
    if eyebrow:
        draw.text((inner_x, y), eyebrow, font=font_eyebrow, fill=COLORS["accent_cyan"])
        y += int(46 * scale)

    title_lines = split_lines_with_max_count((title or "").strip(), font_title, inner_w, draw, max_lines=3)
    title_line_h = get_text_size("测试", font_title, draw)[1] + int(14 * scale)
    for line in title_lines:
        draw.text((inner_x, y), line, font=font_title, fill=COLORS["text_primary"])
        y += title_line_h

    y += int(24 * scale)
    draw.rectangle([(inner_x, y), (card_x2 - int(48 * scale), y + 3)], fill=COLORS["accent_blue"])
    y += int(42 * scale)

    body_bottom = card_y2 - int(96 * scale)
    body_h = max(120, body_bottom - y)
    font_body, body_lines, body_size, body_line_h, overflow = fit_wrapped_text(
        (body or "").strip(),
        inner_w,
        body_h,
        draw,
        size_max=int(42 * scale),
        size_min=int(24 * scale),
        line_spacing=int(12 * scale),
    )
    for line in body_lines:
        draw.text((inner_x, y), line, font=font_body, fill=COLORS["text_secondary"])
        y += body_line_h
    if overflow:
        warnings.append(f"{frame_name}: report body overflow")

    if footer:
        footer_lines = split_lines_with_max_count(footer, font_footer, inner_w, draw, max_lines=2)
        fy = card_y2 - int(70 * scale)
        for line in footer_lines:
            draw.text((inner_x, fy), line, font=font_footer, fill=COLORS["text_dim"])
            fy += int(32 * scale)

    output_path = frames_dir / frame_name
    img.save(output_path, "PNG")
    return {
        "path": output_path,
        "frame_name": frame_name,
        "warnings": warnings,
        "template": "report_text",
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
        "title": title,
        "body": body,
    }


def _build_report_frame_sequence(
    *,
    frame_outputs: list[dict],
    duration_per_frame: dict,
    frames_dir: Path,
    enable_transitions: bool,
    transition_frames: int,
) -> tuple[dict, dict]:
    main_frame_paths = [Path(f["path"]) for f in frame_outputs]
    if enable_transitions and len(main_frame_paths) >= 2:
        trans_result = build_frame_sequence_with_transitions(
            frame_paths=main_frame_paths,
            frames_dir=frames_dir,
            transition_frames=transition_frames,
            enabled=True,
            main_durations=duration_per_frame,
        )
        duration_by_path = trans_result["duration_per_frame"]
        transition_info = {
            "transitionEnabled": True,
            "transitionType": TRANSITION_TYPE,
            "transitionFrames": trans_result["transition_count"],
            "transition_sequence": trans_result["sequence"],
            "transition_duration_per_frame": trans_result["duration_per_frame"],
        }
    else:
        sequence = [{"path": str(p), "type": "main", "index": i} for i, p in enumerate(main_frame_paths)]
        duration_by_path = {}
        for f in frame_outputs:
            fp = Path(f["path"])
            duration_by_path[str(fp)] = duration_per_frame.get(fp.name, 0.0)
            duration_by_path[fp.name] = duration_per_frame.get(fp.name, 0.0)
        transition_info = {
            "transitionEnabled": False,
            "transitionType": None,
            "transitionFrames": 0,
            "transition_sequence": sequence,
            "transition_duration_per_frame": {},
        }
    return transition_info, duration_by_path


def _generate_report_source_bound_frames(
    *,
    experiment_id: str,
    structured: dict,
    key_points: dict,
    target_duration_sec: int,
    resolution: Tuple[int, int],
    enable_transitions: bool,
    transition_frames: int,
    include_overview: bool,
    include_summary: bool,
    segment_durations: list | None,
    backgrounds: dict | None,
    style_params: dict,
) -> dict:
    from app.video_lab.renderers.file_store import get_frames_dir as _get_frames_dir

    frames_dir = _get_frames_dir(experiment_id)
    frame_outputs: list[dict] = []
    duration_per_frame: dict[str, float] = {}
    all_warnings: list[str] = []

    info_plan = style_params.get("informationSummaryPlan") or {}
    plan_overview = key_points.get("overview") or info_plan.get("overview") or {}
    overview_title = (plan_overview.get("title") or "内容概览").strip()
    overview_summary = (plan_overview.get("summary") or structured.get("lead") or "").strip()
    report_title = (
        key_points.get("reportTitle")
        or info_plan.get("reportTitle")
        or info_plan.get("videoTitle")
        or (info_plan.get("metadata") or {}).get("title")
        or style_params.get("coverTitle")
        or overview_title
    )
    source_refs = key_points.get("sourceRefs") or []
    evidence_policy = style_params.get("evidencePolicy") or info_plan.get("evidencePolicy")
    kps = key_points.get("keyPoints") or key_points.get("key_points") or []

    seg_durs = [float(s.get("durationSec", 0)) for s in (segment_durations or [])]
    opening_dur = seg_durs[0] if seg_durs else 6.0
    item_durs = seg_durs[1:-1] if len(seg_durs) >= len(kps) + 2 else []
    closing_dur = seg_durs[-1] if len(seg_durs) >= 2 else 4.0

    cover = _render_report_text_frame(
        frame_name="cover.png",
        title=report_title,
        body=_first_sentence(overview_summary) or "AI 前沿报告",
        eyebrow="报告摘要",
        footer=datetime.now().strftime("%Y年%m月%d日"),
        frames_dir=frames_dir,
        resolution=resolution,
        background_path=(backgrounds or {}).get("cover"),
    )
    frame_outputs.append({"type": "cover", "path": cover["path"], "frame_name": "cover.png", "template": "report_cover", "title": report_title, "body": cover["body"], "templateVersion": TEMPLATE_VERSION, "visualPreset": VISUAL_PRESET})
    duration_per_frame["cover.png"] = max(1.8, min(opening_dur * 0.25, 3.0))
    all_warnings.extend(cover.get("warnings", []))

    if include_overview:
        overview = _render_report_text_frame(
            frame_name="report_overview.png",
            title=overview_title or "内容概览",
            body=overview_summary,
            eyebrow="首页总览",
            footer="报告第一段总览",
            frames_dir=frames_dir,
            resolution=resolution,
            background_path=(backgrounds or {}).get("cover"),
        )
        frame_outputs.append({"type": "overview", "path": overview["path"], "frame_name": "report_overview.png", "template": "report_overview", "title": overview_title, "body": overview_summary, "templateVersion": TEMPLATE_VERSION, "visualPreset": VISUAL_PRESET})
        duration_per_frame["report_overview.png"] = max(2.0, opening_dur - duration_per_frame["cover.png"])
        all_warnings.extend(overview.get("warnings", []))

    total = max(len(kps), 1)
    fallback_item_duration = max(3.5, (target_duration_sec - opening_dur - closing_dur) / max(total, 1))
    for i, kp in enumerate(kps, 1):
        headline = (kp.get("headline") or kp.get("title") or f"信息点 {i}").strip()
        detail = (kp.get("display") or kp.get("body") or "").strip()
        frame_result = render_keypoint_template(
            index=i,
            total=total,
            category="",
            title=headline,
            body=detail,
            source="",
            frames_dir=frames_dir,
            resolution=resolution,
            background_path=(backgrounds or {}).get(i),
            emphasis_terms=kp.get("emphasisTerms") or None,
            metrics=kp.get("metrics"),
        )
        frame_outputs.append({
            "type": "keypoint",
            "frame_num": i,
            "path": frame_result["path"],
            "frame_name": frame_result["frame_name"],
            "template": "report_keypoint",
            "title": headline,
            "body": detail,
            "templateVersion": TEMPLATE_VERSION,
            "visualPreset": VISUAL_PRESET,
            "highlights": frame_result.get("highlights", []),
            "metrics": frame_result.get("metrics"),
        })
        duration_per_frame[frame_result["frame_name"]] = round(max(2.0, item_durs[i - 1] if i - 1 < len(item_durs) else fallback_item_duration), 2)
        all_warnings.extend(frame_result.get("warnings", []))

    conclusion = info_plan.get("conclusion") if isinstance(info_plan.get("conclusion"), dict) else {}
    conclusion_text = (conclusion.get("text") or "").strip()
    if include_summary and conclusion_text:
        result = _render_report_text_frame(
            frame_name="report_conclusion.png",
            title=conclusion.get("title") or "趋势总结",
            body=conclusion_text,
            eyebrow="尾部总结",
            frames_dir=frames_dir,
            resolution=resolution,
        )
        frame_outputs.append({"type": "conclusion", "path": result["path"], "frame_name": "report_conclusion.png", "template": "report_conclusion", "title": conclusion.get("title") or "趋势总结", "body": conclusion_text, "templateVersion": TEMPLATE_VERSION, "visualPreset": VISUAL_PRESET})
        duration_per_frame["report_conclusion.png"] = round(max(1.5, closing_dur), 2)
        all_warnings.extend(result.get("warnings", []))

    source_lines: list[str] = []
    if evidence_policy == "ending_sources":
        for ref in source_refs:
            for ev in ref.get("evidence", []) or []:
                if ev and ev not in source_lines:
                    source_lines.append(ev)
    if source_lines:
        result = _render_report_text_frame(
            frame_name="report_sources.png",
            title="资料来源",
            body="\n".join(source_lines),
            eyebrow="Sources",
            frames_dir=frames_dir,
            resolution=resolution,
        )
        frame_outputs.append({"type": "sources", "path": result["path"], "frame_name": "report_sources.png", "template": "report_sources", "title": "资料来源", "body": "\n".join(source_lines), "templateVersion": TEMPLATE_VERSION, "visualPreset": VISUAL_PRESET})
        duration_per_frame["report_sources.png"] = 3.0
        all_warnings.extend(result.get("warnings", []))

    transition_info, duration_by_path = _build_report_frame_sequence(
        frame_outputs=frame_outputs,
        duration_per_frame=duration_per_frame,
        frames_dir=frames_dir,
        enable_transitions=enable_transitions,
        transition_frames=transition_frames,
    )
    total_duration = round(sum(duration_per_frame.get(Path(f["path"]).name, 0.0) for f in frame_outputs), 2)
    return {
        "frames": frame_outputs,
        "cover": frame_outputs[0]["path"] if frame_outputs else None,
        "duration_per_frame": duration_per_frame,
        "total_frames": len(frame_outputs),
        "total_duration_sec": total_duration,
        "warnings": all_warnings,
        "visualPreset": VISUAL_PRESET,
        "templateVersion": TEMPLATE_VERSION,
        "transitionEnabled": transition_info["transitionEnabled"],
        "transitionType": transition_info["transitionType"],
        "transitionFrames": transition_info["transitionFrames"],
        "highlightTerms": [],
        "overview_frame": next((f["path"] for f in frame_outputs if f["type"] == "overview"), None),
        "summary_frame": next((f["path"] for f in frame_outputs if f["type"] in ("conclusion", "sources")), None),
        "frameSequence": transition_info["transition_sequence"],
        "durationByPath": duration_by_path,
        "frameSequenceCount": len(transition_info["transition_sequence"]),
        "highlightMode": "report_source_bound",
        "includeOverview": include_overview,
        "includeSummary": include_summary,
        "structureType": "report_source_bound",
    }


# ─────────────────────────────────────────
# V0.2.4 Frame Generation with Transitions
# ─────────────────────────────────────────

def generate_frames(
    experiment_id: str,
    structured: dict,
    key_points: dict,
    target_duration_sec: int,
    resolution: Tuple[int, int] = (1080, 1920),
    enable_transitions: bool = True,
    transition_frames: int = TRANSITION_FRAMES_DEFAULT,
    highlight_mode: str = "auto",
    include_overview: bool = True,
    include_summary: bool = True,
    segment_durations: list | None = None,
    backgrounds: dict | None = None,
    style_params: dict | None = None,
) -> dict:
    """
    Generate all frames using AI Frontier Dark templates.
    Includes cover, overview, keypoints, and summary frames with optional fade transitions.

    Args:
        experiment_id: Experiment ID for directory naming
        structured: Structured content from content_structurer
        key_points: Key points from extractor
        target_duration_sec: Target video duration in seconds
        resolution: Video resolution (width, height)
        enable_transitions: Whether to generate fade transitions
        transition_frames: Number of intermediate frames per transition
        highlight_mode: Highlight extraction mode ('auto', 'numbers', 'none')
        include_overview: Whether to generate overview frame (V0.2.5.1)
        include_summary: Whether to generate summary frame (V0.2.5.1)

    Args:
        experiment_id: Experiment ID for directory naming
        structured: Structured content from content_structurer
        key_points: Key points from extractor
        target_duration_sec: Target video duration in seconds
        resolution: Video resolution (width, height)
        enable_transitions: Whether to generate fade transitions
        transition_frames: Number of intermediate frames per transition
        highlight_mode: Highlight extraction mode ('auto', 'numbers', 'none')

    Returns:
        Dict with frames, durations, transitions, and metadata
    """
    from app.video_lab.renderers.file_store import get_frames_dir as _get_frames_dir

    frames_dir = _get_frames_dir(experiment_id)
    width, height = resolution

    all_warnings = []
    frame_outputs = []
    duration_per_frame = {}

    # 样式参数（配色/对齐/图标），来自调试台/对比页参数
    sp = style_params or {}
    if _is_report_source_bound_style(sp):
        return _generate_report_source_bound_frames(
            experiment_id=experiment_id,
            structured=structured,
            key_points=key_points,
            target_duration_sec=target_duration_sec,
            resolution=resolution,
            enable_transitions=enable_transitions,
            transition_frames=transition_frames,
            include_overview=include_overview,
            include_summary=include_summary,
            segment_durations=segment_durations,
            backgrounds=backgrounds,
            style_params=sp,
        )

    def _color(v):
        if isinstance(v, (list, tuple)) and len(v) >= 3:
            return (int(v[0]), int(v[1]), int(v[2]))
        if isinstance(v, str) and v.startswith("#") and len(v) == 7:
            try:
                return (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16))
            except ValueError:
                return None
        return None

    kp_title_color = _color(sp.get("titleColor"))
    kp_body_color = _color(sp.get("bodyColor"))
    kp_highlight_color = _color(sp.get("highlightColor"))
    kp_content_align = sp.get("contentAlign", "top")
    kp_icon = sp.get("icon", "")
    # V0.3.6-quality-p0-fix: showDataViz=false disables metrics visualization
    show_data_viz = sp.get("showDataViz", True) not in (False, "false", "False", 0)
    # 主题自适应：按每条语义自动配高亮色/图标（显式样式优先，可用 themeAdaptive=false 关闭）
    theme_adaptive = sp.get("themeAdaptive", True) not in (False, "false", "False", 0)
    from app.video_lab.renderers.theme_presets import resolve_shot_tone, tone_to_style

    kps = key_points.get("keyPoints") or key_points.get("key_points") or []
    num_keypoints = len(kps)
    if num_keypoints == 0:
        num_keypoints = 1

    # V0.3.8.2 Duration allocation - reduce chrome, give keypoints more time
    cover_duration = 2.0
    overview_duration = 5.0
    summary_duration = 2.0
    available_for_keypoints = target_duration_sec - cover_duration - overview_duration - summary_duration
    keypoint_duration = max(3.5, available_for_keypoints / max(num_keypoints, 1))

    # Date string
    date_str = datetime.now().strftime("%Y年%m月%d日")

    # Get tags for cover from first 3 keypoints (use clean headline, not mid-word cut)
    cover_tags = []
    for kp in kps[:3]:
        head = (kp.get("headline") or "").strip() or split_headline_and_detail(kp.get("title", ""))[0]
        tag = truncate_text(head.strip(), 12)
        if tag:
            cover_tags.append(tag)

    # ─────────────────────────────────────────
    # Cover Frame
    # ─────────────────────────────────────────
    lead_text = structured.get("lead", "")
    # 用首个分句（冒号前）作为干净标题，避免在句中硬截断
    cover_headline, _ = split_headline_and_detail(lead_text)
    cover_result = render_cover_template(
        title=cover_headline or lead_text[:20] or "AI 前沿资讯",
        subtitle="今日要点速览",
        tags=cover_tags if cover_tags else ["安全风险", "人机协作", "企业落地"],
        date_str=date_str,
        frames_dir=frames_dir,
        resolution=resolution,
        background_path=(backgrounds or {}).get("cover"),
    )
    frame_outputs.append({
        "type": "cover",
        "path": cover_result["path"],
        "template": "cover",
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
    })
    duration_per_frame["cover.png"] = cover_duration
    all_warnings.extend(cover_result.get("warnings", []))

    # ─────────────────────────────────────────
    # Overview Frame (V0.2.4, conditional V0.2.5.1)
    # ─────────────────────────────────────────
    overview_result = None
    if include_overview:
        overview_items = []
        for kp in kps[:4]:
            ov_title = (kp.get("headline") or "").strip() or split_headline_and_detail(kp.get("title", "未知"))[0]
            overview_items.append({
                "title": truncate_text(ov_title, 16),
                "category": (kp.get("category") or "").strip(),
            })

        overview_result = render_overview_template(
            items=overview_items,
            frames_dir=frames_dir,
            resolution=resolution,
            # AI 素材路线：概览页复用封面 AI 背景，保持整支视频观感一致
            background_path=(backgrounds or {}).get("cover"),
        )
        frame_outputs.append({
            "type": "overview",
            "path": overview_result["path"],
            "template": "overview",
            "templateVersion": TEMPLATE_VERSION,
            "visualPreset": VISUAL_PRESET,
        })
        duration_per_frame["overview.png"] = overview_duration
        all_warnings.extend(overview_result.get("warnings", []))

    # ─────────────────────────────────────────
    # Keypoint Frames
    # ─────────────────────────────────────────
    all_highlights = []
    for i, kp in enumerate(kps, 1):
        # 优先使用 LLM 规划的 headline/display；否则从整句 title 切分
        headline = (kp.get("headline") or "").strip()
        detail = (kp.get("display") or "").strip()
        if not headline and not detail:
            full_text = kp.get("title", "").strip()
            headline, detail = split_headline_and_detail(full_text)
            kp_body = (kp.get("body", "") or "").strip()
            if kp_body and not kp_body.replace("依据", "").replace(" ", "").isdigit():
                detail = kp_body if not detail else f"{detail} {kp_body}"
        category = (kp.get("category", "") or "").strip()  # 空/默认时模板自动隐藏

        # V0.3.6-b2: carry emphasisTerms from keypoint dict; pass through for priority highlighting
        emphasis_terms: Optional[List[str]] = kp.get("emphasisTerms") or None

        # V0.2.5: Extract highlights based on highlight_mode (for tracking only)
        highlights = extract_highlights_by_mode(f"{headline} {detail}", highlight_mode)
        all_highlights.extend(highlights)

        # 主题自适应：每条按语义配高亮色/图标（显式样式优先）
        eff_highlight = kp_highlight_color
        eff_icon = kp_icon
        card_tone = ""
        if theme_adaptive:
            card_tone = resolve_shot_tone(kp)
            preset = tone_to_style(card_tone)
            if eff_highlight is None:
                eff_highlight = _color(preset["highlight"])
            if not eff_icon:
                eff_icon = preset["icon"]

        frame_result = render_keypoint_template(
            index=i,
            total=num_keypoints,
            category=category,
            title=headline,
            body=detail,
            source="",
            frames_dir=frames_dir,
            resolution=resolution,
            background_path=(backgrounds or {}).get(i),
            emphasis_terms=emphasis_terms,
            title_color=kp_title_color,
            body_color=kp_body_color,
            highlight_color=eff_highlight,
            content_align=kp_content_align,
            icon=eff_icon,
            # V0.3.6-quality-p0-fix: showDataViz=false suppresses metrics card
            metrics=kp.get("metrics") if show_data_viz else None,
        )
        frame_name = frame_result["frame_name"]
        frame_outputs.append({
            "type": "keypoint",
            "frame_num": i,
            "path": frame_result["path"],
            "frame_name": frame_name,
            "template": "keypoint",
            "templateVersion": TEMPLATE_VERSION,
            "visualPreset": VISUAL_PRESET,
            "category": category,
            "highlights": frame_result.get("highlights", highlights),
            "metrics": frame_result.get("metrics"),  # V0.3.6-quality-p0
        })
        duration_per_frame[frame_name] = keypoint_duration
        all_warnings.extend(frame_result.get("warnings", []))

    # ─────────────────────────────────────────
    # Summary Frame (conditional V0.2.5.1)
    # ─────────────────────────────────────────
    summary_result = None
    if include_summary:
        # Generate default conclusions from keypoints
        conclusions = []
        for i, kp in enumerate(kps[:5], 1):
            title = truncate_text(kp.get("title", "未知发现"), 30)
            conclusions.append(f"{title}")

        summary_result = render_summary_template(
            conclusions=conclusions if conclusions else ["AI Agent 的能力边界正在被重新评估", "安全与可控性成为产品化关键"],
            cta="适合作为「今日 AI 前沿」视频化分享模板",
            frames_dir=frames_dir,
            resolution=resolution,
        )
        frame_outputs.append({
            "type": "summary",
            "path": summary_result["path"],
            "template": "summary",
            "templateVersion": TEMPLATE_VERSION,
            "visualPreset": VISUAL_PRESET,
        })
        duration_per_frame["summary.png"] = summary_duration
        all_warnings.extend(summary_result.get("warnings", []))

    # ─────────────────────────────────────────
    # A/V 时序对应：每帧时长跟随对应旁白段
    # segment_durations 顺序：[opening, item1..N, closing]
    # 帧顺序：cover, [overview], kp1..N, [summary]
    # ─────────────────────────────────────────
    if segment_durations and len(segment_durations) >= 2:
        seg_durs = [float(s.get("durationSec", 0)) for s in segment_durations]
        opening_dur = seg_durs[0]
        closing_dur = seg_durs[-1]
        item_durs = seg_durs[1:-1]
        kp_frames = [f for f in frame_outputs if f["type"] == "keypoint"]
        if len(item_durs) == len(kp_frames) and len(kp_frames) > 0:
            # cover + overview 共享 opening
            if include_overview:
                cover_d = max(1.5, min(opening_dur * 0.3, 3.0))
                overview_d = max(2.0, opening_dur - cover_d)
            else:
                cover_d = max(1.5, opening_dur)
                overview_d = 0.0
            duration_per_frame["cover.png"] = round(cover_d, 2)
            if include_overview:
                duration_per_frame["overview.png"] = round(overview_d, 2)
            for f, d in zip(kp_frames, item_durs):
                duration_per_frame[f["frame_name"]] = round(max(2.0, d), 2)
            if include_summary:
                duration_per_frame["summary.png"] = round(max(1.5, closing_dur), 2)
            all_warnings.append(f"av-sync: frame durations aligned to {len(segment_durations)} narration segments")

    # ─────────────────────────────────────────
    # Generate Transitions (V0.2.4 enhancement)
    # ─────────────────────────────────────────
    transition_info = {
        "transitionEnabled": enable_transitions,
        "transitionType": TRANSITION_TYPE if enable_transitions else None,
        "transitionFrames": 0,
        "transition_sequence": [],
        "transition_duration_per_frame": {},
    }

    # Build main frame paths for sequence
    main_frame_paths = [Path(f["path"]) for f in frame_outputs]

    if enable_transitions and len(main_frame_paths) >= 2:
        # Pass real main frame durations to build_frame_sequence_with_transitions
        trans_result = build_frame_sequence_with_transitions(
            frame_paths=main_frame_paths,
            frames_dir=frames_dir,
            transition_frames=transition_frames,
            enabled=True,
            main_durations=duration_per_frame,  # Pass real durations by filename
        )

        transition_info["transitionFrames"] = trans_result["transition_count"]
        transition_info["transition_sequence"] = trans_result["sequence"]
        transition_info["transition_duration_per_frame"] = trans_result["duration_per_frame"]

        # Use the sequence's duration_per_frame which now has real main durations
        duration_by_path = trans_result["duration_per_frame"]
        # Also keep filename-keyed version for backward compatibility
        for frame_path_str, dur in trans_result["duration_per_frame"].items():
            key = Path(frame_path_str).name
            if key not in duration_per_frame:
                duration_per_frame[key] = dur
    else:
        # No transitions - build simple sequence without transitions
        simple_sequence = [{"path": str(p), "type": "main", "index": i} for i, p in enumerate(main_frame_paths)]
        transition_info["transition_sequence"] = simple_sequence
        # Build duration_by_path from duration_per_frame (filename-keyed)
        duration_by_path = {}
        for f in frame_outputs:
            fp = Path(f["path"])
            duration_by_path[str(fp)] = duration_per_frame.get(fp.name, 0.0)
            duration_by_path[fp.name] = duration_per_frame.get(fp.name, 0.0)

    # Deduplicate highlights
    unique_highlights = list(set(all_highlights))

    # V0.2.5.1: Conditionally calculate duration based on included sections
    overview_dur = overview_duration if include_overview else 0.0
    summary_dur = summary_duration if include_summary else 0.0
    total_duration = cover_duration + overview_dur + num_keypoints * keypoint_duration + summary_dur

    # V0.2.5.1: Find overview and summary frame paths
    overview_frame_path = None
    summary_frame_path = None
    for f in frame_outputs:
        if f["type"] == "overview":
            overview_frame_path = f["path"]
        elif f["type"] == "summary":
            summary_frame_path = f["path"]

    return {
        "frames": frame_outputs,
        "cover": frame_outputs[0]["path"] if frame_outputs else None,
        "duration_per_frame": duration_per_frame,
        "total_frames": len(frame_outputs),
        "total_duration_sec": total_duration,
        "warnings": all_warnings,
        # V0.2.4 new fields
        "visualPreset": VISUAL_PRESET,
        "templateVersion": TEMPLATE_VERSION,
        "transitionEnabled": transition_info["transitionEnabled"],
        "transitionType": transition_info["transitionType"],
        "transitionFrames": transition_info["transitionFrames"],
        "highlightTerms": unique_highlights,
        "overview_frame": overview_frame_path,
        "summary_frame": summary_frame_path,
        # V0.2.4.1 new fields
        "frameSequence": transition_info["transition_sequence"],
        "durationByPath": duration_by_path,
        "frameSequenceCount": len(transition_info["transition_sequence"]),
        # V0.2.5 new fields
        "highlightMode": highlight_mode,
        # V0.2.5.1 new fields
        "includeOverview": include_overview,
        "includeSummary": include_summary,
    }


# ─────────────────────────────────────────
# Legacy render functions for backward compatibility
# ─────────────────────────────────────────

def render_cover_frame(
    title: str,
    subtitle: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """Legacy cover frame renderer - delegates to new template."""
    result = render_cover_template(
        title=title,
        subtitle=subtitle,
        tags=["前沿资讯", "研究动态", "技术洞察"],
        date_str=datetime.now().strftime("%Y年%m月%d日"),
        frames_dir=frames_dir,
        resolution=resolution,
    )
    return result


def render_keypoint_frame(
    index: int,
    total: int,
    title: str,
    body: str,
    source: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """Legacy keypoint frame renderer - delegates to new template."""
    return render_keypoint_template(
        index=index,
        total=total,
        category="默认",
        title=title,
        body=body,
        source=source,
        frames_dir=frames_dir,
        resolution=resolution,
    )


def render_summary_frame(
    summary_text: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """Legacy summary frame renderer - delegates to new template."""
    return render_summary_template(
        conclusions=[summary_text] if summary_text else ["本期结束"],
        cta="Video Capability Lab",
        frames_dir=frames_dir,
        resolution=resolution,
    )
