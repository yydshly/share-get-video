"""
Adapter: hybrid_pipeline
混合编排流水线 - 按场景自动路由
"""

from app.video_lab.models import VideoExperimentResult


def run_hybrid_pipeline(
    experiment_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟混合编排流水线。
    按场景自动选择：本地合成、Remotion、AI 视频、AI 图片、TTS、FFmpeg 等能力组合。
    当前状态: mock
    """
    logs = [
        "[1/7] 分析场景特征和输入内容...",
        "[2/7] 路由决策: 选择技术组合路径...",
        "  -> 路径A: Remotion 模板渲染 (结构化内容)",
        "  -> 路径B: AI 图像生成 (视觉素材)",
        "  -> 路径C: TTS 旁白生成 (音频)",
        "[3/7] 并行执行各阶段生成任务...",
        "[4/7] 素材质检与筛选...",
        "[5/7] 混合编排合成...",
        "[6/7] FFmpeg 最终封装...",
        "[7/7] 输出多格式版本 (9:16 / 16:9)",
    ]

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/hybrid_pipeline.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "pipelineSteps": [
                "scene_analysis",
                "route_decision",
                "parallel_generation",
                "quality_filter",
                "hybrid_compose",
                "final_export",
            ],
            "resolution": "1080x1920",
            "formats": ["mp4", "webm"],
            "versions": ["9:16", "16:9"],
        },
        logs=logs,
        provider="Hybrid Router + Multi-Engine",
        adapter="hybrid_pipeline",
        rawOutput={
            "method": "hybrid_pipeline",
            "router": "场景路由引擎",
            "engines": ["Remotion", "AI-ImageGen", "TTS", "FFmpeg"],
            "status": "mock",
        },
    )
