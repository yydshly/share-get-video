"""
app/video_lab/style_gallery/replay.py
V1.0.6: Style Sample Replay — construct rerun payloads from StyleSample records.

Does NOT execute generation; only derives payload structure.
"""

from typing import Any

from app.video_lab.style_gallery.models import StyleSample


def _content_from_sample(sample: StyleSample) -> tuple[str, list[str]]:
    """Derive content string from sample, with warnings for incomplete data."""
    params = dict(sample.params or {})
    warnings: list[str] = []

    content = (
        str(params.get("fullContent") or "").strip()
        or str(params.get("content") or "").strip()
        or sample.content_preview.strip()
    )

    if not content:
        warnings.append("No content found; rerun payload is incomplete.")
    elif content == sample.content_preview and sample.content_preview and len(sample.content_preview) < len(content or ""):
        # content_preview is a truncated version of content — warn
        pass
    elif content == sample.content_preview and sample.content_preview:
        warnings.append("Only content_preview is available; rerun may not match original full content.")

    return content, warnings


def _params_from_sample(sample: StyleSample) -> dict[str, Any]:
    """Derive params dict from sample, enriching from generation metadata."""
    params = dict(sample.params or {})
    gen = sample.generation

    if gen.visual_route and "visualRoute" not in params:
        params["visualRoute"] = gen.visual_route

    if gen.visual_profile and "visualProfile" not in params:
        params["visualProfile"] = gen.visual_profile

    if gen.remotion_family and "remotionFamily" not in params:
        params["remotionFamily"] = gen.remotion_family

    if gen.aspect_ratio and "aspectRatio" not in params:
        params["aspectRatio"] = gen.aspect_ratio

    if gen.target_duration and "targetDuration" not in params:
        params["targetDuration"] = gen.target_duration

    if gen.key_point_count and "keyPointCount" not in params:
        params["keyPointCount"] = gen.key_point_count

    return params


def build_visual_compose_payload(sample: StyleSample) -> dict[str, Any]:
    """Build POST /visual-compose payload from a StyleSample record."""
    content, _ = _content_from_sample(sample)
    params = _params_from_sample(sample)
    visual_route = (
        sample.generation.visual_route.strip()
        or sample.route_id
    )
    return {
        "content": content,
        "visualRoute": visual_route,
        "params": params,
    }


def build_clip_preview_payload(sample: StyleSample) -> dict[str, Any]:
    """Build POST /clip-preview payload from a StyleSample record."""
    content, _ = _content_from_sample(sample)
    params = _params_from_sample(sample)
    visual_route = (
        sample.generation.visual_route.strip()
        or sample.route_id
    )

    # clip-preview specific overrides
    clip_params = dict(params)
    clip_params.setdefault("clipSeconds", 3)

    cover_title = (
        str(sample.params.get("coverTitle", "")).strip()
        if sample.params else ""
    ) or sample.style_name

    return {
        "visualRoute": visual_route,
        "content": content,
        "shot": {},
        "frameType": "keypoint",
        "coverTitle": cover_title,
        "params": clip_params,
    }


def assess_reproducibility(sample: StyleSample) -> tuple[bool, list[str]]:
    """Assess whether a StyleSample can be reliably reproduced.

    Returns (reproducible: bool, warnings: list[str]).
    A sample is reproducible if we have enough content and route info.
    """
    warnings: list[str] = []

    # Check route
    has_route = bool(
        sample.generation.visual_route.strip()
        or sample.route_id
    )
    if not has_route:
        warnings.append("No visual_route or route_id found; cannot determine generation route.")

    # Check content
    content, content_warnings = _content_from_sample(sample)
    warnings.extend(content_warnings)

    if not content:
        return False, warnings

    if not has_route:
        return False, warnings

    return True, warnings


def build_rerun_payload(sample: StyleSample) -> dict[str, Any]:
    """Build the full V1.0.6 rerun payload from a StyleSample.

    Does NOT execute generation — only constructs the payload.
    """
    reproducible, warnings = assess_reproducibility(sample)

    return {
        "sampleId": sample.id,
        "schemaVersion": "1.0.6",
        "reproducible": reproducible,
        "warnings": warnings,
        "source": sample.source.model_dump(mode="json"),
        "generation": sample.generation.model_dump(mode="json"),
        "assetMeta": sample.asset_meta.model_dump(mode="json"),
        "qualityMeta": sample.quality_meta.model_dump(mode="json"),
        "reviewMeta": sample.review_meta.model_dump(mode="json"),
        "jobRun": sample.job_run,
        "visualComposePayload": build_visual_compose_payload(sample),
        "clipPreviewPayload": build_clip_preview_payload(sample),
    }
