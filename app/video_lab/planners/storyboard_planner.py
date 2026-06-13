"""
Storyboard Planner - 生成分镜
"""

from typing import Any


def generate_storyboard(
    script: dict[str, Any],
    method_category: str,
) -> dict[str, Any]:
    """
    根据脚本生成分镜。
    每个分镜包含：序号、画面类型、构图、动态描述。
    """
    segments = script.get("segments", [])
    frames = []

    for seg in segments:
        # 封面帧
        frames.append({
            "frameId": f"frame_{seg['index']}_cover",
            "segmentIndex": seg["index"],
            "type": "cover",
            "composition": "标题居中大字",
            "content": seg["title"],
            "durationFrames": 30,  # 0.5秒
        })

        # 内容帧
        frames.append({
            "frameId": f"frame_{seg['index']}_content",
            "segmentIndex": seg["index"],
            "type": "content_card",
            "composition": "卡片式布局",
            "content": seg["title"],
            "durationFrames": seg["durationSec"] * 30,
        })

        # 来源帧（如果有）
        if seg.get("source"):
            frames.append({
                "frameId": f"frame_{seg['index']}_source",
                "segmentIndex": seg["index"],
                "type": "source",
                "composition": "底部小字",
                "content": seg["source"][:50],
                "durationFrames": 30,
            })

    return {
        "frames": frames,
        "totalFrames": len(frames),
        "estimatedDurationSec": sum(f["durationFrames"] for f in frames) // 30,
    }
