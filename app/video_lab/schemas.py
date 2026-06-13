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
