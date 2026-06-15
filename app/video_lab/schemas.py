"""
Video Capability Lab - Request/Response Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any


class CreateExperimentRequest(BaseModel):
    """JSON body for POST /video-lab/experiments"""

    testCaseId: str = Field(..., min_length=1, description="ID of the test case to run")
    methodId: str = Field(..., min_length=1, description="ID of the generation method to use")
    title: str = Field(..., min_length=1, description="Human-readable title for this experiment")
    inputPayload: dict[str, Any] = Field(
        default_factory=dict,
        description="Input payload passed to the adapter (e.g. {\"content\": \"...\"})",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters (e.g. targetDuration, aspectRatio)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "testCaseId": "case_ai_frontier_daily_001",
                "methodId": "method_local_frame_compose",
                "title": "AI frontier daily test",
                "inputPayload": {"content": "今日 AI 前沿测试内容"},
                "params": {"targetDuration": 45, "aspectRatio": "9:16"},
            }
        }
    }


class SaveEvaluationRequest(BaseModel):
    """JSON body for POST /video-lab/experiments/{id}/evaluation"""

    informationAccuracy: int = Field(..., ge=1, le=5, description="信息准确性 1-5")
    readability: int = Field(..., ge=1, le=5, description="可读性 1-5")
    visualQuality: int = Field(..., ge=1, le=5, description="视觉质量 1-5")
    pacing: int = Field(..., ge=1, le=5, description="节奏 1-5")
    shareability: int = Field(..., ge=1, le=5, description="分享价值 1-5")
    stability: int = Field(..., ge=1, le=5, description="稳定性 1-5")
    productizationValue: int = Field(..., ge=1, le=5, description="产品化价值 1-5")
    notes: str = Field(default="", description="用户备注")


class CreateBenchmarkRequest(BaseModel):
    """JSON body for POST /video-lab/route-benchmarks"""

    testCaseId: str = Field(..., min_length=1, description="ID of the test case")
    title: str = Field(..., min_length=1, description="Human-readable title for this benchmark")
    inputPayload: dict[str, Any] = Field(
        default_factory=dict,
        description="Input payload passed to all routes",
    )
    commonParams: dict[str, Any] = Field(
        default_factory=dict,
        description="Common parameters for all routes (e.g. targetDuration, aspectRatio)",
    )
    routeIds: list[str] = Field(
        ...,
        min_length=1,
        description="List of route IDs to benchmark",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "testCaseId": "case_ai_frontier_daily_001",
                "title": "AI 前沿资讯多路线对比",
                "inputPayload": {"content": "今日 AI 前沿测试内容"},
                "commonParams": {"targetDuration": 45, "aspectRatio": "9:16"},
                "routeIds": ["local_frame_compose", "template_programmatic_render"],
            }
        }
    }


class VisualComposeRequest(BaseModel):
    """JSON body for POST /video-lab/visual-compose (单条视觉路线端到端出片)"""

    content: str = Field(..., min_length=1, description="报告原文")
    visualRoute: str = Field(..., min_length=1, description="视觉路线 routeId")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="生成参数 (targetDuration, aspectRatio, keyPointCount, useLlmPlan...)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "今日 AI 前沿...",
                "visualRoute": "ai_asset_then_compose",
                "params": {"targetDuration": 45, "aspectRatio": "9:16", "keyPointCount": 6},
            }
        }
    }


class TechniqueProbeRequest(BaseModel):
    """JSON body for POST /video-lab/technique-probe (最佳技术探测：多路线各出片→排名)"""

    content: str = Field(..., min_length=1, description="报告原文")
    routes: list[str] = Field(
        default_factory=list,
        description="要探测的视觉路线 routeId 列表；留空=默认三条已落地路线",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="生成参数 (targetDuration, aspectRatio, keyPointCount, useLlmPlan...)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "今日 AI 前沿...",
                "routes": [],
                "params": {"targetDuration": 45, "aspectRatio": "9:16", "keyPointCount": 3},
            }
        }
    }


class FramePreviewRequest(BaseModel):
    """JSON body for POST /video-lab/frame-preview (单帧快速预览，调试台)"""

    visualRoute: str = Field(..., min_length=1, description="视觉路线 routeId")
    frameType: str = Field(default="keypoint", description="cover | keypoint")
    shot: dict[str, Any] = Field(
        default_factory=dict,
        description="单条内容 {headline, display, emphasisTerms}",
    )
    coverTitle: str = Field(default="", description="封面标题（frameType=cover 时用）")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="渲染参数 (aspectRatio, index, total...)",
    )


class VisualJudgeRequest(BaseModel):
    """JSON body for POST /video-lab/visual-judge (视觉模型感知评分)"""

    imageUrl: str = Field(..., min_length=1, description="/runtime/... 画面或视频 URL")
    route: str = Field(default="", description="可选：路线 ID，提供则把感知评分留痕")


class ClipPreviewRequest(BaseModel):
    """JSON body for POST /video-lab/clip-preview (动效片段预览)"""

    visualRoute: str = Field(..., min_length=1)
    content: str = Field(default="", description="报告原文（Remotion 用）")
    shot: dict[str, Any] = Field(default_factory=dict, description="单条内容（Pillow/AI 素材 Ken Burns 用）")
    frameType: str = Field(default="keypoint", description="cover | keypoint")
    coverTitle: str = Field(default="")
    params: dict[str, Any] = Field(default_factory=dict)


class StyleFamilyCompareRequest(BaseModel):
    """JSON body for POST /video-lab/style-family/compare"""

    content: str = Field(
        default="科学研究评审实现突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%。\n依据：依据 1\n购物AI助手落后：主流模型通过率仅57-77%。\n依据：依据 1\n企业级AI加速落地：Anthropic与TCS合作，DeepMind投资千万美元。\n依据：依据 1",
        description="报告原文内容（将拆分为多个要点）",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="渲染参数，支持 keyPointCount, clipSeconds, aspectRatio, useLlmPlan",
    )


class CreateChainBenchmarkRequest(BaseModel):
    """JSON body for POST /video-lab/chain-benchmarks"""

    testCaseId: str = Field(..., min_length=1, description="ID of the test case")
    title: str = Field(..., min_length=1, description="Human-readable title for this benchmark")
    inputPayload: dict[str, Any] = Field(
        default_factory=dict,
        description="Input payload passed to all chains",
    )
    commonParams: dict[str, Any] = Field(
        default_factory=dict,
        description="Common parameters for all chains (e.g. targetDuration, aspectRatio)",
    )
    chainIds: list[str] = Field(
        ...,
        min_length=1,
        description="List of chain IDs to benchmark",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "testCaseId": "case_ai_frontier_daily_001",
                "title": "AI 前沿资讯完整链路对比",
                "inputPayload": {"content": "今日 AI 前沿测试内容"},
                "commonParams": {"targetDuration": 45, "aspectRatio": "9:16"},
                "chainIds": ["local_frame_tts_video", "remotion_tts_video", "hyperframes_tts_video"],
            }
        }
    }


# ─── Style Sample Gallery ─────────────────────────────────────────────────────

class StyleSampleGenerateRequest(BaseModel):
    """JSON body for POST /video-lab/style-samples/generate"""

    style_name: str = Field(..., min_length=1, description="风格名称，如「动态数据栏目」")
    description: str = Field(default="", description="风格描述")
    route_id: str = Field(..., min_length=1, description="视觉路线 routeId")
    content: str = Field(default="", description="生成用的报告原文（可短，30字以上）")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="生成参数（targetDuration, aspectRatio, keyPointCount 等）",
    )
    tags: list[str] = Field(default_factory=list, description="标签列表")


class StyleSampleSaveRequest(BaseModel):
    """JSON body for POST /video-lab/style-samples（保存已生成的样片记录）"""

    id: str = Field(..., min_length=1, description="样片 ID")
    route_id: str = Field(..., min_length=1)
    route_name: str = Field(..., min_length=1)
    style_name: str = Field(..., min_length=1)
    description: str = Field(default="")
    status: str = Field(default="candidate")
    params: dict[str, Any] = Field(default_factory=dict)
    output_type: str = Field(default="mp4")
    output_path: str = Field(default="")
    poster_path: str = Field(default="")
    audio_url: str = Field(default="")
    srt_url: str = Field(default="")
    manifest_url: str = Field(default="")
    content_preview: str = Field(default="")
    duration_sec: float = Field(default=0.0)
    audio_duration_sec: float = Field(default=0.0)
    tags: list[str] = Field(default_factory=list)
    evaluation_readability: int | None = Field(default=None, ge=1, le=5)
    evaluation_motion: int | None = Field(default=None, ge=1, le=5)
    evaluation_visual_impact: int | None = Field(default=None, ge=1, le=5)
    evaluation_stability: int | None = Field(default=None, ge=1, le=5)
    evaluation_cost: int | None = Field(default=None, ge=1, le=5)
    evaluation_notes: str = Field(default="")
