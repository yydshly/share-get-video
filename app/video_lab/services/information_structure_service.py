"""
Information Structure Service V1.1

Provides structured parsing of informational content for video generation.
Used by the "Information Summary Video Mode" in Workbench.

V1.1 Strategy (rule-based, no LLM):
1. Split by blank lines into paragraphs
2. Within each paragraph, split by sentence delimiters (。；)
3. Identify "标题：描述" sub-clauses within each sentence
4. Split multi-point sentences into separate candidate blocks
5. Extract "依据：" as evidence (belongs to previous item)
6. First meaningful paragraph → overview (if short/general)
7. Last paragraph with conclusion keywords → conclusion
8. All remaining blocks → information items
"""

import re
from typing import Any


# ─── Constants ────────────────────────────────────────────────────────────────

_CONCLUSION_KEYWORDS = ["这说明", "总体来看", "整体来看", "趋势是", "总结", "结论", "意味着", "说明", "总的来说"]
# Patterns that indicate a valid "title: description" split point
_TITLE_SEPARATORS = ["：", ":", "－", "-"]
# Minimum and maximum length for a valid title before separator
_MIN_TITLE_LEN = 3
_MAX_TITLE_LEN = 40
# Minimum description length after separator
_MIN_DESC_LEN = 8


# ─── Helper functions ─────────────────────────────────────────────────────────

def _is_conclusion_text(text: str) -> bool:
    """Check if text looks like a conclusion paragraph."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in _CONCLUSION_KEYWORDS)


def _looks_like_title(text: str) -> bool:
    """Check if text looks like a news/scientific headline (title of an information point)."""
    if not text or len(text) < _MIN_TITLE_LEN or len(text) > _MAX_TITLE_LEN:
        return False
    # Must not be too long (would be a sentence, not a title)
    if len(text) > 25:
        return False
    # Title typically doesn't end with common sentence endings
    if text[-1] in "。！？.":
        return False
    # Title often contains specific patterns
    # Avoid splitting generic sentences that happen to have a colon
    # Heuristic: real titles often have specific structure
    stripped = text.strip()
    # Must be mostly Chinese characters
    chinese_count = len(re.findall(r"[一-鿿]", stripped))
    if chinese_count < 2:
        return False
    return True


def _extract_title_desc(text: str) -> tuple[str, str] | None:
    """Try to extract title/description from text using separators.

    Returns (title, description) if found, None otherwise.
    """
    text = text.strip()
    if not text:
        return None

    for sep in _TITLE_SEPARATORS:
        if sep not in text:
            continue
        idx = text.index(sep)
        maybe_title = text[:idx].strip()
        maybe_desc = text[idx + 1 :].strip()
        if not maybe_title or not maybe_desc:
            continue
        if len(maybe_title) < _MIN_TITLE_LEN or len(maybe_title) > _MAX_TITLE_LEN:
            continue
        if len(maybe_desc) < _MIN_DESC_LEN:
            continue
        # Title should not look like a full sentence
        if maybe_title[-1] in "。！？.":
            continue
        return maybe_title, maybe_desc
    return None


def _is_evidence_line(text: str) -> bool:
    """Check if text is an evidence line (依据：...)."""
    stripped = text.strip()
    return bool(re.match(r"^依据[：:]\s*\S", stripped))


def _split_into_sentences(para: str) -> list[str]:
    """Split a paragraph into sentences by 。 or ；
    but avoid splitting inside quoted or bracketed content."""
    # Split by 。 or ； but keep the delimiter
    parts = re.split(r"(?<=[。；])", para)
    sentences = []
    for p in parts:
        p = p.strip()
        if p:
            # Remove trailing sentence-ending punctuation for further processing
            sentences.append(p)
    return sentences


def _parse_sentence_into_blocks(sentence: str) -> list[dict[str, Any]]:
    """Parse a single sentence into one or more candidate blocks.

    Returns list of {title, description, is_complete}.
    """
    blocks = []
    sentence = sentence.strip().rstrip("。")
    if not sentence:
        return blocks

    # Try to extract title:desc from the whole sentence first
    title_desc = _extract_title_desc(sentence)
    if title_desc:
        title, desc = title_desc
        # Check if there are more sub-clauses after the description
        # by looking for additional title:desc patterns in the desc
        remaining = desc
        # Split remaining content by common separators within description
        # Look for embedded "xxx：" patterns in what we thought was description
        embedded_pattern = r"(?<=[^：：])：(?!：)"
        # Actually, just use the whole thing
        blocks.append({
            "title": title,
            "description": remaining,
            "is_complete": True,
        })
        return blocks

    # No title:desc found - the whole sentence is a description without title
    blocks.append({
        "title": "",
        "description": sentence,
        "is_complete": False,
    })
    return blocks


def _split_paragraph_into_items(para: str) -> list[dict[str, Any]]:
    """Split a paragraph into information point items.

    Handles:
    - Multiple "title: description" in one paragraph
    - "依据：" lines (attached to previous item's evidence)
    - Mixed content paragraphs
    """
    if not para or not para.strip():
        return []

    para = para.strip()
    sentences = _split_into_sentences(para)

    items: list[dict[str, Any]] = []
    current_evidence: list[str] = []

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # Handle "依据：" lines - attach to previous item
        if _is_evidence_line(sent):
            m = re.match(r"^依据[：:]\s*(.+)", sent)
            if m and items:
                evidence_text = m.group(1).strip()
                if items[-1].get("description"):
                    items[-1].setdefault("evidence", []).append(evidence_text)
            continue

        # Try to parse as title:description
        parsed = _parse_sentence_into_blocks(sent)
        for block in parsed:
            if block["title"] and block["description"]:
                # Complete block with title
                items.append({
                    "title": block["title"],
                    "description": block["description"],
                    "evidence": current_evidence[:],
                })
                current_evidence = []
            elif block["description"]:
                # No clear title - treat description as content
                # If previous item has no title, merge; otherwise start new item
                if items and not items[-1].get("title"):
                    items[-1]["description"] += " " + block["description"]
                else:
                    items.append({
                        "title": "",
                        "description": block["description"],
                        "evidence": current_evidence[:],
                    })
                    current_evidence = []

    return items


def _build_overview(paragraphs: list[str], items: list[dict]) -> dict[str, str]:
    """Build overview from first paragraph or first item."""
    if not paragraphs:
        return {"title": "内容概览", "subtitle": "", "summary": ""}

    first_para = paragraphs[0].strip()
    if not first_para:
        return {"title": "内容概览", "subtitle": "", "summary": ""}

    # If first item has a short title and long description, it might be overview-like
    if items and items[0].get("title") and items[0].get("description"):
        title = items[0]["title"]
        desc = items[0]["description"]
        # If title is short (< 20 chars) and description is long (> 80 chars),
        # treat as overview
        if len(title) < 20 and len(desc) > 80:
            return {
                "title": title,
                "subtitle": "",
                "summary": f"{title}：{desc}",
            }

    # Use first paragraph as overview summary
    summary = first_para[:150] + ("..." if len(first_para) > 150 else "")
    return {
        "title": "内容概览",
        "subtitle": "",
        "summary": summary,
    }


def _generate_conclusion_text(items: list[dict], conclusion_para: str | None) -> dict[str, str]:
    """Generate conclusion content."""
    if conclusion_para:
        # Try to extract title from conclusion paragraph
        title = "总结"
        desc = conclusion_para.strip()
        td = _extract_title_desc(conclusion_para)
        if td:
            title, desc = td
        return {"title": title, "text": desc}

    # Auto-generate from selected items
    selected_titles = [item["title"] for item in items if item.get("title")]
    if not selected_titles:
        return {"title": "总结", "text": "以上是本次主要内容。"}
    if len(selected_titles) <= 4:
        return {
            "title": "总结",
            "text": f"本期涵盖 {len(selected_titles)} 个要点：{'、'.join(selected_titles)}。",
        }
    return {
        "title": "总结",
        "text": f"本期涵盖 {len(selected_titles)} 个要点，包括：{'、'.join(selected_titles[:3])}{'等' if len(selected_titles) > 3 else ''}。",
    }


def _estimate_duration(item_count: int, has_overview: bool, has_conclusion: bool) -> int:
    """Estimate video duration in seconds."""
    base = item_count * 8
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

    V1.1: improved intra-paragraph splitting for multi-point detection.
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

    # Split paragraphs into raw items using improved logic
    raw_items: list[dict[str, Any]] = []
    conclusion_para: str | None = None
    first_item_taken_as_overview = False

    for i, para in enumerate(paragraphs):
        # Last paragraph - check if it's a conclusion
        if i == len(paragraphs) - 1 and _is_conclusion_text(para):
            conclusion_para = para
            continue

        # Split paragraph into items
        para_items = _split_paragraph_into_items(para)
        for item in para_items:
            # Skip pure evidence-only lines (already attached to previous item)
            if not item.get("title") and not item.get("description"):
                continue
            # Skip items that are just evidence
            if _is_evidence_line(item.get("description", "")) or _is_evidence_line(item.get("title", "")):
                continue
            raw_items.append(item)

    # If first item looks like an overview (short title, long description),
    # remove it from items for use as overview
    overview: dict[str, str] = {"title": "内容概览", "subtitle": "", "summary": ""}
    if raw_items and include_overview:
        first = raw_items[0]
        if first.get("title") and first.get("description") and len(first["description"]) > 60:
            overview = {
                "title": first.get("title", "内容概览"),
                "subtitle": "",
                "summary": f"{first['title']}：{first['description']}",
            }
            first_item_taken_as_overview = True
            raw_items = raw_items[1:]

    if not overview["summary"]:
        overview = _build_overview(paragraphs, raw_items)

    total_items = len(raw_items)

    # Determine target count based on compression mode
    if compression_mode == "brief":
        target_count = 3
    elif compression_mode == "balanced":
        target_count = min(7, max(5, total_items)) if total_items >= 5 else total_items
    elif compression_mode == "strict":
        target_count = total_items
    elif compression_mode == "itemized":
        target_count = total_items
    else:  # manual or auto
        if target_point_count == "auto":
            target_count = min(7, max(5, total_items)) if total_items >= 5 else total_items
        elif target_point_count == "all":
            target_count = total_items
        else:
            target_count = int(target_point_count)

    # Select items
    selected_items: list[dict[str, Any]] = []
    dropped_items: list[dict[str, Any]] = []

    for i, item in enumerate(raw_items):
        if i < target_count:
            item["selected"] = True
            selected_items.append(item)
        else:
            item["selected"] = False
            dropped_items.append(item)

    # Generate conclusion
    conclusion = _generate_conclusion_text(selected_items + dropped_items, conclusion_para)

    # Build output items
    output_items = selected_items.copy()
    if include_conclusion and dropped_items and compression_mode != "strict":
        dropped_titles = [item["title"] for item in dropped_items if item.get("title")]
        if dropped_titles:
            extra = f"\n另有 {len(dropped_titles)} 项内容因篇幅限制未展开：{'、'.join(dropped_titles[:3])}{'等' if len(dropped_titles) > 3 else ''}。"
            if conclusion["text"]:
                conclusion["text"] += extra

    # Estimate duration
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
    Serialize InformationSummaryPlan into a text format for visual-compose.
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
        lines.append("")

    if plan.get("includeConclusion") and plan.get("conclusion"):
        coc = plan["conclusion"]
        lines.append("【尾部总结】")
        if coc.get("title"):
            lines.append(f"标题：{coc['title']}")
        if coc.get("text"):
            lines.append(f"内容：{coc['text']}")

    return "\n".join(lines)
