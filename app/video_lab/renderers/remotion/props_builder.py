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

    # Build keyPoints array
    kps_list = key_points.get("keyPoints", key_points.get("key_points", []))
    key_points_list = []
    for kp in kps_list:
        if isinstance(kp, dict):
            key_points_list.append({
                "title": kp.get("title", ""),
                "body": kp.get("body", ""),
                "source": kp.get("source", ""),
            })
        else:
            key_points_list.append({
                "title": str(kp),
                "body": "",
                "source": "",
            })

    # Duration from params or default
    target_duration = params.get("targetDuration", 45)
    # Remotion template allocates ~3s cover + ~5s per keypoint + ~5s summary
    num_kps = len(key_points_list)
    estimated_duration = 3 + num_kps * 5 + 5  # seconds
    duration_sec = min(target_duration, max(estimated_duration, 15))

    props = {
        "title": title,
        "subtitle": subtitle,
        "keyPoints": key_points_list,
        "durationSec": duration_sec,
        "stylePreset": "ai_frontier_dark",
    }

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
