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
            "srtUrl": "..."
        }
    """
    # 每段旁白拆成多条短字幕，时间按字数比例分配，与 TTS 同步、不截断
    subtitles = []
    for seg in segments:
        subtitles.extend(_segment_to_entries(seg, max_chars=20, max_lines=2))

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

    return {
        "subtitles": subtitles,
        "format": "srt",
        "srtPath": srt_path,
        "srtUrl": srt_url,
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
    merged: list[str] = []
    for c in chunks:
        if merged and len(c) < max_chars * 0.6 and len(merged[-1]) + len(c) <= limit + max_chars:
            merged[-1] += c
        else:
            merged.append(c)
    return merged or [text]


def _segment_to_entries(seg: dict, max_chars: int, max_lines: int) -> list[dict]:
    """把一个旁白段拆成多条时间分配好的字幕条（按字数比例分时间，不截断）。"""
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
        # 最后一条用段末，避免累计误差
        if idx == len(chunks) - 1:
            d = max(0.4, (start + dur) - t)
        else:
            d = max(0.4, dur * (len(c) / total_chars))
        entries.append({
            "startSec": round(t, 3),
            "endSec": round(t + d, 3),
            "text": c,
            "subLines": _wrap_chars(c, max_chars)[:max_lines],
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

    return {
        "subtitles": subtitles,
        "format": "ass",
        "assPath": ass_path,
        "assUrl": ass_url,
        "style": eff_style,
        "playResX": play_res_x,
        "playResY": play_res_y,
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