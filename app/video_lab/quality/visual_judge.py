"""
Visual Judge - 视觉模型评委（感知质量）

把渲染出的画面交给多模态大模型打分，补齐确定性质量层测不了的"好不好看"：
排版、可读性、信息层级、美观度。返回 1-5 分 + 改进建议。

与 video_quality.py（结构层，确定性）互补：这里是感知层，主观维度自动化。
"""

from __future__ import annotations

from typing import Any

from app.video_lab.providers.minimax import MiniMaxChatClient


_SINGLE_PROMPT = (
    "你是专业的竖屏短视频画面质量评审。只依据这张画面本身评估，按以下维度各打 1-5 分（5 最好）：\n"
    "- layout: 排版与留白是否合理、平衡\n"
    "- readability: 文字是否清晰可读、对比度是否足够、有无截断/溢出\n"
    "- hierarchy: 标题/正文/重点的信息层级是否清晰\n"
    "- aesthetics: 整体美观度与专业感\n"
    "再给 overall(1-5 综合) 和最多 3 条**具体可执行**的改进建议（中文，针对这张画面）。\n"
    "严格输出 JSON，不要任何解释或代码块：\n"
    '{"layout":n,"readability":n,"hierarchy":n,"aesthetics":n,"overall":n,"suggestions":["...","..."]}'
)

_MULTI_PROMPT = (
    "你是专业的竖屏短视频画面质量评审。以下是**同一支短视频**按时间顺序抽取的若干关键画面"
    "（封面/关键点卡/结尾）。请综合整支视频评估，按以下维度各打 1-5 分（5 最好）：\n"
    "- layout: 排版与留白是否合理、平衡\n"
    "- readability: 文字是否清晰可读、对比度是否足够、有无截断/溢出\n"
    "- hierarchy: 信息层级是否清晰\n"
    "- aesthetics: 整体美观度与专业感\n"
    "- consistency: 多个画面之间风格/配色/排版是否统一一致\n"
    "再给 overall(1-5 综合) 和最多 3 条**具体可执行**的改进建议（中文）。\n"
    "严格输出 JSON，不要任何解释或代码块：\n"
    '{"layout":n,"readability":n,"hierarchy":n,"aesthetics":n,"consistency":n,"overall":n,"suggestions":["...","..."]}'
)


def assess_visual_quality(image_paths: "str | list[str]") -> dict[str, Any]:
    """对一张或多张画面做感知质量评审。多张时综合评估并增加 consistency 维度。

    返回 {success, scores, overall, suggestions, frameCount, ...}。
    """
    if isinstance(image_paths, str):
        image_paths = [image_paths]
    image_paths = [p for p in image_paths if p]
    if not image_paths:
        return {"success": False, "message": "no image provided"}

    client = MiniMaxChatClient()
    if not client.is_configured():
        return {"success": False, "message": "MINIMAX_API_KEY not configured"}

    multi = len(image_paths) > 1
    prompt = _MULTI_PROMPT if multi else _SINGLE_PROMPT
    dims = ("layout", "readability", "hierarchy", "aesthetics") + (("consistency",) if multi else ())

    result = client.chat_vision_json(prompt, image_paths, temperature=0.2, max_tokens=1400)
    if not result.get("success"):
        return {"success": False, "message": result.get("providerMessage", "vision judge failed")}

    data = result.get("json") or {}
    scores: dict[str, float] = {}
    for d in dims:
        try:
            scores[d] = float(data.get(d))
        except (TypeError, ValueError):
            scores[d] = 0.0
    try:
        overall = float(data.get("overall"))
    except (TypeError, ValueError):
        overall = round(sum(scores.values()) / len(scores), 2) if scores else 0.0

    suggestions = data.get("suggestions") or []
    if isinstance(suggestions, str):
        suggestions = [suggestions]
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()][:3]

    return {
        "success": True,
        "scores": scores,
        "overall": overall,
        "suggestions": suggestions,
        "frameCount": len(image_paths),
        "judge": "minimax-vision",
    }
