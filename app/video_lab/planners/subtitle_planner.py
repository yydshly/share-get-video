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
    subtitles = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start_sec = float(seg.get("startSec", 0))
        duration = float(seg.get("durationSec", 5))
        end_sec = start_sec + duration

        # Split long text into sub-lines (max ~20 chars each)
        sub_lines = _split_subtitle_text(text)

        subtitles.append({
            "startSec": start_sec,
            "endSec": end_sec,
            "text": text,
            "subLines": sub_lines,
        })

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


def _split_subtitle_text(text: str, max_chars: int = 20) -> list[str]:
    """Split Chinese text into subtitle lines of reasonable length."""
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
    return lines if lines else [text]


def _build_srt_content(subtitles: list[dict]) -> str:
    """Build SRT file content from subtitle list."""
    lines: list[str] = []
    for i, sub in enumerate(subtitles, start=1):
        start = _format_srt_time(sub["startSec"])
        end = _format_srt_time(sub["endSec"])
        text = sub.get("text", "")
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


