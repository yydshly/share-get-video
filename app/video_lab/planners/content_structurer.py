"""
Content Structurer - 将原始输入转为结构化内容
"""

import re
from typing import Any


def structure_content(raw_content: str, input_type: str) -> dict[str, Any]:
    """
    将原始输入文本结构化。
    适用于 AI_INSIGHT_SUMMARY 类型输入。

    支持两种格式：
    - 标准格式：标题 + blank line + "依据：" 行
    - 紧凑格式：标题 + 单行 "依据："（无 blank line 分隔）
    """
    # 预处理：统一换行符
    text = raw_content.strip()

    # 先按双换行拆分（标准段落格式）
    double_newline_split = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    if len(double_newline_split) > 2:
        # 标准格式：lead + 多个 item 段落
        lead = double_newline_split[0]
        body_paragraphs = double_newline_split[1:]
        items = _parse_items_from_paragraphs(body_paragraphs)
    else:
        # 紧凑格式：单换行分隔或无分隔
        lead, items = _parse_compact_format(text)

    return {
        "lead": lead,
        "items": items,
        "totalItems": len(items),
        "inputType": input_type,
    }


def _parse_items_from_paragraphs(paragraphs: list[str]) -> list[dict[str, str]]:
    """从段落列表中提取 title+source 项目。"""
    items = []
    current_title = None
    current_source = None

    for para in paragraphs:
        if para.startswith("依据：") or para.startswith("依据:"):
            # 这是一个 source 行
            source = para
            if current_title:
                items.append({"title": current_title, "source": source})
            current_source = source
        else:
            # 这是一个 title 行
            if current_title and current_source:
                items.append({"title": current_title, "source": current_source})
            current_title = para
            current_source = None

    if current_title:
        items.append({"title": current_title, "source": current_source or ""})

    return items


def _parse_compact_format(text: str) -> tuple[str, list[dict[str, str]]]:
    """
    解析紧凑格式（单换行或无明确分隔）。
    格式示例：
      lead 文本
      标题1内容
      依据：依据 1
      标题2内容
      依据：依据 1
    """
    # 按单换行拆分
    lines = text.split("\n")
    lines = [ln.strip() for ln in lines if ln.strip()]

    if not lines:
        return "", []

    # 前几行可能是 lead（直到遇到 "依据：" 开头的行）
    lead_parts = []
    body_lines = []
    in_lead = True

    for ln in lines:
        if in_lead and (ln.startswith("依据：") or ln.startswith("依据:")):
            in_lead = False
            body_lines.append(ln)
        elif in_lead:
            lead_parts.append(ln)
        else:
            body_lines.append(ln)

    lead = " ".join(lead_parts)

    # 解析 body_lines 成 items
    items = []
    current_title = None
    current_source = None

    for ln in body_lines:
        if ln.startswith("依据：") or ln.startswith("依据:"):
            if current_title:
                items.append({"title": current_title, "source": ln})
            current_source = ln
        else:
            if current_title and current_source:
                items.append({"title": current_title, "source": current_source})
            current_title = ln
            current_source = None

    if current_title:
        items.append({"title": current_title, "source": current_source or ""})

    return lead, items
