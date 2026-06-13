"""
Script Planner - 生成视频脚本
"""

from typing import Any


def generate_script(
    key_points: dict[str, Any],
    aspect_ratio: str,
    target_duration_sec: int,
) -> dict[str, Any]:
    """
    根据关键信息点生成视频脚本。
    返回每段的文字内容、时长、视觉描述。
    """
    kps = key_points.get("keyPoints", [])
    segments = []

    for kp in kps:
        title = kp["title"]
        # 估算每段时长（标题 + 内容，约 8-12 秒）
        duration = target_duration_sec // len(kps) if kps else 10

        segments.append({
            "index": kp["index"],
            "title": title,
            "script": f"{title}",
            "durationSec": duration,
            "visual": f"文字卡片展示：{title}",
            "narration": title,
        })

    return {
        "segments": segments,
        "totalSegments": len(segments),
        "estimatedDuration": sum(s["durationSec"] for s in segments),
        "aspectRatio": aspect_ratio,
    }
