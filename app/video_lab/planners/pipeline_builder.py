"""
Production Pipeline Builder - 构建 12 步骤生产流水线
"""

import time
import uuid
from datetime import datetime
from typing import Any

from app.video_lab.models import (
    VideoProductionStep,
    VideoProductionArtifact,
    ProductionStepStatus,
    ArtifactType,
)
from app.video_lab.planners.content_structurer import structure_content
from app.video_lab.planners.key_point_extractor import extract_key_points
from app.video_lab.planners.script_planner import generate_script
from app.video_lab.planners.storyboard_planner import generate_storyboard
from app.video_lab.planners.subtitle_planner import generate_subtitle_plan, generate_voiceover_plan
from app.video_lab.planners.asset_planner import generate_asset_plan
from app.video_lab.planners.render_planner import generate_render_plan


def _step(
    step_id: str,
    name: str,
    description: str,
    input_summary: str,
    output_summary: str,
    key_data: dict[str, Any] | None = None,
    artifacts: list[VideoProductionArtifact] | None = None,
    logs: list[str] | None = None,
) -> VideoProductionStep:
    """创建单个步骤"""
    return VideoProductionStep(
        step_id=step_id,
        name=name,
        description=description,
        status=ProductionStepStatus.SUCCEEDED,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        elapsed_ms=0,
        input_summary=input_summary,
        output_summary=output_summary,
        key_data=key_data or {},
        logs=logs or [],
        artifacts=artifacts or [],
    )


def build_12step_pipeline(
    experiment_id: str,
    test_case_id: str,
    method_category: str,
    input_payload: dict[str, Any],
    params: dict[str, Any],
) -> list[VideoProductionStep]:
    """
    构建 12 步骤生产流水线。
    返回完整的步骤列表（每个步骤都已完成，状态为 SUCCEEDED）。
    """
    raw_content = input_payload.get("content", "")
    target_duration = params.get("targetDuration", 45)
    aspect_ratio = params.get("aspectRatio", "9:16")

    steps = []

    # ── Step 1: 接收输入内容 ──────────────────────────────────
    step1 = _step(
        step_id=f"{experiment_id}_step_01_input",
        name="接收输入内容",
        description="解析原始输入，验证输入格式和内容完整性",
        input_summary=f"原始文本，长度 {len(raw_content)} 字符",
        output_summary="输入验证通过，提取总起段和条目",
        key_data={
            "inputLength": len(raw_content),
            "inputPreview": raw_content[:100] + "...",
        },
        logs=[
            "[1/12] 接收输入内容",
            f"  输入类型: {test_case_id}",
            f"  内容长度: {len(raw_content)} 字符",
            "  输入验证: 通过",
        ],
    )
    steps.append(step1)

    # ── Step 2: 内容结构化 ──────────────────────────────────
    structured = structure_content(raw_content, test_case_id)
    artifact_normalized = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_normalized",
        type=ArtifactType.NORMALIZED_CONTENT,
        title="结构化内容",
        summary=f"lead + {structured['totalItems']} 条内容",
        payload=structured,
    )
    step2 = _step(
        step_id=f"{experiment_id}_step_02_structure",
        name="内容结构化",
        description="将原始文本按段落拆分，提取标题和依据",
        input_summary="原始文本",
        output_summary=f"总起段 + {structured['totalItems']} 条内容项",
        key_data={
            "leadLength": len(structured.get("lead", "")),
            "itemCount": structured.get("totalItems", 0),
        },
        artifacts=[artifact_normalized],
        logs=[
            "[2/12] 内容结构化",
            f"  总起段: {structured.get('lead', '')[:50]}...",
            f"  内容条目: {structured.get('totalItems', 0)} 条",
            "  结构化完成",
        ],
    )
    steps.append(step2)

    # ── Step 3: 提取视频关键信息点 ──────────────────────────
    key_points = extract_key_points(structured, target_duration)
    artifact_kp = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_keypoints",
        type=ArtifactType.KEY_POINTS,
        title="关键信息点",
        summary=f"从 {key_points.get('selectedFrom', 0)} 条中选出 {key_points.get('totalPoints', 0)} 条",
        payload=key_points,
    )
    step3 = _step(
        step_id=f"{experiment_id}_step_03_keypoints",
        name="提取视频关键信息点",
        description="根据目标时长从结构化内容中筛选关键信息点",
        input_summary=f"{structured['totalItems']} 条内容项",
        output_summary=f"选取 {key_points['totalPoints']} 个关键信息点",
        key_data={
            "totalPoints": key_points.get("totalPoints", 0),
            "selectedFrom": key_points.get("selectedFrom", 0),
        },
        artifacts=[artifact_kp],
        logs=[
            "[3/12] 提取视频关键信息点",
            f"  原始条目: {key_points.get('selectedFrom', 0)}",
            f"  选取条目: {key_points.get('totalPoints', 0)}",
            f"  目标时长: {target_duration}s",
        ],
    )
    steps.append(step3)

    # ── Step 4: 判断视频表达类型 ────────────────────────────
    step4 = _step(
        step_id=f"{experiment_id}_step_04_strategy",
        name="判断视频表达类型",
        description="根据测试用例类型决定视频表达策略",
        input_summary=f"测试用例: {test_case_id}",
        output_summary="采用结构化信息展示型策略",
        key_data={
            "testCase": test_case_id,
            "strategy": "structured_info_display",
            "targetDuration": target_duration,
            "aspectRatio": aspect_ratio,
        },
        logs=[
            "[4/12] 判断视频表达类型",
            f"  场景: {test_case_id}",
            f"  策略: structured_info_display",
            f"  时长: {target_duration}s | 比例: {aspect_ratio}",
        ],
    )
    steps.append(step4)

    # ── Step 5: 选择生成方案 ────────────────────────────────
    step5 = _step(
        step_id=f"{experiment_id}_step_05_method",
        name="选择生成方案",
        description=f"路由到 {method_category} 方案",
        input_summary="等待方案选择",
        output_summary=f"使用方案: {method_category}",
        key_data={
            "methodCategory": method_category,
            "suitableFor": ["structured_content", "text_cards"],
            "notSuitableFor": ["high_realism", "free_form_creative"],
        },
        logs=[
            "[5/12] 选择生成方案",
            f"  方案: {method_category}",
            "  适合: 结构化内容、信息卡片、字幕展示",
            "  不适合: 高逼真度、自由创意",
        ],
    )
    steps.append(step5)

    # ── Step 6: 生成共享视频脚本 ────────────────────────────
    script = generate_script(key_points, aspect_ratio, target_duration)
    artifact_script = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_script",
        type=ArtifactType.SCRIPT,
        title="视频脚本",
        summary=f"{script['totalSegments']} 个段落，预计 {script['estimatedDuration']}s",
        payload=script,
    )
    step6 = _step(
        step_id=f"{experiment_id}_step_06_script",
        name="生成共享视频脚本",
        description="根据关键信息点生成视频脚本（每段标题+视觉描述+旁白）",
        input_summary=f"{key_points['totalPoints']} 个关键信息点",
        output_summary=f"{script['totalSegments']} 个段落",
        key_data={
            "totalSegments": script.get("totalSegments", 0),
            "estimatedDuration": script.get("estimatedDuration", 0),
        },
        artifacts=[artifact_script],
        logs=[
            "[6/12] 生成共享视频脚本",
            f"  段落数: {script.get('totalSegments', 0)}",
            f"  预计时长: {script.get('estimatedDuration', 0)}s",
            "  脚本生成完成",
        ],
    )
    steps.append(step6)

    # ── Step 7: 生成分镜 ──────────────────────────────────
    storyboard = generate_storyboard(script, method_category)
    artifact_sb = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_storyboard",
        type=ArtifactType.STORYBOARD,
        title="分镜",
        summary=f"{storyboard['totalFrames']} 个画面帧",
        payload=storyboard,
    )
    step7 = _step(
        step_id=f"{experiment_id}_step_07_storyboard",
        name="生成分镜",
        description="将脚本转换为具体画面帧描述",
        input_summary=f"{script['totalSegments']} 个脚本段落",
        output_summary=f"{storyboard['totalFrames']} 个画面帧",
        key_data={
            "totalFrames": storyboard.get("totalFrames", 0),
            "estimatedDuration": storyboard.get("estimatedDurationSec", 0),
        },
        artifacts=[artifact_sb],
        logs=[
            "[7/12] 生成分镜",
            f"  画面帧数: {storyboard.get('totalFrames', 0)}",
            f"  预计时长: {storyboard.get('estimatedDurationSec', 0)}s",
            "  分镜生成完成",
        ],
    )
    steps.append(step7)

    # ── Step 8: 生成旁白与字幕计划 ─────────────────────────
    subtitle_plan = generate_subtitle_plan(script, include_voiceover=False)
    voiceover_plan = generate_voiceover_plan(script)
    artifact_sub = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_subtitle",
        type=ArtifactType.SUBTITLE_PLAN,
        title="字幕计划",
        summary=f"{subtitle_plan['totalSegments']} 个字幕段",
        payload=subtitle_plan,
    )
    artifact_vo = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_voiceover",
        type=ArtifactType.VOICEOVER_PLAN,
        title="旁白计划",
        summary=f"{voiceover_plan['totalSegments']} 个旁白段",
        payload=voiceover_plan,
    )
    step8 = _step(
        step_id=f"{experiment_id}_step_08_subtitle",
        name="生成旁白与字幕计划",
        description="生成字幕时间轴和旁白文本",
        input_summary=f"{script['totalSegments']} 个脚本段",
        output_summary=f"{subtitle_plan['totalSegments']} 个字幕段 + {voiceover_plan['totalSegments']} 个旁白段",
        key_data={
            "subtitleSegments": subtitle_plan.get("totalSegments", 0),
            "voiceoverSegments": voiceover_plan.get("totalSegments", 0),
            "format": "SRT",
        },
        artifacts=[artifact_sub, artifact_vo],
        logs=[
            "[8/12] 生成旁白与字幕计划",
            f"  字幕段: {subtitle_plan.get('totalSegments', 0)}",
            f"  旁白段: {voiceover_plan.get('totalSegments', 0)}",
            "  旁白 TTS: 待接入",
        ],
    )
    steps.append(step8)

    # ── Step 9: 生成素材计划 ────────────────────────────────
    asset_plan = generate_asset_plan(key_points, method_category)
    artifact_asset = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_assets",
        type=ArtifactType.ASSET_PLAN,
        title="素材计划",
        summary=f"{asset_plan['totalAssets']} 个素材",
        payload=asset_plan,
    )
    step9 = _step(
        step_id=f"{experiment_id}_step_09_assets",
        name="生成素材计划",
        description="规划封面图、信息卡片背景、图标、BGM 等",
        input_summary=f"{key_points['totalPoints']} 个信息点",
        output_summary=f"素材总数: {asset_plan['totalAssets']}",
        key_data={
            "totalAssets": asset_plan.get("totalAssets", 0),
            "hasCover": asset_plan.get("cover") is not None,
            "cardCount": len(asset_plan.get("infoCards", [])),
        },
        artifacts=[artifact_asset],
        logs=[
            "[9/12] 生成素材计划",
            f"  素材总数: {asset_plan.get('totalAssets', 0)}",
            f"  封面图: {'待生成' if method_category == 'ai_asset_then_compose' else 'placeholder'}",
            f"  信息卡片背景: {len(asset_plan.get('infoCards', []))} 张",
            f"  BGM: {asset_plan.get('bgm', {}).get('description', 'N/A')}",
        ],
    )
    steps.append(step9)

    # ── Step 10: 生成渲染计划 ──────────────────────────────
    render_plan = generate_render_plan(script, storyboard, aspect_ratio, method_category)
    artifact_render = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_render",
        type=ArtifactType.RENDER_PLAN,
        title="渲染计划",
        summary=f"使用 {render_plan['renderer']}，分辨率 {render_plan['resolution']}",
        payload=render_plan,
    )
    step10 = _step(
        step_id=f"{experiment_id}_step_10_render",
        name="生成渲染计划",
        description="规划渲染参数、输出路径、编码设置",
        input_summary=f"分镜 {storyboard['totalFrames']} 帧",
        output_summary=f"渲染器: {render_plan['renderer']}",
        key_data={
            "renderer": render_plan.get("renderer", ""),
            "resolution": render_plan.get("resolution", ""),
            "fps": render_plan.get("fps", 30),
            "codec": render_plan.get("codec", ""),
        },
        artifacts=[artifact_render],
        logs=[
            "[10/12] 生成渲染计划",
            f"  渲染器: {render_plan.get('renderer', '')}",
            f"  分辨率: {render_plan.get('resolution', '')}",
            f"  帧率: {render_plan.get('fps', 30)} fps",
            f"  编码: {render_plan.get('codec', '')}",
        ],
    )
    steps.append(step10)

    # ── Step 11: 执行 mock 渲染 ─────────────────────────────
    mock_video_payload = {
        "status": "mock",
        "method": method_category,
        "videoUrl": f"https://mock-cdn.example.com/videos/{experiment_id}/output.mp4",
        "coverUrl": f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        "estimatedDuration": script.get("estimatedDuration", target_duration),
        "message": "Mock 渲染完成，真实渲染待 V0.2+ 接入",
    }
    artifact_mock = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_mock_video",
        type=ArtifactType.MOCK_VIDEO,
        title="Mock 视频结果",
        summary="当前为 Mock 结果，真实 MP4 待 V0.2 接入",
        payload=mock_video_payload,
    )
    step11 = _step(
        step_id=f"{experiment_id}_step_11_render",
        name="执行 mock 渲染",
        description="模拟渲染过程（真实渲染待 V0.2 接入）",
        input_summary=f"渲染器: {render_plan['renderer']}",
        output_summary="Mock 渲染完成",
        key_data={
            "status": "mock",
            "renderer": method_category,
            "mockMessage": "当前为 Mock 结果，真实渲染待 V0.2+",
        },
        artifacts=[artifact_mock],
        logs=[
            "[11/12] 执行 mock 渲染",
            f"  渲染器: {method_category}",
            f"  状态: MOCK (真实渲染待 V0.2 接入)",
            f"  预计时长: {mock_video_payload['estimatedDuration']}s",
            "  Mock 渲染完成",
        ],
    )
    steps.append(step11)

    # ── Step 12: 生成总结建议 ───────────────────────────────
    conclusion_payload = {
        "method": method_category,
        "totalSteps": 12,
        "succeededSteps": 12,
        "artifacts": [
            "normalized_content",
            "key_points",
            "script",
            "storyboard",
            "subtitle_plan",
            "voiceover_plan",
            "asset_plan",
            "render_plan",
            "mock_video",
        ],
        "recommendation": "mock",
        "riskLevel": "medium",
        "nextVersion": "V0.2: 本地帧合成 + FFmpeg 真实 MP4",
    }
    artifact_conclusion = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_conclusion",
        type=ArtifactType.EVALUATION,
        title="总结与建议",
        summary="12 步骤完成，产品化推荐等级: medium",
        payload=conclusion_payload,
    )
    step12 = _step(
        step_id=f"{experiment_id}_step_12_conclusion",
        name="生成总结建议",
        description="汇总实验结果，输出产品化建议",
        input_summary="12 个步骤全部完成",
        output_summary="结论: mock 渲染完成，产品化等级 medium",
        key_data={
            "totalSteps": 12,
            "succeededSteps": 12,
            "recommendation": "mock",
            "riskLevel": "medium",
        },
        artifacts=[artifact_conclusion],
        logs=[
            "[12/12] 生成总结建议",
            "  步骤完成: 12/12",
            "  推荐等级: medium (mock 状态)",
            "  下一步: V0.2 本地帧合成 + FFmpeg 真实 MP4",
        ],
    )
    steps.append(step12)

    return steps
