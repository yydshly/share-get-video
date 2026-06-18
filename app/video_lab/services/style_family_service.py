"""
Style Family Service — extracted from router.py V1.0.2.

Provides run_style_family_compare() for /style-family/compare endpoint.
V1.2.3: Added run_background_variant_matrix() for /style-family/background-matrix.
V1.2.4: Added run_transition_variant_matrix() for /style-family/transition-matrix.
"""

import time
from typing import Any

from app.video_lab.renderers.frame_preview import render_clip_preview


# Default content used when request.content is empty.
STYLE_FAMILY_DEFAULT_CONTENT = (
    "科学研究评审实现突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%。\n"
    "依据：依据 1\n"
    "购物AI助手落后：主流模型通过率仅57-77%。\n"
    "依据：依据 1\n"
    "企业级AI加速落地：Anthropic与TCS合作，DeepMind投资千万美元。\n"
    "依据：依据 1"
)

# Family spec: (response_key, family_id)
FAMILY_SPECS = [
    ("dataNews", "data_news"),
    ("cardStack", "card_stack"),
    ("timelineNews", "timeline_news"),
    ("dashboardBrief", "dashboard_brief"),
    ("captionStory", "caption_story"),
]


def run_style_family_compare(request) -> dict[str, Any]:
    """
    Compare Data News vs Card Stack vs Timeline vs Dashboard vs Caption Story
    Remotion presentation paradigms.

    V0.6.4: Let users see actual preview videos or frame extracts directly in the UI.
    No database, no history tracking — only returns current render results.

    Args:
        request: StyleFamilyCompareRequest object

    Returns:
        dict with family results + totalElapsedMs, preserving existing field names:
        dataNews, cardStack, timelineNews, dashboardBrief, captionStory.
    """
    t0 = time.time()

    content = request.content.strip() or STYLE_FAMILY_DEFAULT_CONTENT
    params = dict(request.params or {})
    params["visualRoute"] = "template_programmatic_render"
    clip_seconds = int(params.get("clipSeconds", 3))
    key_point_count = int(params.get("keyPointCount", 3))

    family_results: dict[str, dict[str, Any]] = {}
    for response_key, family_id in FAMILY_SPECS:
        family_params = {**params, "remotionFamily": family_id, "keyPointCount": key_point_count}
        family_results[response_key] = render_clip_preview(
            content=content,
            visual_route="template_programmatic_render",
            params=family_params,
            clip_seconds=clip_seconds,
        )

    elapsed = int((time.time() - t0) * 1000)

    def parse_result(r: dict) -> dict:
        return {
            "experimentId": r.get("experimentId", ""),
            "success": r.get("success", False),
            "videoUrl": r.get("clipUrl", ""),
            "clipSeconds": r.get("clipSeconds", clip_seconds),
            "elapsedMs": r.get("elapsedMs", 0),
            "message": r.get("message", ""),
            "warnings": r.get("warnings", []),
        }

    return {
        **{key: parse_result(value) for key, value in family_results.items()},
        "totalElapsedMs": elapsed,
    }


# V1.2.3: Lab-only 背景差异化实验
# Valid background presets (from props_builder.py)
VALID_BACKGROUND_PRESETS = [
    "tech_grid_dark",
    "aurora_blue",
    "glass_dashboard",
    "warm_cinematic",
    "neon_circuit",
    "deep_space",
]

# Valid families for matrix experiment
VALID_MATRIX_FAMILIES = [
    "timeline_news",
    "dashboard_brief",
    "caption_story",
]

VALID_TRANSITION_MATRIX_FAMILIES = [
    "data_news",
    "card_stack",
    "caption_story",
]

VALID_TRANSITION_STYLES = [
    "slide_fade",
    "fade",
    "slide",
    "push",
    "wipe",
    "zoom_blur",
    "flip",
    "glitch",
]

MAX_MATRIX_ITEMS = 9

# V1.2.4: Visual Style Preset Matrix
VALID_VISUAL_STYLE_MATRIX_FAMILIES = [
    "data_news",
    "dashboard_brief",
    "caption_story",
]

VALID_VISUAL_STYLE_PRESETS = [
    "light_editorial",
    "warm_paper",
    "bold_magazine",
]


def run_background_variant_matrix(request) -> dict[str, Any]:
    """
    V1.2.3: Background Variant Matrix — 3 families × 3 background presets = 9 clips.

    Lab-only: does NOT write Style Sweep job, Style Gallery sample, or promote.
    All clips are temporary lab assets.

    Args:
        request: BackgroundVariantMatrixRequest object

    Returns:
        {
            "items": [
                {
                    "family": "timeline_news",
                    "backgroundPreset": "tech_grid_dark",
                    "success": true,
                    "videoUrl": "/runtime/video_lab/experiments/clip_xxx/clip.mp4",
                    "elapsedMs": 12345,
                    "message": "",
                    "warnings": []
                },
                ...
            ],
            "totalElapsedMs": 123456
        }
    """
    t0 = time.time()

    content = request.content.strip() or STYLE_FAMILY_DEFAULT_CONTENT
    params = dict(request.params or {})
    params["visualRoute"] = "template_programmatic_render"
    clip_seconds = int(params.get("clipSeconds", 3))
    key_point_count = int(params.get("keyPointCount", 3))

    matrix_config = dict(request.matrix or {})
    families = matrix_config.get("families", VALID_MATRIX_FAMILIES)
    background_presets = matrix_config.get("backgroundPresets", VALID_BACKGROUND_PRESETS)

    # Filter to valid entries only
    families = [f for f in families if f in VALID_MATRIX_FAMILIES]
    background_presets = [bp for bp in background_presets if bp in VALID_BACKGROUND_PRESETS]

    # V1.2.4: Reject invalid / over-limit requests with clear error messages
    if not families:
        raise ValueError(
            f"families filter resulted in empty set. "
            f"Allowed values: {VALID_MATRIX_FAMILIES}"
        )
    if not background_presets:
        raise ValueError(
            f"backgroundPresets filter resulted in empty set. "
            f"Allowed values: {VALID_BACKGROUND_PRESETS}"
        )
    total = len(families) * len(background_presets)
    if total > MAX_MATRIX_ITEMS:
        raise ValueError(
            f"background matrix is limited to {MAX_MATRIX_ITEMS} clips per request, "
            f"but {total} requested ({len(families)} families × {len(background_presets)} presets). "
            f"Reduce families or presets."
        )

    items: list[dict[str, Any]] = []

    for family_id in families:
        for bg_preset in background_presets:
            family_params = {
                **params,
                "remotionFamily": family_id,
                "keyPointCount": key_point_count,
                "backgroundPreset": bg_preset,
            }
            result = render_clip_preview(
                content=content,
                visual_route="template_programmatic_render",
                params=family_params,
                clip_seconds=clip_seconds,
            )
            items.append({
                "family": family_id,
                "backgroundPreset": bg_preset,
                "success": result.get("success", False),
                "videoUrl": result.get("clipUrl", ""),
                "experimentId": result.get("experimentId", ""),
                "clipSeconds": result.get("clipSeconds", clip_seconds),
                "elapsedMs": result.get("elapsedMs", 0),
                "message": result.get("message", ""),
                "warnings": result.get("warnings", []),
            })

    elapsed = int((time.time() - t0) * 1000)

    return {
        "items": items,
        "totalElapsedMs": elapsed,
    }


def run_transition_variant_matrix(request) -> dict[str, Any]:
    """
    V1.2.4: Transition Variant Matrix - family x transition style clips.

    Lab-only: mirrors background matrix behavior and does not persist samples.
    """
    t0 = time.time()

    content = request.content.strip() or STYLE_FAMILY_DEFAULT_CONTENT
    params = dict(request.params or {})
    params["visualRoute"] = "template_programmatic_render"
    clip_seconds = int(params.get("clipSeconds", 3))
    key_point_count = int(params.get("keyPointCount", 3))

    matrix_config = dict(request.matrix or {})
    families = matrix_config.get("families", VALID_TRANSITION_MATRIX_FAMILIES)
    transition_styles = matrix_config.get("transitionStyles", VALID_TRANSITION_STYLES)

    families = [f for f in families if f in VALID_TRANSITION_MATRIX_FAMILIES]
    transition_styles = [ts for ts in transition_styles if ts in VALID_TRANSITION_STYLES]

    # V1.2.4: Reject invalid / over-limit requests with clear error messages
    if not families:
        raise ValueError(
            f"families filter resulted in empty set. "
            f"Allowed values: {VALID_TRANSITION_MATRIX_FAMILIES}"
        )
    if not transition_styles:
        raise ValueError(
            f"transitionStyles filter resulted in empty set. "
            f"Allowed values: {VALID_TRANSITION_STYLES}"
        )
    total = len(families) * len(transition_styles)
    if total > MAX_MATRIX_ITEMS:
        raise ValueError(
            f"transition matrix is limited to {MAX_MATRIX_ITEMS} clips per request, "
            f"but {total} requested ({len(families)} families × {len(transition_styles)} transitions). "
            f"Reduce families or transitions."
        )

    items: list[dict[str, Any]] = []

    for family_id in families:
        for transition_style in transition_styles:
            family_params = {
                **params,
                "remotionFamily": family_id,
                "keyPointCount": key_point_count,
                "transitionStyle": transition_style,
            }
            result = render_clip_preview(
                content=content,
                visual_route="template_programmatic_render",
                params=family_params,
                clip_seconds=clip_seconds,
            )
            items.append({
                "family": family_id,
                "transitionStyle": transition_style,
                "success": result.get("success", False),
                "videoUrl": result.get("clipUrl", ""),
                "experimentId": result.get("experimentId", ""),
                "clipSeconds": result.get("clipSeconds", clip_seconds),
                "elapsedMs": result.get("elapsedMs", 0),
                "message": result.get("message", ""),
                "warnings": result.get("warnings", []),
            })

    elapsed = int((time.time() - t0) * 1000)

    return {
        "items": items,
        "totalElapsedMs": elapsed,
    }


def run_visual_style_matrix(request) -> dict[str, Any]:
    """
    V1.2.4: Visual Style Preset Matrix — family × visualStylePreset clips.

    Lab-only: does NOT write Style Sweep job, Style Gallery sample, or promote.
    All clips are temporary lab assets.

    Args:
        request: VisualStyleMatrixRequest object

    Returns:
        {
            "items": [
                {
                    "family": "data_news",
                    "visualStylePreset": "light_editorial",
                    "success": true,
                    "videoUrl": "/runtime/video_lab/experiments/clip_xxx/clip.mp4",
                    "experimentId": "...",
                    "clipSeconds": 2,
                    "elapsedMs": 12345,
                    "message": "",
                    "warnings": []
                },
                ...
            ],
            "totalElapsedMs": 123456
        }
    """
    t0 = time.time()

    content = request.content.strip() or STYLE_FAMILY_DEFAULT_CONTENT
    params = dict(request.params or {})
    params["visualRoute"] = "template_programmatic_render"
    clip_seconds = int(params.get("clipSeconds", 3))
    key_point_count = int(params.get("keyPointCount", 3))

    matrix_config = dict(request.matrix or {})
    families = matrix_config.get("families", VALID_VISUAL_STYLE_MATRIX_FAMILIES)
    visual_style_presets = matrix_config.get("visualStylePresets", VALID_VISUAL_STYLE_PRESETS)

    # Filter to valid entries only
    families = [f for f in families if f in VALID_VISUAL_STYLE_MATRIX_FAMILIES]
    visual_style_presets = [p for p in visual_style_presets if p in VALID_VISUAL_STYLE_PRESETS]

    # V1.2.4: Reject invalid / over-limit requests with clear error messages
    if not families:
        raise ValueError(
            f"families filter resulted in empty set. "
            f"Allowed values: {VALID_VISUAL_STYLE_MATRIX_FAMILIES}"
        )
    if not visual_style_presets:
        raise ValueError(
            f"visualStylePresets filter resulted in empty set. "
            f"Allowed values: {VALID_VISUAL_STYLE_PRESETS}"
        )
    total = len(families) * len(visual_style_presets)
    if total > MAX_MATRIX_ITEMS:
        raise ValueError(
            f"visual style matrix is limited to {MAX_MATRIX_ITEMS} clips per request, "
            f"but {total} requested ({len(families)} families × {len(visual_style_presets)} presets). "
            f"Reduce families or presets."
        )

    items: list[dict[str, Any]] = []

    for family_id in families:
        for preset in visual_style_presets:
            family_params = {
                **params,
                "remotionFamily": family_id,
                "keyPointCount": key_point_count,
                "visualStylePreset": preset,
            }
            result = render_clip_preview(
                content=content,
                visual_route="template_programmatic_render",
                params=family_params,
                clip_seconds=clip_seconds,
            )
            items.append({
                "family": family_id,
                "visualStylePreset": preset,
                "success": result.get("success", False),
                "videoUrl": result.get("clipUrl", ""),
                "experimentId": result.get("experimentId", ""),
                "clipSeconds": result.get("clipSeconds", clip_seconds),
                "elapsedMs": result.get("elapsedMs", 0),
                "message": result.get("message", ""),
                "warnings": result.get("warnings", []),
            })

    elapsed = int((time.time() - t0) * 1000)

    return {
        "items": items,
        "totalElapsedMs": elapsed,
    }


# V1.2.4: Visual Technique Matrix
VALID_VISUAL_TECHNIQUE_MATRIX_FAMILIES = [
    "caption_story",
    "data_news",
    "timeline_news",
]

VALID_VISUAL_TECHNIQUES = [
    "academic_sketch",
    "blueprint",
]


def run_visual_technique_matrix(request) -> dict[str, Any]:
    """
    V1.2.4: Visual Technique Matrix — family × visualTechnique clips.

    First technique: academic_sketch — paper-like background, grid lines, hand-drawn annotations.

    Lab-only: does NOT write Style Sweep job, Style Gallery sample, or promote.
    All clips are temporary lab assets.
    """
    t0 = time.time()

    content = request.content.strip() or STYLE_FAMILY_DEFAULT_CONTENT
    params = dict(request.params or {})
    params["visualRoute"] = "template_programmatic_render"
    clip_seconds = int(params.get("clipSeconds", 2))
    key_point_count = int(params.get("keyPointCount", 2))

    # Inject defaults when not explicitly set
    if "visualStylePreset" not in params:
        params["visualStylePreset"] = "warm_paper"
    if "backgroundPreset" not in params:
        params["backgroundPreset"] = "warm_cinematic"
    if "transitionStyle" not in params:
        params["transitionStyle"] = "slide_fade"

    matrix_config = dict(request.matrix or {})
    families = matrix_config.get("families", VALID_VISUAL_TECHNIQUE_MATRIX_FAMILIES)
    visual_techniques = matrix_config.get("visualTechniques", VALID_VISUAL_TECHNIQUES)

    families = [f for f in families if f in VALID_VISUAL_TECHNIQUE_MATRIX_FAMILIES]
    visual_techniques = [vt for vt in visual_techniques if vt in VALID_VISUAL_TECHNIQUES]

    if not families:
        raise ValueError(
            f"families filter resulted in empty set. "
            f"Allowed values: {VALID_VISUAL_TECHNIQUE_MATRIX_FAMILIES}"
        )
    if not visual_techniques:
        raise ValueError(
            f"visualTechniques filter resulted in empty set. "
            f"Allowed values: {VALID_VISUAL_TECHNIQUES}"
        )
    total = len(families) * len(visual_techniques)
    if total > MAX_MATRIX_ITEMS:
        raise ValueError(
            f"visual technique matrix is limited to {MAX_MATRIX_ITEMS} clips per request, "
            f"but {total} requested ({len(families)} families × {len(visual_techniques)} techniques). "
            f"Reduce families or techniques."
        )

    items: list[dict[str, Any]] = []

    for family_id in families:
        for vt in visual_techniques:
            family_params = {
                **params,
                "remotionFamily": family_id,
                "keyPointCount": key_point_count,
                "visualTechnique": vt,
            }
            result = render_clip_preview(
                content=content,
                visual_route="template_programmatic_render",
                params=family_params,
                clip_seconds=clip_seconds,
            )
            items.append({
                "family": family_id,
                "visualTechnique": vt,
                "success": result.get("success", False),
                "videoUrl": result.get("clipUrl", ""),
                "experimentId": result.get("experimentId", ""),
                "clipSeconds": result.get("clipSeconds", clip_seconds),
                "elapsedMs": result.get("elapsedMs", 0),
                "message": result.get("message", ""),
                "warnings": result.get("warnings", []),
            })

    elapsed = int((time.time() - t0) * 1000)

    return {
        "items": items,
        "totalElapsedMs": elapsed,
    }
