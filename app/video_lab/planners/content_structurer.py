"""
Content Structurer - 将原始输入转为结构化内容
"""

from typing import Any


def structure_content(raw_content: str, input_type: str) -> dict[str, Any]:
    """
    将原始输入文本结构化。
    适用于 AI_INSIGHT_SUMMARY 类型输入。
    """
    # 简单按段落拆分
    paragraphs = [p.strip() for p in raw_content.split("\n\n") if p.strip()]

    # 如果第一条是总起段，单独标记
    lead = paragraphs[0] if paragraphs else ""
    body = paragraphs[1:] if len(paragraphs) > 1 else []

    # 解析 body 中的 "标题\n依据：依据 X" 格式
    items = []
    current_title = None
    current_source = None

    for para in body:
        if para.startswith("依据："):
            if current_title:
                items.append({"title": current_title, "source": para})
            current_source = para
        else:
            if current_title and current_source:
                items.append({"title": current_title, "source": current_source})
            current_title = para
            current_source = None

    if current_title:
        items.append({"title": current_title, "source": current_source or ""})

    return {
        "lead": lead,
        "items": items,
        "totalItems": len(items),
        "inputType": input_type,
    }
