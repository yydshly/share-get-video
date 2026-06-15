"""
technique_probe —— 最佳技术探测编排

一份内容 → 在多条视觉路线上各出整片 → 按统一质量分排名 → 给出推荐路线。

为可测试，重活（单路线端到端出片）通过 compose_fn 注入：
- 生产环境由 router 传入真实的 _run_visual_compose（跑 TTS+渲染+合成+打分）
- 测试用桩函数返回预设结果，不触发任何真实渲染
"""

from typing import Any, Callable

# 探测默认覆盖的三条已落地视觉路线
DEFAULT_PROBE_ROUTES = [
    "local_frame_compose",
    "template_programmatic_render",
    "ai_asset_then_compose",
]

# 路线展示名（给 UI 用，避免前端散落硬编码）
ROUTE_DISPLAY_NAMES = {
    "local_frame_compose": "Pillow 静态卡",
    "template_programmatic_render": "Remotion 动效",
    "ai_asset_then_compose": "AI 素材 + 合成",
}


def _score_of(result: dict) -> float:
    """取一次出片的总质量分；未成功记 -1，确保排到末尾。"""
    if result.get("status") != "succeeded":
        return -1.0
    quality = result.get("quality") or {}
    try:
        return float(quality.get("overallScore") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def rank_probe_results(results: list[dict]) -> list[dict]:
    """按总质量分降序排名；失败路线排末尾。返回供 UI 直接渲染的精简条目。"""
    ordered = sorted(results, key=_score_of, reverse=True)
    ranked: list[dict] = []
    for i, r in enumerate(ordered, 1):
        s = _score_of(r)
        route = r.get("visualRoute", "")
        ranked.append({
            "rank": i,
            "visualRoute": route,
            "displayName": ROUTE_DISPLAY_NAMES.get(route, route),
            "status": r.get("status", "unknown"),
            "score": s if s >= 0 else None,
            "finalVideoUrl": r.get("finalVideoUrl", ""),
            "coverUrl": r.get("coverUrl", ""),
            "failedReason": r.get("failedReason", ""),
        })
    return ranked


def run_technique_probe(
    content: str,
    routes: list[str] | None,
    params: dict[str, Any] | None,
    compose_fn: Callable[[str, str, dict], dict],
) -> dict[str, Any]:
    """对每条路线各出一片 → 排名 → 推荐。compose_fn(content, route, params)->result dict。"""
    routes = routes or DEFAULT_PROBE_ROUTES
    params = params or {}

    results: list[dict] = []
    for route in routes:
        try:
            results.append(compose_fn(content, route, params))
        except Exception as e:  # 单路线异常不应中断整个探测
            results.append({
                "visualRoute": route,
                "status": "failed",
                "failedReason": f"compose error: {e}",
                "quality": {},
            })

    ranking = rank_probe_results(results)
    succeeded = [r for r in ranking if r["status"] == "succeeded"]
    recommended = succeeded[0]["visualRoute"] if succeeded else None

    return {
        "routesRun": routes,
        "ranking": ranking,
        "results": results,
        "recommendedRoute": recommended,
        "recommendedDisplayName": ROUTE_DISPLAY_NAMES.get(recommended, recommended) if recommended else None,
        "succeededCount": len(succeeded),
        "totalCount": len(routes),
    }
