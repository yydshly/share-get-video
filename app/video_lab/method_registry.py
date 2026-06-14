"""
Video Capability Lab - Method Registry
方法路由注册表，将 method category 映射到具体 adapter
"""

from typing import Callable, Optional
from app.video_lab.models import MethodCategory
from app.video_lab.adapters import (
    local_frame_compose,
    local_media_compose,
    remotion_template,
    ai_video_direct,
    ai_asset_then_compose,
    hybrid_pipeline,
    tts_subtitle_compose,
    hyperframes_html_render,
)


# Adapter registry: category -> function
_METHOD_ADAPTERS: dict[str, Callable] = {
    MethodCategory.LOCAL_FRAME_COMPOSE.value: local_frame_compose.run_local_frame_compose,
    MethodCategory.LOCAL_MEDIA_COMPOSE.value: local_media_compose.run_local_media_compose,
    MethodCategory.TEMPLATE_PROGRAMMATIC_RENDER.value: remotion_template.run_remotion_template,
    MethodCategory.TTS_SUBTITLE_COMPOSE.value: tts_subtitle_compose.run_tts_subtitle_compose,
    MethodCategory.HYPERFRAMES_HTML_RENDER.value: hyperframes_html_render.run_hyperframes_html_render,
    MethodCategory.AI_VIDEO_DIRECT.value: ai_video_direct.run_ai_video_direct,
    MethodCategory.AI_ASSET_THEN_COMPOSE.value: ai_asset_then_compose.run_ai_asset_then_compose,
    MethodCategory.HYBRID_PIPELINE.value: hybrid_pipeline.run_hybrid_pipeline,
}


def get_adapter_for_category(category: MethodCategory) -> Optional[Callable]:
    """根据 method category 获取对应的 adapter 函数"""
    return _METHOD_ADAPTERS.get(category.value)


def list_registered_categories() -> list[str]:
    """返回所有已注册的方法类别"""
    return list(_METHOD_ADAPTERS.keys())


def is_category_registered(category: MethodCategory) -> bool:
    """检查某个 category 是否已注册 adapter"""
    return category.value in _METHOD_ADAPTERS
