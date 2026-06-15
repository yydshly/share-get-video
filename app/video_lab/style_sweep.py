"""
style_sweep —— 同一路线的样式对比编排

选定一条技术路线 → 用同一份内容把它的每个预置样式各出一片 → 并排返回，
让用户看清"同一技术、不同样式"的生成效果差异（项目目标②）。

为可测试，重活（单样式端到端出片）通过 render_fn 注入：
- 生产环境由 router 传入真实的 _run_visual_compose
- 测试用桩函数返回预设结果，不触发任何真实渲染
预置样式默认取自 style_gallery.presets，也可注入以便测试。
"""

from typing import Any, Callable

from app.video_lab.style_gallery.presets import list_preset_styles


def styles_for_route(route_id: str, styles: list[dict] | None = None) -> list[dict]:
    """取某路线的全部预置样式。styles 留空则取全局预置表。"""
    src = styles if styles is not None else list_preset_styles()
    return [s for s in src if s.get("route_id") == route_id]


def run_style_sweep(
    content: str,
    route_id: str,
    params: dict[str, Any] | None,
    render_fn: Callable[[str, str, dict], dict],
    styles: list[dict] | None = None,
) -> dict[str, Any]:
    """对某路线每个预置样式各出一片（同内容），返回逐样式结果供并排对比。

    render_fn(content, route_id, merged_params) -> result dict（含 finalVideoUrl/quality/...）。
    样式自带的 params 覆盖在传入 params 之上（样式即一组参数）。
    """
    params = params or {}
    route_styles = styles_for_route(route_id, styles)

    results: list[dict] = []
    for st in route_styles:
        merged = {**params, **(st.get("params") or {})}
        try:
            r = render_fn(content, route_id, merged)
        except Exception as e:  # 单样式异常不应中断整批
            r = {
                "visualRoute": route_id,
                "status": "failed",
                "failedReason": f"render error: {e}",
                "quality": {},
            }
        results.append({
            "styleId": st.get("style_id", ""),
            "styleName": st.get("style_name", ""),
            "description": st.get("description", ""),
            "tags": st.get("tags", []),
            "result": r,
        })

    succeeded = sum(1 for x in results if x["result"].get("status") == "succeeded")
    return {
        "routeId": route_id,
        "routeName": route_styles[0].get("route_name", route_id) if route_styles else route_id,
        "styleCount": len(route_styles),
        "succeededCount": succeeded,
        "results": results,
    }
