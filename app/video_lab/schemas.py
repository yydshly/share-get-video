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
