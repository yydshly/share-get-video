"""
props_builder.py - Build Remotion props JSON from structured content
V0.3.1: Minimum verification
"""

import json
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import get_experiment_dir


def build_remotion_props(
    experiment_id: str,
    structured: dict[str, Any],
    key_points: dict[str, Any],
    params: dict[str, Any],
    segment_durations: list | None = None,
) -> dict[str, Any]:
    """
    Build Remotion props JSON for AiNewsVideo template.

    Args:
        experiment_id: experiment identifier
        structured: structured content (from content_structurer)
        key_points: key points (from key_point_extractor)
        params: render parameters (targetDuration, etc.)

    Returns:
        dict suitable for Remotion --props JSON input
    """
    # Extract title from structured content
    lead = structured.get("lead", "")
    title = _extract_title(lead)
    subtitle = structured.get("subtitle", "今日 AI 前沿速览")

    # Build keyPoints array (prefer LLM-planned headline/display)
    # V0.3.6-b1: also carry emphasisTerms for Remotion highlighting
    kps_list = key_points.get("keyPoints", key_points.get("key_points", []))
    key_points_list = []
    for kp in kps_list:
        if isinstance(kp, dict):
            key_points_list.append({
                "title": kp.get("headline") or kp.get("title", ""),
                "body": kp.get("display") or kp.get("body", ""),
                "source": kp.get("source", ""),
                # V0.3.6-b1: carry through emphasisTerms if present
                "emphasisTerms": kp.get("emphasisTerms", []),
            })
        else:
            key_points_list.append({
                "title": str(kp),
                "body": "",
                "source": "",
                "emphasisTerms": [],
            })

    num_kps = len(key_points_list)

    # 段时长与旁白对齐：segment_durations 顺序 [opening, item1..N, closing]
    segment_durations_prop = None
    duration_sec = None
    if segment_durations and len(segment_durations) == num_kps + 2 and num_kps > 0:
        seg = [float(s.get("durationSec", 0)) for s in segment_durations]
        segment_durations_prop = {
            "coverSec": round(seg[0], 2),
            "cardSecs": [round(x, 2) for x in seg[1:-1]],
            "summarySec": round(seg[-1], 2),
        }
        duration_sec = round(sum(seg), 2)

    if duration_sec is None:
        target_duration = params.get("targetDuration", 45)
        estimated_duration = 3 + num_kps * 5 + 5
        duration_sec = min(target_duration, max(estimated_duration, 15))

    props = {
        "title": title,
        "subtitle": subtitle,
        "keyPoints": key_points_list,
        "durationSec": duration_sec,
        "stylePreset": "ai_frontier_dark",
    }
    if segment_durations_prop:
        props["segmentDurations"] = segment_durations_prop

    # Write props to runtime directory
    props_path = _write_props_json(experiment_id, props)
    return props


def _write_props_json(experiment_id: str, props: dict[str, Any]) -> Path:
    """Write props JSON to experiment directory."""
    exp_dir = get_experiment_dir(experiment_id)
    props_path = exp_dir / "remotion_props.json"
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)
    return props_path


def get_props_path(experiment_id: str) -> Path:
    """Get path to remotion_props.json for an experiment."""
    return get_experiment_dir(experiment_id) / "remotion_props.json"


def _extract_title(lead: str) -> str:
    """Extract a short title from the lead text."""
    if not lead:
        return "AI 前沿动态"
    # Take first sentence or first 30 chars
    sentences = lead.split("。")
    first = sentences[0].strip()
    if len(first) > 30:
        return first[:30] + "..."
    return first if first else "AI 前沿动态"
