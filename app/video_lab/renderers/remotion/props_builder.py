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
    # V0.3.6-quality-p0: also carry metrics for data visualization
    from app.video_lab.renderers.theme_presets import resolve_shot_tone

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
                # V0.3.6-quality-p0: carry through metrics if present
                "metrics": kp.get("metrics", []),
                # 主题自适应：解析每条基调（LLM 给的优先，否则按文本推断）
                "tone": resolve_shot_tone(kp),
            })
        else:
            key_points_list.append({
                "title": str(kp),
                "body": "",
                "source": "",
                "emphasisTerms": [],
                "metrics": [],
                "tone": "neutral",
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
        # V0.3.6-quality-p0-fix: showDataViz flag for metric visualization
        "showDataViz": params.get("showDataViz", True) is not False,
    }
    if segment_durations_prop:
        props["segmentDurations"] = segment_durations_prop
        # V0.8.1: timelineDebug snapshot for post-hoc inspection of
        # remotion_props.json (without touching the frontend). Helps trace
        # why a given render's visual timeline diverges from audio.
        props["timelineDebug"] = {
            "source": "voiceover_segments",
            "segmentCount": len(segment_durations),
            "coverSec": segment_durations_prop["coverSec"],
            "cardSecs": list(segment_durations_prop["cardSecs"]),
            "summarySec": segment_durations_prop["summarySec"],
            "totalSec": duration_sec,
        }

    # V0.8.2: contentDebug snapshot for cheap post-hoc inspection.
    # Mirrors the content the Remotion template will render so users can
    # diff "what we said the title was" vs "what came out". Includes per-KP
    # metrics to diagnose "number chart missing" reports. Diagnostic-only;
    # not read by the template.
    metrics_by_key_point = []
    for _i, _kp in enumerate(key_points_list, 1):
        metrics_by_key_point.append({
            "index": _i,
            "title": _kp.get("title", ""),
            "metrics": list(_kp.get("metrics", []) or []),
        })
    has_metrics = any(bool(m.get("metrics")) for m in metrics_by_key_point)
    props["contentDebug"] = {
        "title": title,
        "subtitle": subtitle,
        "keyPointCount": len(key_points_list),
        "keyPointTitles": [kp.get("title", "") for kp in key_points_list],
        "keyPointBodies": [kp.get("body", "") for kp in key_points_list],
        "metricsByKeyPoint": metrics_by_key_point,
        "hasMetrics": has_metrics,
        "style": style,
        "remotionFamily": props.get("remotionFamily", "data_news"),
    }

    # 可调样式（对应调试台旋钮：配色/字号/图标）
    # V0.3.7: remotionStyle takes priority; top-level params also accepted
    rstyle = params.get("remotionStyle") if isinstance(params.get("remotionStyle"), dict) else {}
    style: dict[str, Any] = {}
    accent = rstyle.get("accentColor") or params.get("accentColor")
    highlight = rstyle.get("highlightColor") or params.get("highlightColor")
    font_scale = rstyle.get("fontScale") or params.get("fontScale")
    show_icon = rstyle.get("showIcon") if rstyle.get("showIcon") is not None else params.get("showIcon")
    if accent:
        style["accentColor"] = accent
    if highlight:
        style["highlightColor"] = highlight
    if font_scale:
        try:
            style["fontScale"] = float(font_scale)
        except (TypeError, ValueError):
            pass
    if show_icon is not None:
        style["showIcon"] = bool(show_icon)

    # V0.3.7: Additional Remotion style params
    motion_intensity = rstyle.get("motionIntensity") or params.get("motionIntensity")
    if motion_intensity:
        style["motionIntensity"] = motion_intensity
    cover_style = rstyle.get("coverStyle") or params.get("coverStyle")
    if cover_style:
        style["coverStyle"] = cover_style
    overview_style = rstyle.get("overviewStyle") or params.get("overviewStyle")
    if overview_style:
        style["overviewStyle"] = overview_style
    metric_animation = rstyle.get("metricAnimation") or params.get("metricAnimation")
    if metric_animation:
        style["metricAnimation"] = metric_animation
    transition_style = rstyle.get("transitionStyle") or params.get("transitionStyle")
    if transition_style:
        style["transitionStyle"] = transition_style

    if style:
        props["style"] = style

    # V0.6.2: Remotion family — selects presentation paradigm (data_news | card_stack)
    remotion_family = params.get("remotionFamily")
    if remotion_family in ("data_news", "card_stack"):
        props["remotionFamily"] = remotion_family

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
