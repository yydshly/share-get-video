"""
Local Frame Renderer - 使用 Pillow 生成信息卡片 PNG 帧
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont

from app.video_lab.renderers.text_layout import (
    find_chinese_font,
    wrap_text,
    truncate_text,
    split_title_and_body,
    get_text_size,
)


# 颜色配置
COLORS = {
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


def render_gradient_background(width: int, height: int) -> Image.Image:
    """创建深色渐变背景"""
    img = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(COLORS["gradient_top"][0] * (1 - ratio) + COLORS["gradient_bottom"][0] * ratio)
        g = int(COLORS["gradient_top"][1] * (1 - ratio) + COLORS["gradient_bottom"][1] * ratio)
        b = int(COLORS["gradient_top"][2] * (1 - ratio) + COLORS["gradient_bottom"][2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


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


def render_cover_frame(
    title: str,
    subtitle: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """渲染封面帧。"""
    width, height = resolution
    img = render_gradient_background(width, height)
    draw = ImageDraw.Draw(img)

    font_title, warnings = find_chinese_font(72)
    font_subtitle, warnings_sub = find_chinese_font(32)
    warnings.extend(warnings_sub)

    # 顶部装饰线
    draw.rectangle([(width // 4, height // 6), (width * 3 // 4, height // 6 + 4)], fill=COLORS["accent"])

    # 主标题
    draw_centered_text(draw, title, height // 2 - 50, width, font_title, COLORS["primary"])

    # 副标题
    if subtitle:
        draw_centered_text(draw, subtitle, height // 2 + 60, width, font_subtitle, COLORS["secondary"])

    # 底部标签
    tag_text = "AI 前沿资讯 · 视频解读"
    draw_centered_text(draw, tag_text, height - 200, width, font_subtitle, COLORS["accent"])

    # 底部装饰线
    draw.rectangle([(width // 4, height - 150), (width * 3 // 4, height - 146)], fill=COLORS["accent"])

    output_path = frames_dir / "cover.png"
    img.save(output_path, "PNG")

    return {
        "path": output_path,
        "warnings": warnings,
    }


def render_keypoint_frame(
    index: int,
    total: int,
    title: str,
    body: str,
    source: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """渲染关键信息点帧。"""
    width, height = resolution
    img = render_gradient_background(width, height)
    draw = ImageDraw.Draw(img)

    font_index, warnings = find_chinese_font(28)
    font_title, warnings_title = find_chinese_font(52)
    font_body, warnings_body = find_chinese_font(32)
    font_source, warnings_source = find_chinese_font(22)
    warnings.extend(warnings_title)
    warnings.extend(warnings_body)
    warnings.extend(warnings_source)

    # 左侧序号
    index_text = f"{index}/{total}"
    draw.text((60, 60), index_text, font=font_index, fill=COLORS["accent"])

    # 顶部装饰
    draw.rectangle([(50, 120), (width - 50, 124)], fill=COLORS["tag_bg"])

    # 主标题区域
    title_max_width = int(width * 0.85)
    title_lines = wrap_text(title, font_title, title_max_width, draw)
    title_line_h = get_text_size("测试", font_title, draw)[1] + 10
    title_start_y = 180
    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, title_start_y + i * title_line_h), line, font=font_title, fill=COLORS["primary"])

    # 分隔线
    draw.rectangle([(width // 4, 650), (width * 3 // 4, 654)], fill=COLORS["accent_glow"])

    # 正文区域
    if body:
        body_max_width = int(width * 0.85)
        body_lines = wrap_text(body, font_body, body_max_width, draw)
        body_line_h = get_text_size("测试", font_body, draw)[1] + 8
        body_start_y = 700
        for i, line in enumerate(body_lines[:6]):
            bbox = draw.textbbox((0, 0), line, font=font_body)
            bw = bbox[2] - bbox[0]
            draw.text(((width - bw) // 2, body_start_y + i * body_line_h), line, font=font_body, fill=COLORS["secondary"])

    # 来源
    if source:
        source_max_width = int(width * 0.8)
        source_short = truncate_text(source, 60)
        source_lines = wrap_text(source_short, font_source, source_max_width, draw)
        source_line_h = get_text_size("测试", font_source, draw)[1] + 5
        source_start_y = height - 300
        for i, line in enumerate(source_lines[:2]):
            bbox = draw.textbbox((0, 0), line, font=font_source)
            sw = bbox[2] - bbox[0]
            draw.text(((width - sw) // 2, source_start_y + i * source_line_h), line, font=font_source, fill=COLORS["tag_bg"])

    # 底部标签
    tag_text = "AI 前沿资讯"
    bbox = draw.textbbox((0, 0), tag_text, font=font_source)
    tw = bbox[2] - bbox[0]
    draw.rectangle([(width // 2 - tw // 2 - 20, height - 100), (width // 2 + tw // 2 + 20, height - 60)], fill=COLORS["tag_bg"])
    draw.text(((width - tw) // 2, height - 95), tag_text, font=font_source, fill=COLORS["accent"])

    frame_name = f"frame_{index:03d}.png"
    output_path = frames_dir / frame_name
    img.save(output_path, "PNG")

    return {
        "path": output_path,
        "frame_name": frame_name,
        "warnings": warnings,
    }


def render_summary_frame(
    summary_text: str,
    frames_dir: Path,
    resolution: Tuple[int, int] = (1080, 1920),
) -> Dict[str, Any]:
    """渲染总结帧。"""
    width, height = resolution
    img = render_gradient_background(width, height)
    draw = ImageDraw.Draw(img)

    font_title, warnings = find_chinese_font(56)
    font_body, warnings_body = find_chinese_font(30)
    warnings.extend(warnings_body)

    # 顶部装饰
    draw.rectangle([(width // 4, 150), (width * 3 // 4, 154)], fill=COLORS["highlight"])

    # 标题
    draw_centered_text(draw, "本期小结", height // 3, width, font_title, COLORS["highlight"])

    # 正文
    if summary_text:
        max_w = int(width * 0.85)
        lines = wrap_text(summary_text, font_body, max_w, draw)
        line_h = get_text_size("测试", font_body, draw)[1] + 10
        start_y = height // 2 + 50
        for i, line in enumerate(lines[:8]):
            bbox = draw.textbbox((0, 0), line, font=font_body)
            bw = bbox[2] - bbox[0]
            draw.text(((width - bw) // 2, start_y + i * line_h), line, font=font_body, fill=COLORS["secondary"])

    # 底部
    tag_text = "AI 前沿资讯 · 每日更新"
    bbox = draw.textbbox((0, 0), tag_text, font=font_body)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, height - 150), tag_text, font=font_body, fill=COLORS["accent"])

    output_path = frames_dir / "summary.png"
    img.save(output_path, "PNG")

    return {
        "path": output_path,
        "warnings": warnings,
    }


def generate_frames(
    experiment_id: str,
    structured: dict,
    key_points: dict,
    target_duration_sec: int,
    resolution: Tuple[int, int] = (1080, 1920),
) -> dict:
    """生成所有帧。"""
    from app.video_lab.renderers.file_store import get_frames_dir as _get_frames_dir

    frames_dir = _get_frames_dir(experiment_id)
    width, height = resolution

    all_warnings = []
    frame_outputs = []
    duration_per_frame = {}

    kps = key_points.get("key_points", [])
    num_keypoints = len(kps)
    if num_keypoints == 0:
        num_keypoints = 1

    cover_duration = 4.0
    keypoint_duration = max(3.0, (target_duration_sec - cover_duration - 4.0) / max(num_keypoints, 1))
    summary_duration = 4.0

    # 封面
    lead_text = structured.get("lead", "")
    title_part, _ = split_title_and_body(lead_text, max_title_chars=25)
    cover_result = render_cover_frame(
        title=title_part or "AI 前沿资讯",
        subtitle="今日要点速览",
        frames_dir=frames_dir,
        resolution=resolution,
    )
    frame_outputs.append({"type": "cover", "path": cover_result["path"]})
    duration_per_frame["cover.png"] = cover_duration
    all_warnings.extend(cover_result["warnings"])

    # 关键信息点
    for i, kp in enumerate(kps, 1):
        title = truncate_text(kp.get("title", ""), 50)
        body = kp.get("source", "")
        frame_result = render_keypoint_frame(
            index=i,
            total=num_keypoints,
            title=title,
            body=body,
            source="依据: AI前沿研究",
            frames_dir=frames_dir,
            resolution=resolution,
        )
        frame_name = frame_result["frame_name"]
        frame_outputs.append({"type": "keypoint", "frame_num": i, "path": frame_result["path"], "frame_name": frame_name})
        duration_per_frame[frame_name] = keypoint_duration
        all_warnings.extend(frame_result["warnings"])

    # 总结帧
    summary_result = render_summary_frame(
        summary_text=f"本期共{num_keypoints}条前沿资讯",
        frames_dir=frames_dir,
        resolution=resolution,
    )
    frame_outputs.append({"type": "summary", "path": summary_result["path"]})
    duration_per_frame["summary.png"] = summary_duration
    all_warnings.extend(summary_result["warnings"])

    total_duration = cover_duration + num_keypoints * keypoint_duration + summary_duration

    return {
        "frames": frame_outputs,
        "cover": frame_outputs[0]["path"] if frame_outputs else None,
        "duration_per_frame": duration_per_frame,
        "total_frames": len(frame_outputs),
        "total_duration_sec": total_duration,
        "warnings": all_warnings,
    }
