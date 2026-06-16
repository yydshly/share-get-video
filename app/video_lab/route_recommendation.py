"""
route_recommendation —— 数据驱动的"最佳路线"推荐

不再写死推荐，而是读取 quality_log 里**真实累计的评分**（每次出片/评分都会记一条），
按综合分给出推荐 + 证据。数据不足时如实说明，绝不编造结论。

核心函数 recommend_route_from_summary(summary) 是纯函数（summary 可注入，便于测试）。
"""

from typing import Any

from app.video_lab.technique_probe import ROUTE_DISPLAY_NAMES

# 样本数达到该阈值才算"有把握"，否则给出但标注待巩固
MIN_SAMPLES_FOR_CONFIDENCE = 3


def _to_100(v: Any) -> float | None:
    """把 0-5 量纲的分数归一到 0-100；已是 0-100 则原样。无效返回 None。"""
    if not isinstance(v, (int, float)):
        return None
    return float(v) * 20.0 if v <= 5 else float(v)


def _route_combined(kinds: dict) -> float | None:
    """从某路线的 summary（structural/perceptual 各自 latest）算综合分(0-100)。

    有结构分+视觉分则各占一半；只有一种则用那一种；都没有返回 None。
    """
    structural = _to_100((kinds.get("structural") or {}).get("latest"))
    perceptual = _to_100((kinds.get("perceptual") or {}).get("latest"))
    parts = [p for p in (structural, perceptual) if p is not None]
    if not parts:
        return None
    return round(sum(parts) / len(parts), 2)


def recommend_route_from_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """从 quality_log.summarize_by_route() 的结果算出数据驱动推荐。"""
    ranked: list[dict] = []
    for route, kinds in (summary or {}).items():
        score = _route_combined(kinds)
        if score is None:
            continue
        samples = max((kinds.get(k, {}).get("count", 0) for k in kinds), default=0)
        ranked.append({
            "route": route,
            "displayName": ROUTE_DISPLAY_NAMES.get(route, route),
            "score": score,
            "samples": samples,
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    if not ranked:
        return {
            "dataDriven": False,
            "recommendedRoute": None,
            "recommendedDisplayName": None,
            "confident": False,
            "reason": "暂无评分数据——先到「技术探测台」或「视频生成对比」跑几次出片，系统会按真实评分给出推荐。",
            "ranking": [],
        }

    top = ranked[0]
    confident = top["samples"] >= MIN_SAMPLES_FOR_CONFIDENCE
    reason = f"基于真实评分：{top['displayName']} 综合分最高（{top['score']}，{top['samples']} 次样本）"
    if not confident:
        reason += "；样本较少，结论待更多数据巩固"

    return {
        "dataDriven": True,
        "recommendedRoute": top["route"],
        "recommendedDisplayName": top["displayName"],
        "confident": confident,
        "reason": reason,
        "ranking": ranked,
    }


def recommend_route() -> dict[str, Any]:
    """读取真实累计评分并给出推荐（生产入口）。"""
    from app.video_lab.quality.quality_log import summarize_by_route
    return recommend_route_from_summary(summarize_by_route())
