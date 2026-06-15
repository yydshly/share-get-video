"""
style_gallery/models.py - Style Sample data models
V0.3.7: Style Sample Gallery — lightweight JSONL-backed style experiment records
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SampleStatus(str, Enum):
    CANDIDATE = "candidate"       # 探索中，待评价
    APPROVED = "approved"         # 确认保存
    REJECTED = "rejected"         # 已放弃
    COMPARING = "comparing"       # 入选对比


class EvaluationScore(BaseModel):
    readability: int | None = Field(default=None, ge=1, le=5, description="可读性 1-5")
    motion: int | None = Field(default=None, ge=1, le=5, description="动效/动态感 1-5")
    visual_impact: int | None = Field(default=None, ge=1, le=5, description="视觉冲击力 1-5")
    stability: int | None = Field(default=None, ge=1, le=5, description="稳定性 1-5")
    cost: int | None = Field(default=None, ge=1, le=5, description="成本性价比 1-5")
    notes: str = Field(default="", description="人工评价备注")


class StyleSampleOutput(BaseModel):
    type: str = Field(default="mp4", description="输出类型 mp4 / gif / png")
    path: str = Field(default="", description="相对于 runtime/ 的文件路径")
    poster: str = Field(default="", description="封面/海报图路径")
    audio_url: str = Field(default="", description="音频文件路径")
    srt_url: str = Field(default="", description="字幕文件路径")
    manifest_url: str = Field(default="", description="清单文件路径")


# V0.4.0: Visual judgement result from AI judge
class VisualJudgement(BaseModel):
    score: float = Field(..., description="总分 0-100")
    grade: str = Field(..., description="等级: excellent/good/ok/poor")
    summary: str = Field(default="", description="整体评价摘要")
    strengths: list[str] = Field(default_factory=list, description="优点列表")
    weaknesses: list[str] = Field(default_factory=list, description="问题列表")
    suggestions: list[str] = Field(default_factory=list, description="改进建议")
    judged_at: str = Field(default="", description="评分时间 ISO 格式")
    # 详细维度分 (来自 visual_judge.py 的原始分数，1-5)
    dimensions: dict[str, float] = Field(default_factory=dict, description="各维度分数")


class StyleSample(BaseModel):
    """一条风格样片记录。"""

    id: str = Field(..., description="样片唯一ID，格式 sample_xxxx")
    route_id: str = Field(..., description="视觉路线 routeId")
    route_name: str = Field(..., description="路线展示名")
    style_name: str = Field(..., description="风格名称，如「动态数据栏目」")
    description: str = Field(default="", description="风格描述")
    status: SampleStatus = Field(default=SampleStatus.CANDIDATE, description="样片状态")
    params: dict[str, Any] = Field(default_factory=dict, description="生成时的完整参数")
    output: StyleSampleOutput = Field(default_factory=StyleSampleOutput, description="输出文件信息")
    evaluation: EvaluationScore = Field(default_factory=EvaluationScore, description="人工评价")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    content_preview: str = Field(default="", description="生成所用内容的摘要（前100字）")
    duration_sec: float = Field(default=0.0, description="视频时长（秒）")
    audio_duration_sec: float = Field(default=0.0, description="音频时长（秒）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    # V0.4.0: 视觉评分结果 (可选，兼容旧记录)
    visual_judgement: VisualJudgement | None = Field(default=None, description="AI 视觉评分结果")

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump(mode="json")
        d["created_at"] = self.created_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "StyleSample":
        if isinstance(d.get("created_at"), str):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        # V0.4.0: visual_judgement is optional - pass through if missing (backward compat)
        if "visual_judgement" not in d:
            d["visual_judgement"] = None
        return cls(**d)
