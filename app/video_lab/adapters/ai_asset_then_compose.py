"""
Adapter: ai_asset_then_compose
大模型拆解内容 + 生成素材 + 本地合成
"""

from app.video_lab.models import VideoExperimentResult
from app.video_lab.planners.pipeline_builder import build_12step_pipeline


def run_ai_asset_then_compose(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟 LLM + TTS + 图像生成 + 合成的多阶段流水线。
    当前状态: mock
    """
    method_category = "ai_asset_then_compose"

    logs = [
        "[ADAPTER] ai_asset_then_compose (AI 素材 + 本地合成)",
        "[1/8] LLM 解析内容结构，生成脚本...",
        "[2/8] 调用 TTS API 生成旁白音频...",
        "[3/8] 生成图片提示词 (DALL-E / Midjourney / FLUX)...",
        "[4/8] 调用图像生成模型...",
        "[5/8] 下载并整理素材...",
        "[6/8] 调用 Remotion 模板渲染 (或 FFmpeg 合成)...",
        "[7/8] 压制字幕轨道...",
        "[8/8] 输出带字幕和 BGM 的完整视频",
        "",
        "【方案特点】",
        "  成本: 高 | 可控性: 中 | 稳定性: 中 | 产品化: 中",
        "  适合: 长视频、多模态内容、半自动化流水线",
        "  不适合: 实时性要求高、成本敏感、需要逐帧精确控制",
        "",
        "【风险提示】",
        "  多阶段串行，总耗时 10-30 分钟",
        "  LLM 生成内容有随机性，需人工审核",
        "  图像生成成本较高，需批量筛选",
        "",
        "【与 template_programmatic_render 对比】",
        "  ✓ 视觉丰富度更高 (AI 图片素材)",
        "  ✗ 成本更高、耗时更长",
        "  ✗ 内容可控性略低 (LLM 生成有随机性)",
        "  → 适合后续增强版，当前阶段推荐 Remotion 模板",
    ]

    production_steps = build_12step_pipeline(
        experiment_id=experiment_id,
        test_case_id=test_case_id,
        method_category=method_category,
        input_payload=input_payload,
        params=params,
    )

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
            "method": method_category,
        },
        logs=logs,
        provider="LLM + TTS + ImageGen + Remotion + FFmpeg",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "llm": "GPT-4 / Claude (待接入)",
            "tts": "ElevenLabs / Azure TTS (待接入)",
            "imageGen": "DALL-E / FLUX (待接入)",
            "composer": "Remotion + FFmpeg",
            "status": "mock",
            "riskAssessment": {
                "accuracy": "medium - LLM 生成有随机性",
                "stability": "medium - 多阶段串行",
                "visualAppeal": "high - AI 素材丰富",
                "productization": "medium - 成本较高",
            },
            "productizationRecommendation": "backup",
            "productizationReason": "视觉丰富度高但成本和耗时较高，适合后续增强版",
        },
        productionSteps=production_steps,
    )
