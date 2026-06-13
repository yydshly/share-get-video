"""
Adapter: template_programmatic_render
Remotion 程序化模板渲染
"""

from app.video_lab.models import VideoExperimentResult
from app.video_lab.planners.pipeline_builder import build_12step_pipeline


def run_remotion_template(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟 Remotion 程序化模板渲染流程。
    使用 React/CSS/SVG/Canvas 做模板化视频渲染。
    """
    method_category = "template_programmatic_render"

    logs = [
        "[ADAPTER] template_programmatic_render (Remotion)",
        "[1/6] 加载 Remotion 项目...",
        "[2/6] 解析模板参数 JSON (InsightCardVideo)...",
        "[3/6] 渲染 React 组件序列 (Canvas)...",
        "[4/6] 合成音频轨道 (TTS + BGM)...",
        "[5/6] 编码输出 MP4 (H.264, 30fps)...",
        "[6/6] 渲染完成，生成预览链接",
        "",
        "【方案特点】",
        "  成本: 中 | 可控性: 高 | 稳定性: 中 | 产品化: 高",
        "  适合: 资讯/日报视频、产品介绍、知识卡片、数据报告",
        "  不适合: 高逼真度人物场景、自由创意内容",
        "",
        "【风险提示】",
        "  Remotion 渲染依赖 Node.js 环境 (V0.3 目标接入)",
        "  模板设计有前期成本，但批量生成成本极低",
        "  字幕与旁白时间轴精确可控，信息准确性高",
        "",
        "【推荐理由 - AI 资讯共享视频】",
        "  ✓ 文字精确可控，无 AI 生成字幕的错漏风险",
        "  ✓ 批量生成一致性高，适合日更/周更场景",
        "  ✓ 模板迭代成本低，版本管理清晰",
        "  ✓ 字幕+旁白时间轴完全对齐",
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
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/remotion_render.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "compositionId": "InsightCardVideo",
            "frameCount": 1350,
            "fps": 30,
            "resolution": "1080x1920",
            "format": "mp4",
            "templateVersion": "1.0.0",
            "method": method_category,
        },
        logs=logs,
        provider="Remotion",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "renderer": "Remotion",
            "stack": ["React", "Canvas", "FFmpeg"],
            "status": "mock_success",
            "riskAssessment": {
                "accuracy": "high - 模板精确控制",
                "stability": "medium - 渲染环境依赖",
                "visualAppeal": "high - React 动画灵活",
                "productization": "high - 批量成本极低",
            },
            "productizationRecommendation": "recommended",
            "productizationReason": "信息准确性高，批量成本低，模板可控",
        },
        productionSteps=production_steps,
    )
