"""
Adapter: local_frame_compose
本地图像帧合成 + FFmpeg
"""

from app.video_lab.models import VideoExperimentResult
from app.video_lab.planners.pipeline_builder import build_12step_pipeline


def run_local_frame_compose(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟本地图像帧合成流程。
    使用 Pillow/Canvas/OpenCV 生成帧，FFmpeg 合成视频。
    """
    method_category = "local_frame_compose"

    logs = [
        "[ADAPTER] local_frame_compose",
        "[1/5] 初始化合成器 (Pillow + FFmpeg)...",
        "[2/5] 生成图像帧序列 (30fps)...",
        "[3/5] 应用动画参数:位移、缩放、淡入淡出...",
        "[4/5] 调用 FFmpeg 合成 MP4...",
        "[5/5] 输出视频完成",
        "",
        "【方案特点】",
        "  成本: 低 | 可控性: 高 | 稳定性: 高 | 产品化: 高",
        "  适合: 固定模板批量生成、数据可视化、文字动态效果",
        "  不适合: 高逼真度人物/风景、创意运动",
        "",
        "【风险提示】",
        "  视觉上限有限，无法生成真实运动画面",
        "  适合作为结构化信息展示，不适合情绪/创意内容",
        "  建议配合 AI 图片生成封面和背景素材增强视觉",
    ]

    # 使用 12 步骤流水线
    production_steps = build_12step_pipeline(
        experiment_id=experiment_id,
        test_case_id=test_case_id,
        method_category=method_category,
        input_payload=input_payload,
        params=params,
    )

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/local_frame_compose.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "frameCount": 1350,
            "fps": 30,
            "resolution": "1080x1920",
            "format": "mp4",
            "codec": "libx264",
            "method": method_category,
        },
        logs=logs,
        provider="Pillow + FFmpeg",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "frameEngine": "Pillow",
            "synthesizer": "FFmpeg",
            "status": "mock_success",
            "riskAssessment": {
                "accuracy": "high - 文字精确可控",
                "stability": "high - 批量一致",
                "visualAppeal": "medium - 视觉上限有限",
                "productization": "high - 成本低易规模化",
            },
        },
        productionSteps=production_steps,
    )
