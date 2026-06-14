"""
Visual Renderer - 可插拔视觉渲染抽象

设计目标（解耦"画面生成方式"与"成片链路"）：
    一条完整链路 = 结构化 → 关键点 → 旁白 → TTS → 字幕
                  → [VisualRenderer 产出静默视频] → FFmpeg 合成音频+字幕 → 成片

每种"生成视频的方式"（Pillow 帧、Remotion 模板、AI 视频、HTML…）只需实现
一个 VisualRenderer：输入结构化内容 + 参数，输出**一个静默视频文件**。
下游的 TTS / 字幕 / 合成保持共享，从而可以在同一条链路上横向对比不同画面技术。

统一契约：VisualRenderer.render() 必须返回一个静默视频（仅画面，无音频）的路径。
- Pillow：生成帧序列后用 FFmpeg 合成 silent.mp4
- Remotion：直接渲染出静默 output.mp4
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VisualRenderRequest:
    """视觉渲染输入。

    所有视觉路线共享同一份上游内容（structured + key_points），各路线
    通过 ``params`` 读取自己关心的参数（如转场帧数、模板预设等）。
    """

    experiment_id: str
    structured: dict[str, Any]
    key_points: dict[str, Any]
    target_duration_sec: float
    resolution: tuple[int, int]
    params: dict[str, Any] = field(default_factory=dict)
    # 若已知配音时长，视觉可对齐到音频（部分路线使用）
    audio_duration_sec: float = 0.0
    # 旁白分段（含 startSec/durationSec），用于画面与配音时序对齐
    voiceover_segments: list[dict[str, Any]] = field(default_factory=list)
    # 少数路线（如 Remotion adapter）需要原始输入再推导一次
    test_case_id: str = ""
    input_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualRenderResult:
    """视觉渲染输出。核心是 ``silent_video_path``（静默视频文件路径）。"""

    success: bool
    route_id: str = ""
    silent_video_path: str = ""
    silent_video_url: str = ""
    cover_path: str = ""
    cover_url: str = ""
    total_duration_sec: float = 0.0
    frame_count: int = 0
    message: str = ""
    logs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # 路线特有的元数据（用于详情展示 / 对比）
    extra: dict[str, Any] = field(default_factory=dict)


class VisualRenderer(ABC):
    """可插拔视觉渲染器协议。

    新增一种"生成视频的方式"时：实现本类 → 在 registry 注册，即可挂入链路对比。
    """

    #: 与 ChainDefinition.visual_route / MethodCategory 对齐的稳定 ID
    route_id: str = ""
    #: 人类可读名称
    display_name: str = ""

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """检查该渲染器运行环境是否就绪。返回 (是否可用, 说明)。"""
        raise NotImplementedError

    @abstractmethod
    def render(self, request: VisualRenderRequest) -> VisualRenderResult:
        """产出静默视频。失败时返回 ``success=False`` 并填 ``message``，不抛异常。"""
        raise NotImplementedError
