"""
Subtitle and Voiceover Planner - 字幕与旁白计划
"""

from typing import Any


def generate_subtitle_plan(
    script: dict[str, Any],
    include_voiceover: bool = False,
) -> dict[str, Any]:
    """
    生成字幕计划。
    如果 include_voiceover 为 True，也生成旁白计划。
    """
    segments = script.get("segments", [])
    subtitles = []

    for seg in segments:
        # 计算每段字幕
        # 每行不超过20字，每段约3-4行
        text = seg.get("title", "")
        lines = [text[i:i+20] for i in range(0, len(text), 20)]

        subtitles.append({
            "segmentIndex": seg["index"],
            "lines": lines,
            "displayDuration": seg["durationSec"],
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
    生成旁白计划。
    """
    segments = script.get("segments", [])
    voiceovers = []

    for seg in segments:
        voiceovers.append({
            "segmentIndex": seg["index"],
            "text": seg.get("title", ""),
            "duration": seg["durationSec"],
            "voice": voice,
            "provider": "TTS-待接入",
        })

    return {
        "voiceovers": voiceovers,
        "totalSegments": len(voiceovers),
        "estimatedTotalDuration": sum(v["duration"] for v in voiceovers),
    }
