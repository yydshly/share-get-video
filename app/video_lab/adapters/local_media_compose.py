"""
Adapter: local_media_compose
本地媒体素材合成 - MoviePy / FFmpeg
"""

from app.video_lab.models import VideoExperimentResult
from app.video_lab.planners.pipeline_builder import build_12step_pipeline


def run_local_media_compose(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟本地媒体素材合成。
    使用 MoviePy / FFmpeg 对图片、音频、字幕、BGM 做合成。
    """
    method_category = "local_media_compose"

    logs = [
        "[ADAPTER] local_media_compose",
        "[1/6] 加载素材文件 (图片/音频/字幕)...",
        "[2/6] 分析音频波形与 BGM 节奏...",
        "[3/6] 同步字幕时间轴 (SRT)...",
        "[4/6] 执行视频片段拼接 (MoviePy)...",
        "[5/6] 压制字幕轨道 + 混音 BGM...",
        "[6/6] FFmpeg 最终导出 MP4",
        "",
        "【方案特点】",
        "  成本: 低 | 可控性: 高 | 稳定性: 高 | 产品化: 高",
        "  适合: 多素材组合编排、音频+画面同步、字幕压制",
        "  不适合: 从零生成视觉内容、AI 素材整合",
        "",
        "【风险提示】",
        "  依赖素材质量，素材准备需要人工或 AI 图片生成配合",
        "  字幕需要 SRT 文件，输入内容需结构化",
        "  视觉丰富度取决于素材多样性和后期编排",
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
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/local_media_compose.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "clipsCount": 5,
            "totalDurationSec": 45,
            "resolution": "1080x1920",
            "hasAudio": True,
            "hasSubtitle": True,
            "hasBgm": True,
            "format": "mp4",
            "method": method_category,
        },
        logs=logs,
        provider="MoviePy + FFmpeg",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "editor": "MoviePy",
            "synthesizer": "FFmpeg",
            "status": "mock_success",
            "riskAssessment": {
                "accuracy": "high - 字幕精确可控",
                "stability": "high - 批量一致",
                "visualAppeal": "medium - 依赖素材质量",
                "productization": "high - 成本低易规模化",
            },
        },
        productionSteps=production_steps,
    )
