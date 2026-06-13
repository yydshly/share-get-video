"""
Adapter: ai_asset_then_compose
大模型拆解内容 + 生成素材 + 本地合成
"""

from app.video_lab.models import VideoExperimentResult


def run_ai_asset_then_compose(
    experiment_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟 LLM + TTS + 图像生成 + 合成的多阶段流水线。
    当前状态: mock
    """
    logs = [
        "[1/8] LLM 解析内容结构，生成脚本...",
        "[2/8] 调用 TTS API 生成旁白音频...",
        "[3/8] 生成图片提示词...",
        "[4/8] 调用图像生成模型 (如 DALL-E / Midjourney)...",
        "[5/8] 下载并整理素材...",
        "[6/8] 调用 Remotion 模板渲染...",
        "[7/8] FFmpeg 合成最终视频...",
        "[8/8] 输出带字幕和 BGM 的完整视频",
    ]

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/ai_asset_compose.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "scriptBlocks": 6,
            "ttsAudioDuration": 42,
            "imageCount": 5,
            "resolution": "1080x1920",
            "format": "mp4",
            "hasSubtitle": True,
            "hasBgm": True,
        },
        logs=logs,
        provider="LLM + TTS + ImageGen + Remotion + FFmpeg",
        adapter="ai_asset_then_compose",
        rawOutput={
            "method": "ai_asset_then_compose",
            "llm": "GPT-4 / Claude",
            "tts": "待定",
            "imageGen": "待定",
            "composer": "Remotion + FFmpeg",
            "status": "mock",
        },
    )
