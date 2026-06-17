"""
Subtitle Planner - 字幕计划生成器
V0.3.3: Generates SRT subtitle files for TTS audio

Extends the existing subtitle/voiceover plan functions with SRT file generation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import path_to_url


def generate_subtitle_plan(
    script: dict[str, Any],
    include_voiceover: bool = False,
) -> dict[str, Any]:
    """
    Generate a subtitle plan from a script (legacy, used by local_frame_compose).
    """
    segments = script.get("segments", [])
    subtitles = []

    for seg in segments:
        text = seg.get("title", "")
        lines = [text[i:i+20] for i in range(0, len(text), 20)]

        subtitles.append({
            "segmentIndex": seg["index"],
            "lines": lines,
            "displayDuration": seg.get("durationSec", 4),
            "fontSize": 48,
            "position": "bottom_center",
            "hasVoiceover": include_voiceover,
        })

    return {
        "subtitles": subtitles,
        "totalSegments": len(subtitles),
        "includeVoiceover": include_voiceover,
        "format": "SRT",
    }


def generate_voiceover_plan(
    script: dict[str, Any],
    voice: str = "zh-CN-female",
) -> dict[str, Any]:
    """
    Generate a voiceover plan from a script (legacy, used by local_frame_compose).
    """
    segments = script.get("segments", [])
    voiceovers = []

    for seg in segments:
        voiceovers.append({
            "segmentIndex": seg["index"],
            "text": seg.get("title", ""),
            "duration": seg.get("durationSec", 4),
            "voice": voice,
            "provider": "TTS-待接入",
        })

    return {
        "voiceovers": voiceovers,
        "totalSegments": len(voiceovers),
        "estimatedTotalDuration": sum(v["duration"] for v in voiceovers),
    }


def generate_srt_from_segments(
    segments: list[dict[str, Any]],
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """
    Generate an SRT subtitle file from voiceover segments.

    Args:
        segments: list of voiceover segments with text, startSec, durationSec
        output_path: optional path to write the SRT file

    Returns:
        {
            "subtitles": [...],
            "format": "srt",
            "srtPath": "...",
            "srtUrl": "...",
            "subtitleDiagnostics": {...}
        }
    """
    # 每段旁白拆成多条短字幕，时间按字数比例分配，与 TTS 同步、不截断
    # V1.2.3 P1: use DEFAULT_ASS_STYLE limits for consistency
    eff_max_chars = DEFAULT_ASS_STYLE["max_chars"]
    eff_max_lines = DEFAULT_ASS_STYLE["max_lines"]
    subtitles = []
    for seg in segments:
        subtitles.extend(_segment_to_entries(seg, max_chars=eff_max_chars, max_lines=eff_max_lines))

    # Build SRT content
    srt_content = _build_srt_content(subtitles)

    srt_path = ""
    srt_url = ""
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(srt_content, encoding="utf-8")
        srt_path = str(output_path)
        srt_url = path_to_url(output_path)

    diagnostics = analyze_subtitle_entries(
        subtitles,
        max_chars=eff_max_chars,
        max_lines=eff_max_lines,
        segment_count=len(segments),
    )

    return {
        "subtitles": subtitles,
        "format": "srt",
        "srtPath": srt_path,
        "srtUrl": srt_url,
        "subtitleDiagnostics": diagnostics,
    }


def _split_subtitle_text(text: str, max_chars: int = 22) -> list[str]:
    """Split Chinese text into subtitle lines of reasonable length (max 2 lines for safe area)."""
    if not text:
        return []
    lines = []
    current = ""
    for char in text:
        current += char
        if len(current) >= max_chars:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    # Cap at 2 lines to avoid blocking too much of the video
    return lines[:2] if lines else [text[:max_chars]]


def _wrap_chars(text: str, max_chars: int) -> list[str]:
    """Wrap text into lines of <= max_chars (no truncation)."""
    if not text:
        return [""]
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def _chunk_text(text: str, max_chars: int) -> list[str]:
    """把整句旁白按标点切成多条短字幕块（每块最多约 2 行），不丢内容。"""
    import re
    limit = max_chars * 2
    # 按句末/句中标点切分，保留标点
    parts = re.split(r"(?<=[。！？!?，、；,;])", text)
    parts = [p for p in (s.strip() for s in parts) if p]
    if not parts:
        parts = [text]

    chunks: list[str] = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) <= limit:
            cur += p
        else:
            if cur:
                chunks.append(cur)
                cur = ""
            if len(p) <= limit:
                cur = p
            else:
                # 超长子句：尽量均分，避免最后留下很短的碎片
                import math
                n = math.ceil(len(p) / limit)
                size = math.ceil(len(p) / n)
                for i in range(0, len(p), size):
                    chunks.append(p[i:i + size])
                cur = ""
    if cur:
        chunks.append(cur)

    # 合并过短的碎片到相邻块（避免字幕一闪而过）
    # 注意：不能合并出超过 limit（约 2 行）的 chunk，否则 _segment_to_entries
    # 会拆分出超过 max_lines 的 entry 导致丢字
    merged: list[str] = []
    for c in chunks:
        if merged and len(c) < max_chars * 0.6 and len(merged[-1]) + len(c) <= limit:
            merged[-1] += c
        else:
            merged.append(c)
    return merged or [text]


def _segment_to_entries(seg: dict, max_chars: int, max_lines: int) -> list[dict]:
    """把一个旁白段拆成多条时间分配好的字幕条（按字数比例分时间，不截断）。

    每个 chunk 如果 wrap 后超过 max_lines 行，会被拆成多条 entry，
    每条 entry 有 max_lines 行，时间按字数比例分配。
    """
    text = (seg.get("text", "") or "").strip()
    if not text:
        return []
    start = float(seg.get("startSec", 0))
    dur = float(seg.get("durationSec", 5))
    chunks = _chunk_text(text, max_chars)
    total_chars = sum(len(c) for c in chunks) or 1

    entries = []
    t = start
    for idx, c in enumerate(chunks):
        wrapped = _wrap_chars(c, max_chars)
        chunk_total_chars = len(c)

        # 如果 wrap 后超过 max_lines 行，拆成多条 entry，每条 max_lines 行
        pages: list[list[str]] = []
        for i in range(0, len(wrapped), max_lines):
            pages.append(wrapped[i:i + max_lines])

        # 计算每页应分配的时间（按字数比例）
        chars_per_page = chunk_total_chars / len(pages) if pages else 1

        for page_idx, page_lines in enumerate(pages):
            if page_idx == len(pages) - 1 and idx == len(chunks) - 1:
                # 最后一个 chunk 的最后一页：用段末，避免累计误差
                d = max(0.4, (start + dur) - t)
            else:
                d = max(0.4, dur * (chars_per_page / total_chars))
            entries.append({
                "startSec": round(t, 3),
                "endSec": round(t + d, 3),
                "text": c,
                "subLines": page_lines,
            })
            t += d

    return entries


def _build_srt_content(subtitles: list[dict]) -> str:
    """Build SRT file content from subtitle list."""
    lines: list[str] = []
    for i, sub in enumerate(subtitles, start=1):
        start = _format_srt_time(sub["startSec"])
        end = _format_srt_time(sub["endSec"])
        text = "\n".join(sub.get("subLines") or [sub.get("text", "")])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT time: HH:MM:SS,mmm"""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    secs = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


# ─────────────────────────────────────────────────────────────
# V0.3.8.1: ASS subtitle generation for proper font scaling
# ─────────────────────────────────────────────────────────────

# Default safe-area subtitle style for 1080x1920 portrait video.
# Use ASS file with explicit PlayResX/Y so FFmpeg/libass scales correctly.
# V0.3.6-a2: Enhanced for short-video readability - larger font, better vertical
# position (avoiding player controls), wider max_chars, stronger background.
DEFAULT_ASS_STYLE = {
    "font_size": 36,           # V0.3.6-a2: 32→36 (短视频字幕更醒目)
    "margin_v": 150,          # V0.3.6-a2: 240→150 (距底部120-180px，避免控制条遮挡)
    "margin_lr": 80,
    "outline": 2,
    "shadow": 3,              # V0.3.6-a2: 1→3 (更强阴影分离度)
    "alignment": 2,           # bottom center
    "max_chars": 22,           # V0.3.6-a2: 18→22 (字幕宽度控制72-82%)
    "max_lines": 2,
    "primary_colour": "&H00FFFFFF",   # white
    "outline_colour": "&H00000000",   # black
    "back_colour": "&HBb000000",      # V0.3.6-a2: 99→BB 更不透明底板
    "font_name": "Microsoft YaHei",
}


def generate_ass_from_segments(
    segments: list[dict[str, Any]],
    output_path: Path | str | None = None,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    style: dict[str, Any] | None = None,
    max_chars: int | None = None,
    max_lines: int | None = None,
) -> dict[str, Any]:
    """
    Generate an ASS (Advanced SubStation Alpha) subtitle file.

    ASS supports explicit PlayResX/Y so FFmpeg/libass scales font size
    relative to the target resolution. This avoids the issue where
    SRT + force_style uses libass defaults (often 384x288) and Fontsize
    is interpreted in those units.

    Args:
        segments: list of voiceover segments with text, startSec, durationSec
        output_path: optional path to write the ASS file
        play_res_x: target video width (default 1080)
        play_res_y: target video height (default 1920)
        style: optional style override dict
        max_chars: override DEFAULT_ASS_STYLE["max_chars"]
        max_lines: override DEFAULT_ASS_STYLE["max_lines"]

    Returns:
        {
            "subtitles": [...],
            "format": "ass",
            "assPath": "...",
            "assUrl": "...",
            "style": {...}
        }
    """
    eff_style = {**DEFAULT_ASS_STYLE, **(style or {})}
    eff_max_chars = max_chars if max_chars is not None else eff_style["max_chars"]
    eff_max_lines = max_lines if max_lines is not None else eff_style["max_lines"]

    # 每段旁白拆成多条短字幕，时间按字数比例分配，与 TTS 同步、不截断
    subtitles = []
    for seg in segments:
        subtitles.extend(_segment_to_entries(seg, max_chars=eff_max_chars, max_lines=eff_max_lines))

    ass_content = _build_ass_content(
        subtitles,
        play_res_x=play_res_x,
        play_res_y=play_res_y,
        style=eff_style,
    )

    ass_path = ""
    ass_url = ""
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(ass_content, encoding="utf-8")
        ass_path = str(output_path)
        ass_url = path_to_url(output_path)

    diagnostics = analyze_subtitle_entries(
        subtitles,
        max_chars=eff_max_chars,
        max_lines=eff_max_lines,
        segment_count=len(segments),
    )

    return {
        "subtitles": subtitles,
        "format": "ass",
        "assPath": ass_path,
        "assUrl": ass_url,
        "style": eff_style,
        "playResX": play_res_x,
        "playResY": play_res_y,
        "subtitleDiagnostics": diagnostics,
    }


def _build_ass_content(
    subtitles: list[dict],
    play_res_x: int,
    play_res_y: int,
    style: dict[str, Any],
) -> str:
    """Build ASS file content with explicit PlayResX/Y and style."""
    # ASS Style line fields (in order):
    # Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,
    # Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,
    # BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    style_line = (
        f"Style: Default,"
        f"{style['font_name']},"
        f"{style['font_size']},"
        f"{style['primary_colour']},"
        f"&H000000FF,"  # secondary (Karaoke) — default
        f"{style['outline_colour']},"
        f"{style['back_colour']},"
        f"0,0,0,0,"  # Bold/Italic/Underline/StrikeOut
        f"100,100,0,0,"  # ScaleX/Y, Spacing, Angle
        f"1,"  # BorderStyle: 1 = outline + shadow
        f"{style['outline']},"
        f"{style['shadow']},"
        f"{style['alignment']},"
        f"{style['margin_lr']},{style['margin_lr']},{style['margin_v']},"
        f"1"  # Encoding: 1 = default
    )

    lines = [
        "[Script Info]",
        f"; Generated by video-lab subtitle_planner.py (V0.3.8.1)",
        "ScriptType: v4.00+",
        "Collisions: Normal",
        f"PlayResX: {play_res_x}",
        f"PlayResY: {play_res_y}",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        style_line,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for sub in subtitles:
        start = _format_ass_time(sub["startSec"])
        end = _format_ass_time(sub["endSec"])
        text_lines = sub.get("subLines", [sub["text"]])
        text = "\\N".join(text_lines)  # ASS line break
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return "\n".join(lines) + "\n"


def _format_ass_time(seconds: float) -> str:
    """Format seconds as ASS time: H:MM:SS.cc (centiseconds)."""
    total_cs = int(round(seconds * 100))
    hours = total_cs // 360000
    minutes = (total_cs % 360000) // 6000
    secs = (total_cs % 6000) // 100
    cs = total_cs % 100
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{cs:02d}"


# ─────────────────────────────────────────────────────────────
# V1.2.3 P1: ASS subtitle style resolution + diagnostics
# ─────────────────────────────────────────────────────────────

# Safe-range limits for user-supplied style overrides
_STYLE_LIMITS = {
    "font_size": (24, 56),
    "margin_v": (80, 320),
    "margin_lr": (40, 180),
    "max_chars": (14, 30),
    "max_lines": (1, 3),
}

# Known overrideable fields (anything else in params.subtitleStyle is ignored)
_KNOWN_STYLE_FIELDS = {
    "font_size", "margin_v", "margin_lr", "max_chars", "max_lines",
    "outline", "shadow", "alignment",
    "primary_colour", "outline_colour", "back_colour", "font_name",
}


def resolve_ass_subtitle_style(
    *,
    aspect_ratio: str = "9:16",
    visual_route: str = "",
    params: dict | None = None,
) -> dict:
    """
    Resolve ASS subtitle style based on visual route and optional params override.

    Returns a style dict derived from DEFAULT_ASS_STYLE, updated with route-specific
    defaults, then overlaid with any valid fields from params["subtitleStyle"].

    Args:
        aspect_ratio: target video aspect ratio (e.g. "9:16", "16:9")
        visual_route: identifies the rendering pipeline (e.g. "ai_asset_then_compose",
                      "template_programmatic_render", "local_frame_compose")
        params: optional dict that may contain a "subtitleStyle" key with override values

    Returns:
        dict with resolved style fields including max_chars and max_lines
    """
    # Start from defaults
    style = dict(DEFAULT_ASS_STYLE)

    # Route-specific safe-area defaults
    if visual_route == "ai_asset_then_compose":
        style.update({
            "font_size": 34,
            "margin_v": 190,
            "margin_lr": 90,
            "back_colour": "&HC0000000",
            "max_chars": 20,
            "max_lines": 2,
        })
    elif visual_route == "template_programmatic_render":
        # Remotion — restrained bottom subtitle, avoids obscuring card content
        style.update({
            "font_size": 32,
            "margin_v": 160,
            "margin_lr": 90,
            "max_chars": 20,
            "max_lines": 2,
        })
    elif visual_route == "local_frame_compose":
        # Pillow static card — stable bottom subtitle
        style.update({
            "font_size": 36,
            "margin_v": 150,
            "max_chars": 22,
            "max_lines": 2,
        })
    # else: use DEFAULT_ASS_STYLE unchanged

    # Apply user/params overrides from params["subtitleStyle"]
    if params and isinstance(params, dict):
        override = params.get("subtitleStyle")
        if override and isinstance(override, dict):
            for key, value in override.items():
                if key not in _KNOWN_STYLE_FIELDS:
                    continue  # ignore unknown keys silently
                if key in _STYLE_LIMITS:
                    lo, hi = _STYLE_LIMITS[key]
                    if isinstance(value, (int, float)):
                        value = int(value)
                        value = max(lo, min(hi, value))  # clamp
                # Only add if not None
                if value is not None:
                    style[key] = value

    return style


def analyze_subtitle_entries(
    subtitles: list[dict],
    *,
    max_chars: int,
    max_lines: int,
    segment_count: int = 0,
) -> dict:
    """
    Diagnose subtitle entries for common quality issues.

    Args:
        subtitles: list of subtitle entries from generate_*_from_segments
        max_chars: per-line character limit used when generating
        max_lines: per-entry line limit used when generating
        segment_count: original number of voiceover segments (for context)

    Returns:
        dict with diagnostic flags and metrics:
        {
            "subtitleCount": int,
            "maxLineLength": int,
            "maxLinesPerEntry": int,
            "avgDurationSec": float,
            "minDurationSec": float,
            "maxDurationSec": float,
            "hasTooFastEntries": bool,
            "tooFastCount": int,
            "hasOverLineLimit": bool,
            "overLineLimitCount": int,
            "hasOverCharLimit": bool,
            "overCharLimitCount": int,
        }
    """
    if not subtitles:
        return {
            "subtitleCount": 0,
            "maxLineLength": 0,
            "maxLinesPerEntry": 0,
            "avgDurationSec": 0.0,
            "minDurationSec": 0.0,
            "maxDurationSec": 0.0,
            "hasTooFastEntries": False,
            "tooFastCount": 0,
            "hasOverLineLimit": False,
            "overLineLimitCount": 0,
            "hasOverCharLimit": False,
            "overCharLimitCount": 0,
            "segmentCount": segment_count,
        }

    durations = []
    max_line_len = 0
    max_lines_used = 0
    too_fast = 0
    over_line = 0
    over_char = 0

    for entry in subtitles:
        lines = entry.get("subLines", [])
        text = entry.get("text", "")

        # Duration
        start = float(entry.get("startSec", 0))
        end = float(entry.get("endSec", 0))
        dur = end - start
        durations.append(dur)

        # Per-line char length
        for ln in lines:
            max_line_len = max(max_line_len, len(ln))

        # Lines per entry
        max_lines_used = max(max_lines_used, len(lines))

        # Too fast: < 0.6s
        if dur < 0.6:
            too_fast += 1

        # Over line limit
        if len(lines) > max_lines:
            over_line += 1

        # Over char limit (any line longer than max_chars)
        for ln in lines:
            if len(ln) > max_chars:
                over_char += 1
                break  # count per entry, not per line

    return {
        "subtitleCount": len(subtitles),
        "maxLineLength": max_line_len,
        "maxLinesPerEntry": max_lines_used,
        "avgDurationSec": round(sum(durations) / len(durations), 3) if durations else 0.0,
        "minDurationSec": round(min(durations), 3) if durations else 0.0,
        "maxDurationSec": round(max(durations), 3) if durations else 0.0,
        "hasTooFastEntries": too_fast > 0,
        "tooFastCount": too_fast,
        "hasOverLineLimit": over_line > 0,
        "overLineLimitCount": over_line,
        "hasOverCharLimit": over_char > 0,
        "overCharLimitCount": over_char,
        "segmentCount": segment_count,
    }