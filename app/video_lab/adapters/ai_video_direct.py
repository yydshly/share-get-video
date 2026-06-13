"""
Adapter: ai_video_direct
大模型直接生成视频 - 文生视频 / 图生视频
"""

from app.video_lab.models import VideoExperimentResult, ImplementationStatus


def run_ai_video_direct(
    experiment_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    大模型直接生成视频。
    当前状态: reserved / not_configured
    """
    logs = [
        "[1/3] 连接视频生成模型 API...",
        "[2/3] 发送生成请求 (prompt/video reference)...",
        "[3/3] 等待模型生成 (预计 2-5 分钟)...",
    ]

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl="",
        coverUrl="",
        assets={
            "modelProvider": "待配置",
            "estimatedDuration": "5-60秒",
            "resolution": "待配置",
            "status": ImplementationStatus.RESERVED.value,
        },
        logs=logs + ["当前方法状态: reserved/not_configured - 等待视频模型接入"],
        provider="待定",
        adapter="ai_video_direct",
        rawOutput={
            "method": "ai_video_direct",
            "status": "reserved",
            "note": "视频模型 API 未接入，当前为占位状态",
        },
    )
