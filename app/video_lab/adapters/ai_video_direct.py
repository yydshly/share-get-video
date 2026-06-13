"""
Adapter: ai_video_direct
大模型直接生成视频 - 文生视频 / 图生视频
"""

from app.video_lab.models import VideoExperimentResult, ProductionStepStatus, VideoProductionStep, VideoProductionArtifact, ArtifactType


def run_ai_video_direct(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    大模型直接生成视频。
    当前状态: reserved / not_configured
    """
    method_category = "ai_video_direct"

    # 只返回关键步骤，不使用完整 12 步（因为是 reserved 状态）
    steps = [
        VideoProductionStep(
            step_id=f"{experiment_id}_step_01_input",
            name="接收输入内容",
            description="解析原始输入",
            status=ProductionStepStatus.SUCCEEDED,
            input_summary=f"原始文本，长度 {len(input_payload.get('content', ''))} 字符",
            output_summary="输入验证通过",
            logs=["[1/4] 接收输入内容", "  输入验证: 通过"],
            artifacts=[],
        ),
        VideoProductionStep(
            step_id=f"{experiment_id}_step_02_prompt",
            name="压缩为视频 Prompt",
            description="将内容压缩为文生视频 prompt",
            status=ProductionStepStatus.SUCCEEDED,
            input_summary="原始内容",
            output_summary="压缩为 prompt (约 200 字)",
            key_data={
                "promptLength": "~200 chars",
                "compressionRatio": "10:1",
            },
            logs=[
                "[2/4] 压缩为视频 Prompt",
                "  原始长度: ~1000 chars",
                "  压缩后: ~200 chars",
                "  ⚠️ 信息损失风险: 高",
            ],
            artifacts=[],
        ),
        VideoProductionStep(
            step_id=f"{experiment_id}_step_03_generation",
            name="调用视频模型生成",
            description="发送 prompt 到视频生成模型",
            status=ProductionStepStatus.SKIPPED,
            input_summary="video prompt",
            output_summary="⚠️ SKIPPED - video model not configured",
            key_data={
                "status": "reserved",
                "provider": "待定 (Runway/Kling/Sora/Pika)",
                "estimatedDuration": "60-300s",
            },
            logs=[
                "[3/4] 调用视频模型生成",
                "  ⚠️ 状态: reserved / not_configured",
                "  video model API 未接入",
                "  等待 V0.4 接入",
            ],
            artifacts=[],
        ),
        VideoProductionStep(
            step_id=f"{experiment_id}_step_04_risks",
            name="风险评估",
            description="评估 AI 直接生成的适用性",
            status=ProductionStepStatus.SUCCEEDED,
            input_summary="case_ai_frontier_daily_001",
            output_summary="结论: 不推荐用于 AI 资讯共享视频",
            key_data={
                "accuracyRisk": "high - 字幕不可控",
                "stabilityRisk": "high - 批量不一致",
                "costRisk": "very_high",
                "verdict": "not_recommended",
            },
            logs=[
                "[4/4] 风险评估",
                "  信息准确性风险: 高 - AI 可能漏掉或扭曲关键信息",
                "  字幕可控性: 低 - 文生视频字幕不可控",
                "  批量一致性: 低 - 每次生成结果不同",
                "  成本: 极高 - 按次计费",
                "",
                "  ❌ 结论: 不推荐用于 AI 资讯共享视频",
                "  ✓ 适用: 背景素材、情绪镜头，不适合主体内容",
            ],
            artifacts=[
                VideoProductionArtifact(
                    artifact_id=f"{experiment_id}_art_risk",
                    type=ArtifactType.EVALUATION,
                    title="风险评估报告",
                    summary="AI 直接生成视频 - 不推荐用于 AI 资讯共享",
                    payload={
                        "accuracyRisk": "high",
                        "subtitleRisk": "high",
                        "stabilityRisk": "high",
                        "costRisk": "very_high",
                        "verdict": "not_recommended_for_ai_news",
                        "suitableFor": ["background_footage", "emotional_shots", "creative_exploration"],
                    },
                )
            ],
        ),
    ]

    logs = [
        "[ADAPTER] ai_video_direct (大模型直接生成视频)",
        "",
        "【方案状态】",
        "  ⚠️ 状态: reserved / not_configured",
        "  video model API 未接入",
        "",
        "【方案特点】",
        "  成本: 极高 | 可控性: 低 | 稳定性: 低 | 产品化: 中",
        "  适合: 情绪/氛围短片、图片动态化、创意探索",
        "  不适合: 需要精确文字、结构化信息承载、批量一致性要求",
        "",
        "【AI 资讯共享视频场景风险】",
        "  ❌ 信息准确性风险: 高 - AI 可能遗漏关键信息点",
        "  ❌ 字幕可控性: 低 - 文生视频字幕不可控，可能错漏",
        "  ❌ 批量一致性: 低 - 每次生成结果不同",
        "  ❌ 成本: 极高 - 按次计费，无法批量",
        "",
        "【建议】",
        "  仅作为背景素材或情绪镜头来源，主体内容仍用模板化渲染",
    ]

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl="",
        coverUrl="",
        assets={
            "method": method_category,
            "status": "reserved",
            "message": "video model API 未接入，当前为占位状态",
        },
        logs=logs,
        provider="待定",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "status": "reserved",
            "note": "视频模型 API 未接入，当前为占位状态",
            "riskAssessment": {
                "accuracy": "low - 信息可能错漏",
                "stability": "low - 批量不一致",
                "visualAppeal": "high - 生成式视觉丰富",
                "productization": "low - 成本高可控性低",
            },
            "productizationRecommendation": "not_recommended",
            "productizationReason": "信息准确性、字幕可控性、批量一致性均不满足 AI 资讯共享视频要求",
        },
        productionSteps=steps,
    )
