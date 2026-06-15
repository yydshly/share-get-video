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


# 结构分(确定性)在总分里的权重；其余给视觉感知分。
# 结构分容易顶到满分、区分度低，所以让视觉分占一半来拉开差距。
STRUCTURAL_WEIGHT = 0.5
VISUAL_WEIGHT = 0.5


def _structural_score(result: dict) -> float:
    """结构分(0-5)；未成功记 -1。"""
    if result.get("status") != "succeeded":
        return -1.0
    quality = result.get("quality") or {}
    try:
        return float(quality.get("overallScore") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _visual_score(result: dict) -> float | None:
    """视觉感知分(0-100)；缺失返回 None。"""
    v = result.get("visualScore")
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _combined_score(result: dict) -> float:
    """综合分(0-100)：结构分×20 归一后与视觉分加权；失败记 -1 排末尾。

    有视觉分 → 加权；无视觉分 → 退化为纯结构分(0-100)，保证仍可排名。
    """
    st = _structural_score(result)
    if st < 0:
        return -1.0
    st100 = st * 20.0
    vis = _visual_score(result)
    if vis is None:
        return round(st100, 2)
    return round(STRUCTURAL_WEIGHT * st100 + VISUAL_WEIGHT * vis, 2)


def rank_probe_results(results: list[dict]) -> list[dict]:
    """按综合分降序排名；失败路线排末尾。返回供 UI 直接渲染的精简条目。"""
    ordered = sorted(results, key=_combined_score, reverse=True)
    ranked: list[dict] = []
    for i, r in enumerate(ordered, 1):
        st = _structural_score(r)
        combined = _combined_score(r)
        route = r.get("visualRoute", "")
        ranked.append({
            "rank": i,
            "visualRoute": route,
            "displayName": ROUTE_DISPLAY_NAMES.get(route, route),
            "status": r.get("status", "unknown"),
            "score": st if st >= 0 else None,            # 结构分(0-5)，UI 既有展示
            "visualScore": _visual_score(r),             # 视觉感知分(0-100) 或 None
            "combinedScore": combined if combined >= 0 else None,  # 综合分(0-100)
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
    judge_fn: Callable[[dict], dict | None] | None = None,
) -> dict[str, Any]:
    """对每条路线各出一片 → (可选)视觉评分 → 排名 → 推荐。

    compose_fn(content, route, params) -> result dict（含 finalVideoUrl/quality/...）。
    judge_fn(result) -> {"visualScore": 0-100, "visualDimensions": {...}} 或 None；
        传入则对成功出片做视觉感知评分并并入综合分（让排名有区分度、推荐可信）。
    """
    routes = routes or DEFAULT_PROBE_ROUTES
    params = params or {}

    results: list[dict] = []
    for route in routes:
        try:
            result = compose_fn(content, route, params)
        except Exception as e:  # 单路线异常不应中断整个探测
            result = {
                "visualRoute": route,
                "status": "failed",
                "failedReason": f"compose error: {e}",
                "quality": {},
            }
        # 视觉感知评分（仅对成功出片；评分失败不影响该路线仍按结构分排名）
        if judge_fn and result.get("status") == "succeeded":
            try:
                judged = judge_fn(result)
                if judged:
                    result["visualScore"] = judged.get("visualScore")
                    result["visualDimensions"] = judged.get("visualDimensions", {})
            except Exception:
                pass
        results.append(result)

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
