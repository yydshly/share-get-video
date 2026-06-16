"""
visual_profiles.py - Visual rendering parameter profiles.

Provides named visual profiles (ai_frontier_dark, data_card_dense, etc.)
with sensible defaults for each presentation style. Profiles can be
referenced by ID in API params, and user-supplied overrides always
take precedence over profile defaults.

This is a pure data layer — no UI changes, no template changes.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_PROFILE_ID = "ai_frontier_dark"


VISUAL_PROFILES: dict[str, dict[str, Any]] = {
    "ai_frontier_dark": {
        "id": "ai_frontier_dark",
        "label": "AI Frontier Dark",
        "description": "默认深色 AI 资讯风格，适合前沿动态和数据摘要。",
        "defaults": {
            "showDataViz": True,
            "themeAdaptive": True,
            "contentAlign": "center",
            "motionIntensity": "medium",
            "coverStyle": "editorial",
            "overviewStyle": "timeline",
            "metricAnimation": "countup_bar",
            "transitionStyle": "slide_fade",
        },
    },
    "data_card_dense": {
        "id": "data_card_dense",
        "label": "Data Card Dense",
        "description": "高信息密度数据卡，适合 benchmark / 指标 / 数字密集内容。",
        "defaults": {
            "showDataViz": True,
            "themeAdaptive": True,
            "contentAlign": "top",
            "motionIntensity": "medium",
            "coverStyle": "minimal",
            "overviewStyle": "grid",
            "metricAnimation": "countup_number",
            "transitionStyle": "fade",
        },
    },
    "editorial_clean": {
        "id": "editorial_clean",
        "label": "Editorial Clean",
        "description": "干净编辑风，减少装饰，优先保证可读性。",
        "defaults": {
            "showDataViz": False,
            "themeAdaptive": False,
            "contentAlign": "center",
            "motionIntensity": "low",
            "coverStyle": "minimal",
            "overviewStyle": "clean",
            "metricAnimation": "none",
            "transitionStyle": "fade",
        },
    },
    "cinematic_summary": {
        "id": "cinematic_summary",
        "label": "Cinematic Summary",
        "description": "电影感摘要风格，适合重点报道和氛围型资讯。",
        "defaults": {
            "showDataViz": True,
            "themeAdaptive": True,
            "contentAlign": "center",
            "motionIntensity": "low",
            "coverStyle": "cinematic",
            "overviewStyle": "grid",
            "metricAnimation": "countup_number",
            "transitionStyle": "fade",
        },
    },
    "low_motion_readable": {
        "id": "low_motion_readable",
        "label": "Low Motion Readable",
        "description": "低动效高可读，适合先验证内容准确性和字幕节奏。",
        "defaults": {
            "showDataViz": False,
            "themeAdaptive": False,
            "contentAlign": "center",
            "motionIntensity": "low",
            "coverStyle": "minimal",
            "overviewStyle": "clean",
            "metricAnimation": "none",
            "transitionStyle": "fade",
            "transitionEnabled": False,
            "transitionFrames": 0,
        },
    },
}


def get_visual_profile(profile_id: str | None) -> tuple[dict[str, Any], list[str]]:
    """
    Look up a visual profile by ID.

    Args:
        profile_id: profile identifier (e.g. "ai_frontier_dark")

    Returns:
        (profile_dict, warnings_list)

    If profile_id is None or unknown, falls back to DEFAULT_PROFILE_ID
    and appends a warning.
    """
    warnings: list[str] = []
    pid = profile_id or DEFAULT_PROFILE_ID
    profile = VISUAL_PROFILES.get(pid)
    if not profile:
        warnings.append(f"Unknown visualProfile '{pid}', falling back to '{DEFAULT_PROFILE_ID}'")
        profile = VISUAL_PROFILES[DEFAULT_PROFILE_ID]
    return deepcopy(profile), warnings


def merge_visual_profile(
    profile_id: str | None,
    overrides: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    """
    Merge a visual profile with explicit overrides.

    Priority (highest first):
        1. Explicit overrides (user-supplied params)
        2. Profile defaults

    Args:
        profile_id: profile identifier
        overrides: explicit parameter overrides from API call

    Returns:
        (merged_params_dict, warnings_list)
        merged_params_dict includes a "visualProfile" key with the profile id.
    """
    profile, warnings = get_visual_profile(profile_id)
    merged = deepcopy(profile.get("defaults", {}))
    merged.update(overrides or {})
    merged["visualProfile"] = profile["id"]
    return merged, warnings
