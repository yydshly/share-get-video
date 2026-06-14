"""
Key Point Extractor - 提取视频关键信息点
"""

import re
from typing import Any


def extract_key_points(
    structured: dict[str, Any],
    target_duration_sec: int,
    max_points: int = 10,
) -> dict[str, Any]:
    """
    从结构化内容中提取关键信息点。

    默认尽量保留所有源条目（至多 max_points），由调用方（keyPointCount）做最终裁剪，
    避免"目标时长//15"把信息砍掉一半造成信息不全。

    每条 keyPoint 的 title 会被裁剪到 60 字符以内，
    并从 source 中提炼出一行摘要作为 body。
    """
    items = structured.get("items", [])

    if not items:
        return {"keyPoints": [], "totalPoints": 0, "selectedFrom": 0}

    # 保留所有源条目（封顶 max_points）；不再用 target_duration 砍条数
    num_points = min(len(items), max(1, max_points))

    key_points = []
    for i, item in enumerate(items[:num_points]):
        raw_title = item.get("title", "").strip()
        raw_source = item.get("source", "").strip()

        # 清理 title：仅归一化空白，不截断（卡片渲染会自适应字号容纳全文）
        title = re.sub(r"\s+", " ", raw_title).strip()

        # 从 source 中提炼 body：去除 "依据：" 前缀，取第一句
        body = _extract_body(raw_source)

        key_points.append({
            "index": i + 1,
            "title": title,
            "body": body,
            "source": raw_source,
            "displayTime": f"{(i * target_duration_sec // num_points) if num_points else 0}-{(i + 1) * target_duration_sec // num_points}s",
        })

    return {
        "keyPoints": key_points,
        "key_points": key_points,  # 兼容两种 key 名
        "totalPoints": len(key_points),
        "selectedFrom": len(items),
    }


def _extract_body(source: str) -> str:
    """从 source 中提取一行简短说明。"""
    if not source:
        return ""
    # 去掉 "依据：" 前缀
    s = re.sub(r"^依据[：:]\s*", "", source)
    # 取第一句（到句号或换行）
    s = s.split("。")[0].split("\n")[0].strip()
    # 截断到 50 字符
    return s[:50]
