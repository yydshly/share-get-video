"""
Visual Renderer Registry - 视觉路线注册表

新增一种"生成视频的方式"时：实现 VisualRenderer → 在此注册一个实例。
链路通过 visual_route（与 ChainDefinition.visual_route 对齐）选择渲染器。
"""

from app.video_lab.renderers.visual.base import VisualRenderer
from app.video_lab.renderers.visual.pillow_renderer import PillowVisualRenderer
from app.video_lab.renderers.visual.remotion_renderer import RemotionVisualRenderer
from app.video_lab.renderers.visual.ai_asset_renderer import AiAssetVisualRenderer


_VISUAL_RENDERERS: dict[str, VisualRenderer] = {
    PillowVisualRenderer.route_id: PillowVisualRenderer(),
    RemotionVisualRenderer.route_id: RemotionVisualRenderer(),
    AiAssetVisualRenderer.route_id: AiAssetVisualRenderer(),
}

# 默认视觉路线（保持现有链路行为）
DEFAULT_VISUAL_ROUTE = PillowVisualRenderer.route_id


def get_visual_renderer(route_id: str) -> VisualRenderer | None:
    """按 route_id 获取视觉渲染器；未知返回 None。"""
    return _VISUAL_RENDERERS.get(route_id)


def list_visual_renderers() -> list[dict]:
    """列出所有已注册视觉路线及其可用性，用于前端展示/对比。"""
    out = []
    for route_id, renderer in _VISUAL_RENDERERS.items():
        available, msg = renderer.is_available()
        out.append({
            "routeId": route_id,
            "displayName": renderer.display_name,
            "available": available,
            "availabilityMessage": msg,
        })
    return out


def resolve_visual_route(params: dict | None) -> str:
    """从参数解析 visualRoute，未指定/未知则回退默认路线。"""
    if not params:
        return DEFAULT_VISUAL_ROUTE
    route = params.get("visualRoute") or params.get("visual_route")
    if route and route in _VISUAL_RENDERERS:
        return route
    return DEFAULT_VISUAL_ROUTE
