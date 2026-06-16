"""
Information Structure Service V1.0

Provides structured parsing of informational content for video generation.
Used by the "Information Summary Video Mode" in Workbench.

V0 Strategy (rule-based, no LLM):
1. Split by blank lines
2. Parse "标题：内容" format
3. Extract "依据：" as evidence
4. First paragraph → overview candidate
5. Last paragraph with conclusion keywords → conclusion candidate
"""

import re
import uuid
from datetime import datetime
from typing import Any


# ─── Evidence extraction ───────────────────────────────────────────────────────

_EVIDENCE_RE = re.compile(r"依据[：:]\s*(.+)", re.IGNORECASE)
_CONCLUSION_KEYWORDS = ["这说明", "总体来看", "整体来看", "趋势是", "总结", "结论", "意味着", "说明"]


def _extract_evidence(text: str) -> tuple[str, str | None]:
    """Split text into main content and evidence. Returns (content, evidence)."""
    m = _EVIDENCE_RE.search(text)
    if m:
        evidence = m.group(1).strip()
        content = _EVIDENCE_RE.sub("", text).strip()
        # Clean up trailing punctuation
        content = re.sub(r"[。；]\s*$", "", content).strip()
        return content, evidence
    return text.strip(), None


def _parse_paragraph(para: str, index: int) -> dict[str, Any]:
    """Parse a single paragraph into {title, description, evidence, sourceText}."""
    para = para.strip()
    if not para:
        return {"id": f"item_{index}", "title": "", "description": "", "selected": True}

    title = ""
    description = para

    # Try "标题：内容" or "标题-内容" format
    for sep in ["：", ":", "－", "-"]:
        if sep in para:
            idx = para.index(sep)
            maybe_title = para[:idx].strip()
            maybe_desc = para[idx + 1 :].strip()
            if maybe_title and maybe_desc and len(maybe_title) < 50:
                title = maybe_title
                description = maybe_desc
                break

    content, evidence = _extract_evidence(description)

    return {
        "id": f"item_{index}",
        "title": title,
        "description": content,
        "evidence": [evidence] if evidence else [],
        "sourceText": para,
        "selected": True,
    }


def _is_conclusion_paragraph(para: str) -> bool:
    """Check if paragraph looks like a conclusion."""
    para_lower = para.lower()
    return any(kw in para_lower for kw in _CONCLUSION_KEYWORDS)


def _generate_conclusion(items: list[dict], original_conclusion_para: str | None) -> dict[str, str]:
    """Generate conclusion from items or use original conclusion paragraph."""
    if original_conclusion_para:
        # Try to extract title from conclusion
        title = "总结"
        desc = original_conclusion_para.strip()
        for sep in ["：", ":", "－", "-"]:
            if sep in original_conclusion_para:
                idx = original_conclusion_para.index(sep)
                maybe_title = original_conclusion_para[:idx].strip()
                maybe_desc = original_conclusion_para[idx + 1 :].strip()
                if maybe_title and maybe_desc:
                    title = maybe_title
                    desc = maybe_desc
                    break
        return {"title": title, "text": desc}

    # Auto-generate conclusion from selected items
    selected_titles = [item["title"] for item in items if item.get("selected") and item.get("title")]
    if not selected_titles:
        return {"title": "总结", "text": "以上是本次主要内容。"}
    return {
        "title": "总结",
        "text": f"本期涵盖 {len(selected_titles)} 个要点，包括：{'、'.join(selected_titles[:3])}{'等' if len(selected_titles) > 3 else ''}。",
    }


def _estimate_duration(item_count: int, has_overview: bool, has_conclusion: bool) -> int:
    """Estimate video duration in seconds based on content structure."""
    base = item_count * 8  # ~8 seconds per item
    if has_overview:
        base += 5
    if has_conclusion:
        base += 5
    return max(15, base)


# ─── Main public function ─────────────────────────────────────────────────────

def generate_information_structure(
    content: str,
    *,
    compression_mode: str = "balanced",
    target_point_count: str = "auto",
    include_overview: bool = True,
    include_conclusion: bool = True,
    evidence_policy: str = "ending_sources",
    target_duration_mode: str = "auto",
) -> dict[str, Any]:
    """
    Parse content and generate an InformationSummaryPlan structure.

    Args:
        content: Raw text content (title + body)
        compression_mode: "brief" | "balanced" | "strict" | "itemized" | "manual"
        target_point_count: "auto" | 3 | 5 | 8 | "all"
        include_overview: Whether to generate overview card
        include_conclusion: Whether to generate conclusion card
        evidence_policy: "hide" | "badge" | "ending_sources" | "keep_inline"
        target_duration_mode: "auto" | 30 | 60 | 90

    Returns:
        InformationSummaryPlan dict
    """
    # Split into paragraphs by blank lines
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]

    if not paragraphs:
        return {
            "mode": "information_summary",
            "compressionMode": compression_mode,
            "targetPointCount": target_point_count,
            "includeOverview": include_overview,
            "includeConclusion": include_conclusion,
            "evidencePolicy": evidence_policy,
            "targetDurationMode": target_duration_mode,
            "overview": {"title": "内容概览", "subtitle": "", "summary": "（未识别到内容）"},
            "items": [],
            "conclusion": {"title": "总结", "text": ""},
            "stats": {"detectedItemCount": 0, "selectedItemCount": 0, "droppedItemCount": 0, "estimatedDurationSec": 0},
        }

    # Parse all paragraphs into items
    raw_items: list[dict[str, Any]] = []
    conclusion_para: str | None = None

    for i, para in enumerate(paragraphs):
        if i == len(paragraphs) - 1 and _is_conclusion_paragraph(para):
            conclusion_para = para
        else:
            parsed = _parse_paragraph(para, len(raw_items))
            if parsed["title"] or parsed["description"]:
                raw_items.append(parsed)

    # Determine target count based on compression mode
    total_items = len(raw_items)
    if compression_mode == "brief":
        target_count = 3
    elif compression_mode == "balanced":
        target_count = min(7, max(5, total_items))
    elif compression_mode == "strict":
        target_count = total_items
    elif compression_mode == "itemized":
        target_count = total_items
    else:  # manual or auto
        if target_point_count == "auto":
            target_count = min(7, max(5, total_items))
        elif target_point_count == "all":
            target_count = total_items
        else:
            target_count = int(target_point_count)

    # Select items (keep first N, mark rest as dropped)
    selected_items: list[dict[str, Any]] = []
    dropped_items: list[dict[str, Any]] = []

    for i, item in enumerate(raw_items):
        if i < target_count:
            item["selected"] = True
            selected_items.append(item)
        else:
            item["selected"] = False
            dropped_items.append(item)

    # Determine if first item is overview-like
    overview_candidate = ""
    if selected_items and len(selected_items[0]["title"]) < 30 and len(selected_items[0]["description"]) > 50:
        # First item looks like an overview
        overview_candidate = selected_items[0]["title"]
        if include_overview:
            overview_text = f"{selected_items[0]['title']}：{selected_items[0]['description']}"
            if selected_items[0].get("evidence"):
                overview_text += f"（{'、'.join(selected_items[0]['evidence'])})"
        else:
            overview_text = ""
        overview = {
            "title": selected_items[0]["title"] if include_overview else "内容概览",
            "subtitle": "",
            "summary": overview_text if include_overview else "",
        }
        if include_overview:
            selected_items = selected_items[1:]  # Remove from items if used as overview
    else:
        overview = {
            "title": "内容概览",
            "subtitle": "",
            "summary": paragraphs[0][:100] if paragraphs else "（内容概览）",
        }

    # Generate conclusion
    conclusion = _generate_conclusion(selected_items + dropped_items, conclusion_para)

    # Build output items
    output_items = selected_items.copy()
    if include_conclusion:
        # Add dropped items to conclusion text if not already there
        if dropped_items and compression_mode != "strict":
            dropped_titles = [item["title"] for item in dropped_items if item.get("title")]
            if dropped_titles:
                conclusion["text"] += f"\n另有 {len(dropped_titles)} 项内容因篇幅限制未展开：{'、'.join(dropped_titles[:3])}{'等' if len(dropped_titles) > 3 else ''}。"

    # Estimate duration
    item_count_for_duration = len(output_items) + (1 if include_overview else 0) + (1 if include_conclusion else 0)
    if target_duration_mode == "auto":
        estimated_duration = _estimate_duration(len(output_items), include_overview, include_conclusion)
    else:
        estimated_duration = int(target_duration_mode)

    return {
        "mode": "information_summary",
        "compressionMode": compression_mode,
        "targetPointCount": target_point_count,
        "includeOverview": include_overview,
        "includeConclusion": include_conclusion,
        "evidencePolicy": evidence_policy,
        "targetDurationMode": target_duration_mode,
        "overview": overview,
        "items": output_items,
        "conclusion": conclusion if include_conclusion else {"title": "", "text": ""},
        "stats": {
            "detectedItemCount": total_items,
            "selectedItemCount": len(output_items),
            "droppedItemCount": len(dropped_items),
            "estimatedDurationSec": estimated_duration,
        },
    }


def serialize_for_visual_compose(plan: dict[str, Any]) -> str:
    """
    Serialize InformationSummaryPlan into a text format suitable for visual-compose.

    Format:
    【首页总览】
    title: ...
    summary: ...

    【信息点 1】
    标题：...
    描述：...
    依据：...

    【信息点 2】
    ...

    【尾部总结】
    ...
    """
    lines: list[str] = []

    if plan.get("includeOverview") and plan.get("overview"):
        ov = plan["overview"]
        lines.append("【首页总览】")
        if ov.get("title"):
            lines.append(f"标题：{ov['title']}")
        if ov.get("summary"):
            lines.append(f"摘要：{ov['summary']}")
        lines.append("")

    for i, item in enumerate(plan.get("items", []), 1):
        lines.append(f"【信息点 {i}】")
        if item.get("title"):
            lines.append(f"标题：{item['title']}")
        if item.get("description"):
            lines.append(f"描述：{item['description']}")
        if item.get("evidence") and plan.get("evidencePolicy") != "hide":
            ev_text = "、".join(item["evidence"])
            if plan.get("evidencePolicy") == "badge":
                lines.append(f"依据：{ev_text}")
            elif plan.get("evidencePolicy") == "keep_inline":
                lines.append(f"（依据：{ev_text}）")
            # ending_sources is handled separately in video
        lines.append("")

    if plan.get("includeConclusion") and plan.get("conclusion"):
        coc = plan["conclusion"]
        lines.append("【尾部总结】")
        if coc.get("title"):
            lines.append(f"标题：{coc['title']}")
        if coc.get("text"):
            lines.append(f"内容：{coc['text']}")

    return "\n".join(lines)
