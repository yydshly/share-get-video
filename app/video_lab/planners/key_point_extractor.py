"""
Key Point Extractor - 提取视频关键信息点
"""

from typing import Any


def extract_key_points(structured: dict[str, Any], target_duration_sec: int) -> dict[str, Any]:
    """
    从结构化内容中提取关键信息点。
    根据目标时长决定展示多少条。
    """
    items = structured.get("items", [])
    # 简单策略：每 10 秒一条，但至少 3 条
    num_points = max(3, min(len(items), target_duration_sec // 10))

    key_points = []
    for i, item in enumerate(items[:num_points]):
        key_points.append({
            "index": i + 1,
            "title": item.get("title", "")[:50],
            "source": item.get("source", ""),
            "displayTime": f"{(i * target_duration_sec // num_points)}-{(i + 1) * target_duration_sec // num_points}s",
        })

    return {
        "keyPoints": key_points,
        "totalPoints": len(key_points),
        "selectedFrom": len(items),
    }
