"""
Content Structurer - 将原始输入转为结构化内容

将 AI 资讯报告解析为：lead（总起）+ items（每条新闻的 title + source）。

兼容两种书写格式（统一按"行"处理，对是否有空行不敏感）：
- 标准格式：标题 + 空行 + "依据：..."
- 紧凑格式：标题 与 "依据：..." 仅以单换行相邻，条目之间也无空行

解析规则（前瞻配对，避免重复 / 丢条）：
1. 第一行为 lead（总起段落）。
2. 其余行中，以"依据"开头的行归为当前条目的 source（可多行累加）；
   其它行视为一条新 title，遇到新 title 时先收尾上一条。
"""

from typing import Any


def structure_content(raw_content: str, input_type: str) -> dict[str, Any]:
    """将原始输入文本结构化为 lead + items。"""
    text = (raw_content or "").strip()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    if not lines:
        return {"lead": "", "items": [], "totalItems": 0, "inputType": input_type}

    lead = lines[0]
    items = _pair_titles_and_sources(lines[1:])

    return {
        "lead": lead,
        "items": items,
        "totalItems": len(items),
        "inputType": input_type,
    }


def _is_source_line(line: str) -> bool:
    """判断某行是否为"依据"行（source）。"""
    return line.startswith("依据：") or line.startswith("依据:")


def _pair_titles_and_sources(lines: list[str]) -> list[dict[str, str]]:
    """将行序列配对为 [{title, source}]，每个 title 收尾一次（不重复、不丢条）。"""
    items: list[dict[str, str]] = []
    current_title: str | None = None
    current_sources: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_sources
        if current_title is not None:
            items.append({
                "title": current_title,
                "source": " ".join(current_sources).strip(),
            })
        current_title = None
        current_sources = []

    for ln in lines:
        if _is_source_line(ln):
            current_sources.append(ln)
        else:
            # 新标题：先收尾上一条
            flush()
            current_title = ln

    flush()
    return items
