"""
Style Family Service — extracted from router.py V1.0.2.

Provides run_style_family_compare() for /style-family/compare endpoint.
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
