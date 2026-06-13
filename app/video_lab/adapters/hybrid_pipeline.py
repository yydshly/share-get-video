"""
Adapter: hybrid_pipeline
混合编排流水线 - 按场景自动路由
"""

from app.video_lab.models import VideoExperimentResult
from app.video_lab.planners.pipeline_builder import build_12step_pipeline


def run_hybrid_pipeline(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟混合编排流水线。
    按场景自动选择：本地合成、Remotion、AI 视频、AI 图片、TTS、FFmpeg 等能力组合。
    当前状态: mock
    """
    method_category = "hybrid_pipeline"

    logs = [
        "[ADAPTER] hybrid_pipeline (混合编排流水线)",
        "[1/7] 分析场景特征和输入内容...",
        "[2/7] 路由决策: 选择技术组合路径...",
        "  -> 路径A: Remotion 模板渲染 (结构化内容主体)",
        "  -> 路径B: AI 图像生成 (封面/背景素材)",
        "  -> 路径C: TTS 旁白生成 (语音解说)",
        "[3/7] 并行执行各阶段生成任务...",
        "[4/7] 素材质检与筛选...",
        "[5/7] 混合编排合成...",
        "[6/7] FFmpeg 最终封装 (多格式: 9:16 + 16:9)...",
        "[7/7] 输出多格式版本 (MP4 + WebM)",
        "",
        "【方案特点】",
        "  成本: 高 | 可控性: 中 | 稳定性: 中 | 产品化: 高",
        "  适合: 复杂多模态内容、需要多技术配合、按需调度最优路径",
        "  不适合: 简单单一步骤、实时渲染要求、高度定制化单作品",
        "",
        "【风险提示】",
        "  架构复杂度高，需要可靠的路由决策引擎",
        "  多阶段并行增加调度和质检成本",
        "  适合产品化后期，当前阶段建议先用单一方案",
        "",
        "【推荐理由 - AI 资讯共享视频】",
        "  当前阶段不推荐作为首选，架构复杂度高",
        "  建议先用 template_programmatic_render 打通闭环",
        "  后续增强版再引入混合编排能力",
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
            "method": method_category,
        },
        logs=logs,
        provider="Hybrid Router + Multi-Engine",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "router": "场景路由引擎 (待实现)",
            "engines": ["Remotion", "AI-ImageGen", "TTS", "FFmpeg"],
            "status": "mock",
            "riskAssessment": {
                "accuracy": "high - 路由选择最优方案",
                "stability": "medium - 多引擎串并联",
                "visualAppeal": "high - 多模态组合",
                "productization": "high - 最优路径选择",
            },
            "productizationRecommendation": "future",
            "productizationReason": "架构复杂度高，建议 V0.5+ 再引入，当前阶段先用单一方案",
        },
        productionSteps=production_steps,
    )
