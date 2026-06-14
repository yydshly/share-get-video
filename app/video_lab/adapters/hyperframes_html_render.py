"""
Adapter: hyperframes_html_render
HeyGen HyperFrames HTML 渲染路线 - V0.3.2 Manual Route

当前为手动路线：
1. 生成 HTML 页面 artifact
2. 人工复制到 HeyGen HyperFrames 插件
3. 渲染视频后手动记录评分

未来如果有 HyperFrames API，可升级为 real route。
"""

from datetime import datetime

from app.video_lab.models import (
    VideoExperimentResult,
    VideoProductionStep,
    VideoProductionArtifact,
    ProductionStepStatus,
    ArtifactType,
)
from app.video_lab.planners.content_structurer import structure_content
from app.video_lab.planners.key_point_extractor import extract_key_points
from app.video_lab.renderers.file_store import (
    get_experiment_dir,
    ensure_runtime_exists,
    path_to_url,
    write_manifest,
)
from app.video_lab.renderers.hyperframes.html_builder import build_html


def make_step(
    step_id: str,
    name: str,
    description: str,
    status: ProductionStepStatus,
    input_summary: str,
    output_summary: str,
    key_data: dict = None,
    logs: list = None,
    artifacts: list = None,
) -> VideoProductionStep:
    return VideoProductionStep(
        step_id=step_id,
        name=name,
        description=description,
        status=status,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        elapsed_ms=0,
        input_summary=input_summary,
        output_summary=output_summary,
        key_data=key_data or {},
        logs=logs or [],
        artifacts=artifacts or [],
    )


def run_hyperframes_html_render(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    HyperFrames HTML render adapter - V0.3.2 manual route.

    Flow:
        1. Receive input
        2. Structure content
        3. Extract key points
        4. Build HTML page
        5. Write artifact
        6. Return manual result

    This route does NOT produce a real videoUrl.
    It produces an HTML artifact that must be manually rendered via
    HeyGen HyperFrames plugin.
    """
    method_category = "hyperframes_html_render"
    raw_content = input_payload.get("content", "")
    target_duration = params.get("targetDuration", 45)
    all_logs = []
    all_warnings = []
    steps = []

    ensure_runtime_exists()

    # Step 1: receive input
    step1 = make_step(
        step_id=f"{experiment_id}_step_01_input",
        name="Receive Input",
        description="Parse raw input and validate content",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"Content length: {len(raw_content)} chars",
        output_summary="Validation passed",
        key_data={"inputLength": len(raw_content)},
        logs=["[1/5] Receive input", f"  Length: {len(raw_content)} chars"],
    )
    steps.append(step1)
    all_logs.extend(step1.logs)

    # Step 2: structure content
    if not raw_content:
        step2 = make_step(
            step_id=f"{experiment_id}_step_02_structure",
            name="Structure Content",
            description="Split raw text into structured format",
            status=ProductionStepStatus.FAILED,
            input_summary="Empty content",
            output_summary="Failed: content is required",
            logs=["[2/5] Structure content", "  ERROR: content is required"],
        )
        steps.append(step2)
        all_logs.extend(step2.logs)
        return _build_manual_result(experiment_id, method_category, steps, all_logs)

    structured = structure_content(raw_content, test_case_id)
    artifact_normalized = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_normalized",
        type=ArtifactType.NORMALIZED_CONTENT,
        title="Structured Content",
        summary=f"Lead + {structured.get('totalItems', 0)} items",
        payload=structured,
    )
    step2 = make_step(
        step_id=f"{experiment_id}_step_02_structure",
        name="Structure Content",
        description="Split raw text into structured format",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="Raw text",
        output_summary=f"Lead + {structured.get('totalItems', 0)} items",
        key_data={"leadLength": len(structured.get("lead", "")), "itemCount": structured.get("totalItems", 0)},
        logs=["[2/5] Structure content", f"  Items: {structured.get('totalItems', 0)}"],
        artifacts=[artifact_normalized],
    )
    steps.append(step2)
    all_logs.extend(step2.logs)

    # Step 3: extract key points
    key_points = extract_key_points(structured, target_duration)
    kps_list = key_points.get("keyPoints", key_points.get("key_points", []))
    key_points["keyPoints"] = kps_list
    key_points["key_points"] = kps_list

    artifact_kp = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_keypoints",
        type=ArtifactType.KEY_POINTS,
        title="Key Points",
        summary=f"{len(kps_list)} key points",
        payload=key_points,
    )
    step3 = make_step(
        step_id=f"{experiment_id}_step_03_keypoints",
        name="Extract Key Points",
        description="Extract key information points",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{structured.get('totalItems', 0)} content items",
        output_summary=f"{len(kps_list)} key points",
        key_data={"totalPoints": len(kps_list)},
        logs=["[3/5] Extract key points", f"  Points: {len(kps_list)}"],
        artifacts=[artifact_kp],
    )
    steps.append(step3)
    all_logs.extend(step3.logs)

    # Step 4: build HTML
    try:
        html_result = build_html(experiment_id, structured, key_points, params)
        all_warnings.extend(html_result.get("warnings", []))
    except Exception as e:
        step4 = make_step(
            step_id=f"{experiment_id}_step_04_html",
            name="Build HTML Page",
            description="Generate self-contained HTML page",
            status=ProductionStepStatus.FAILED,
            input_summary="structured + key_points",
            output_summary=f"Failed: {e}",
            logs=[f"[4/5] Build HTML", f"  ERROR: {e}"],
        )
        steps.append(step4)
        all_logs.extend(step4.logs)
        return _build_manual_result(experiment_id, method_category, steps, all_logs)

    artifact_html = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_html",
        type=ArtifactType.MANIFEST,
        title="HyperFrames HTML Artifact",
        summary=f"HTML: {html_result.get('htmlPath', '')}",
        payload={
            "htmlPath": html_result.get("htmlPath", ""),
            "htmlUrl": html_result.get("htmlUrl", ""),
            "title": html_result.get("title", ""),
            "keyPointCount": html_result.get("keyPointCount", 0),
        },
    )
    step4 = make_step(
        step_id=f"{experiment_id}_step_04_html",
        name="Build HTML Page",
        description="Generate self-contained HTML page for HeyGen HyperFrames",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="structured + key_points",
        output_summary=f"HTML: {html_result.get('htmlUrl', '')}",
        key_data={
            "htmlUrl": html_result.get("htmlUrl", ""),
            "keyPointCount": html_result.get("keyPointCount", 0),
        },
        logs=[
            f"[4/5] Build HTML",
            f"  Path: {html_result.get('htmlPath', '')}",
            f"  URL: {html_result.get('htmlUrl', '')}",
            f"  KeyPoints: {html_result.get('keyPointCount', 0)}",
        ],
        artifacts=[artifact_html],
    )
    steps.append(step4)
    all_logs.extend(step4.logs)

    # Step 5: write manifest
    manifest_path = get_experiment_dir(experiment_id) / "manifest.json"
    manifest_url = path_to_url(manifest_path)
    manifest = {
        "experimentId": experiment_id,
        "method": method_category,
        "engine": "hyperframes-html",
        "resolution": "1080x1920",
        "htmlUrl": html_result.get("htmlUrl", ""),
        "htmlPath": html_result.get("htmlPath", ""),
        "title": html_result.get("title", ""),
        "keyPointCount": html_result.get("keyPointCount", 0),
        "createdAt": datetime.utcnow().isoformat(),
        "manifestUrl": manifest_url,
        "routeMode": "manual",
        "requires": "HeyGen HyperFrames plugin",
        "nextAction": "Paste generated HTML into HeyGen HyperFrames plugin and render video",
    }
    write_manifest(experiment_id, manifest)

    manifest_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_manifest",
        type=ArtifactType.MANIFEST,
        title="Experiment Manifest",
        summary=f"Path: {manifest_path}",
        payload=manifest,
    )

    conclusion_payload = {
        "method": method_category,
        "engine": "hyperframes-html",
        "totalSteps": 5,
        "htmlUrl": html_result.get("htmlUrl", ""),
        "routeMode": "manual",
        "requires": "HeyGen HyperFrames plugin",
        "nextAction": "Paste HTML into HeyGen HyperFrames and render video",
        "warnings": all_warnings,
    }

    conclusion_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_conclusion",
        type=ArtifactType.EVALUATION,
        title="Conclusion",
        summary=f"Manual route: HTML artifact ready for HeyGen HyperFrames",
        payload=conclusion_payload,
    )

    step5 = make_step(
        step_id=f"{experiment_id}_step_05_conclusion",
        name="Generate Conclusion",
        description="Write manifest and finalize result",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="5 steps completed",
        output_summary=f"Manifest: {manifest_path.name}",
        key_data={
            "htmlUrl": html_result.get("htmlUrl", ""),
            "routeMode": "manual",
        },
        logs=["[5/5] Generate conclusion", "  HTML artifact ready for HeyGen HyperFrames"],
        artifacts=[manifest_artifact, conclusion_artifact],
    )
    steps.append(step5)
    all_logs.extend(step5.logs)

    all_logs.extend([
        "",
        "[HyperFrames HTML Route - Manual]",
        "  生成 HTML artifact，需人工复制到 HeyGen HyperFrames 插件",
        "  渲染后手动记录评分",
        "  优点: 视觉效果丰富，支持复杂 CSS 动画",
        "  限制: 需要人工操作，无法批量自动化",
    ])

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl="",
        coverUrl="",
        assets={
            "method": method_category,
            "engine": "hyperframes-html",
            "resolution": "1080x1920",
            "format": "html",
            "htmlUrl": html_result.get("htmlUrl", ""),
            "keyPointCount": html_result.get("keyPointCount", 0),
            "routeMode": "manual",
            "requires": "HeyGen HyperFrames plugin",
        },
        logs=all_logs,
        provider="HeyGen HyperFrames",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "engine": "hyperframes-html",
            "status": "manual_completed",
            "htmlUrl": html_result.get("htmlUrl", ""),
            "routeMode": "manual",
            "requires": "HeyGen HyperFrames plugin",
            "nextAction": "Paste HTML into HeyGen HyperFrames and render video",
            "riskAssessment": {
                "accuracy": "high - text precise and controllable",
                "stability": "medium - depends on manual operation",
                "visualAppeal": "high - CSS animations rich",
                "productization": "medium - requires manual step",
            },
            "productizationRecommendation": "manual_verification",
        },
        productionSteps=steps,
    )


def _build_manual_result(
    experiment_id: str,
    method_category: str,
    steps: list,
    logs: list,
) -> VideoExperimentResult:
    """Build a result for failed manual route."""
    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl="",
        coverUrl="",
        assets={"method": method_category, "status": "failed", "routeMode": "manual"},
        logs=logs,
        provider="HeyGen HyperFrames",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "engine": "hyperframes-html",
            "status": "manual_failed",
            "routeMode": "manual",
            "riskAssessment": {
                "accuracy": "n/a",
                "stability": "n/a",
                "visualAppeal": "n/a",
                "productization": "n/a",
            },
            "productizationRecommendation": "not_applicable",
        },
        productionSteps=steps,
    )
