"""Source-bound information summary plan helpers."""

from __future__ import annotations

import re
from typing import Any


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _selected_items(info_plan: dict) -> list[dict]:
    items = info_plan.get("items", [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get("selected") is True]


def _evidence_text(item: dict) -> str:
    evidence = item.get("evidence", [])
    if isinstance(evidence, str):
        return _clean_text(evidence)
    if isinstance(evidence, list):
        parts = [_clean_text(part) for part in evidence]
        return " ".join(part for part in parts if part)
    return ""


def _evidence_list(item: dict) -> list[str]:
    evidence = item.get("evidence", [])
    if isinstance(evidence, str):
        text = _clean_text(evidence)
        return [text] if text else []
    if isinstance(evidence, list):
        return [text for text in (_clean_text(part) for part in evidence) if text]
    return []


def _emphasis_terms(title: str) -> list[str]:
    title = _clean_text(title)
    if not title:
        return []
    parts = [part.strip() for part in re.split(r"[，,、:：\s]+", title) if part.strip()]
    terms: list[str] = []
    for term in [title, *parts]:
        if term and term not in terms:
            terms.append(term)
        if len(terms) >= 5:
            break
    return terms


def build_structured_from_information_summary_plan(info_plan: dict) -> dict:
    """Build the minimal structured artifact without parsing serialized text."""
    overview = info_plan.get("overview") if isinstance(info_plan.get("overview"), dict) else {}
    selected_items = _selected_items(info_plan)
    lead = _clean_text(overview.get("summary")) or _clean_text(overview.get("title"))
    items = [
        {
            "title": _clean_text(item.get("title")),
            "body": _clean_text(item.get("description")),
            "source": "informationSummaryPlan",
        }
        for item in selected_items
    ]
    return {
        "lead": lead,
        "items": items,
        "totalItems": len(items),
        "source": "informationSummaryPlan",
    }


def build_source_bound_plan_from_information_summary(
    info_plan: dict,
    target_duration_sec: float | None = None,
) -> dict:
    """Build a plan_shots-compatible plan directly from informationSummaryPlan."""
    overview = info_plan.get("overview") if isinstance(info_plan.get("overview"), dict) else {}
    conclusion = info_plan.get("conclusion") if isinstance(info_plan.get("conclusion"), dict) else {}
    selected_items = _selected_items(info_plan)
    input_profile = _clean_text(info_plan.get("inputProfile"))
    is_report_source_bound = input_profile == "report_overview_items"
    metadata = info_plan.get("metadata") if isinstance(info_plan.get("metadata"), dict) else {}
    report_title = (
        _clean_text(info_plan.get("reportTitle"))
        or _clean_text(info_plan.get("videoTitle"))
        or _clean_text(metadata.get("title"))
    )

    shots = []
    source_refs = []
    for idx, item in enumerate(selected_items, 1):
        title = _clean_text(item.get("title")) or f"信息点 {idx}"
        description = _clean_text(item.get("description"))
        display = description
        evidence = _evidence_list(item)
        if evidence:
            source_refs.append({
                "itemIndex": idx,
                "itemTitle": title,
                "evidence": evidence,
            })
        shots.append(
            {
                "headline": title,
                "display": display,
                "narration": description or title,
                "emphasisTerms": _emphasis_terms(title),
                "metrics": item.get("metrics") if isinstance(item.get("metrics"), list) else [],
                "tone": _clean_text(item.get("tone")),
            }
        )

    return {
        "coverTitle": report_title or _clean_text(overview.get("title")) or ("报告摘要" if is_report_source_bound else "今日重点"),
        "opening": _clean_text(overview.get("summary")) or _clean_text(overview.get("title")),
        "shots": shots,
        "closing": _clean_text(conclusion.get("text")),
        "source": "source_bound_information_summary",
        "structureType": "report_source_bound" if is_report_source_bound else "source_bound_information_summary",
        "overview": {
            "title": _clean_text(overview.get("title")),
            "summary": _clean_text(overview.get("summary")),
        },
        "includeOverview": bool(info_plan.get("includeOverview", True)),
        "includeConclusion": bool(info_plan.get("includeConclusion", True)),
        "sourceRefs": source_refs,
        "reportTitle": report_title,
        "targetDurationSec": target_duration_sec,
    }
