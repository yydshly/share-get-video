"""
Routes Benchmark - Route Registry
V0.3.0: Defines all available routes and their implementation status
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class RouteDefinition:
    """Definition of a single route."""
    route_id: str
    name: str
    status: str  # "real" | "mock" | "reserved"
    description: str
    expected_pipeline: list[str]
    adapter_category: str | None = None  # maps to MethodCategory if applicable


# All registered routes
ROUTE_REGISTRY: list[RouteDefinition] = [
    RouteDefinition(
        route_id="local_frame_compose",
        name="本地图像帧合成",
        status="real",
        description="使用 Pillow 生成信息卡片帧，FFmpeg 合成视频。成本低、可控性高、稳定性高。",
        expected_pipeline=[
            "接收输入",
            "结构化内容",
            "提取关键点",
            "视频策略",
            "选择方法",
            "生成脚本",
            "生成分镜",
            "字幕计划",
            "资产计划",
            "Pillow 生成 PNG 帧",
            "FFmpeg 合成 MP4",
            "生成结论",
        ],
        adapter_category="local_frame_compose",
    ),
    RouteDefinition(
        route_id="template_programmatic_render",
        name="Remotion 程序化渲染",
        status="real",
        description="Remotion / React 程序化模板渲染，真实生成 MP4，用于验证动态模板路线。需 Node.js + Remotion 环境。",
        expected_pipeline=[
            "接收输入",
            "结构化内容",
            "提取关键点",
            "构建 Remotion Props",
            "npx remotion render",
            "生成 manifest",
            "输出 MP4",
        ],
        adapter_category="template_programmatic_render",
    ),
    RouteDefinition(
        route_id="tts_subtitle_compose",
        name="TTS + 字幕合成",
        status="mock",
        description="TTS 语音 + 字幕压制。需要 TTS API（如 ElevenLabs）和字幕时间轴。",
        expected_pipeline=[
            "接收输入",
            "LLM 生成脚本",
            "TTS 语音生成",
            "字幕时间轴",
            "画面渲染",
            "字幕压制",
            "FFmpeg 合成",
        ],
        adapter_category=None,
    ),
    RouteDefinition(
        route_id="ai_asset_then_compose",
        name="AI 素材 + 本地合成",
        status="mock",
        description="LLM 生成脚本和旁白，TTS 生成语音，图像模型生成素材，FFmpeg 最终合成。",
        expected_pipeline=[
            "接收输入",
            "LLM 脚本生成",
            "TTS 旁白生成",
            "图像生成封面/背景",
            "本地帧渲染",
            "音频合成",
            "FFmpeg 最终合成",
        ],
        adapter_category="ai_asset_then_compose",
    ),
    RouteDefinition(
        route_id="ai_video_direct",
        name="大模型直接生成视频",
        status="reserved",
        description="文生视频 / 图生视频。信息准确性低、字幕不可控、成本极高。",
        expected_pipeline=[
            "接收输入",
            "压缩为视频 Prompt",
            "调用视频生成模型",
            "风险评估",
        ],
        adapter_category="ai_video_direct",
    ),
    RouteDefinition(
        route_id="hybrid_pipeline",
        name="混合编排流水线",
        status="reserved",
        description="按场景自动选择最优路径组合。需要完整路由引擎。",
        expected_pipeline=[
            "场景判断",
            "路径选择",
            "多步执行",
            "质量评估",
            "FFmpeg 合成",
        ],
        adapter_category="hybrid_pipeline",
    ),
]


def get_route_by_id(route_id: str) -> RouteDefinition | None:
    """Get route definition by ID."""
    for route in ROUTE_REGISTRY:
        if route.route_id == route_id:
            return route
    return None


def list_routes() -> list[dict]:
    """List all registered routes as dicts."""
    return [
        {
            "routeId": r.route_id,
            "name": r.name,
            "status": r.status,
            "description": r.description,
            "expectedPipeline": r.expected_pipeline,
        }
        for r in ROUTE_REGISTRY
    ]


def get_routes_by_ids(route_ids: list[str]) -> list[RouteDefinition]:
    """Get multiple routes by IDs. Returns only found ones."""
    return [r for r in ROUTE_REGISTRY if r.route_id in route_ids]
