"""Pluggable visual renderers - 可插拔视觉渲染层。"""

from app.video_lab.renderers.visual.base import (
    VisualRenderer,
    VisualRenderRequest,
    VisualRenderResult,
)
from app.video_lab.renderers.visual.registry import (
    get_visual_renderer,
    list_visual_renderers,
    resolve_visual_route,
    DEFAULT_VISUAL_ROUTE,
)

__all__ = [
    "VisualRenderer",
    "VisualRenderRequest",
    "VisualRenderResult",
    "get_visual_renderer",
    "list_visual_renderers",
    "resolve_visual_route",
    "DEFAULT_VISUAL_ROUTE",
]
