"""
Adapter: template_programmatic_render
Remotion 程序化模板渲染 - V0.3.1 real implementation
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
from app.video_lab.renderers.remotion.props_builder import build_remotion_props
from app.video_lab.renderers.remotion.remotion_renderer import (
    render_remotion_video,
    check_remotion_available,
)


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


def run_remotion_template(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    Real Remotion programmatic template rendering.
    V0.3.1: Minimum verification - renders MP4 via npx remotion render.

    Flow:
        1. Receive input
        2. Structure content
        3. Extract key points
        4. Build Remotion props JSON
        5. Run Remotion render (npx remotion render)
        6. Write manifest
        7. Return VideoExperimentResult
    """
    method_category = "template_programmatic_render"
    raw_content = input_payload.get("content", "")
    target_duration = params.get("targetDuration", 45)
    all_logs = []
    all_warnings = []
    steps = []

    ensure_runtime_exists()
    exp_dir = get_experiment_dir(experiment_id)

    # Step 1: receive input
    step1 = make_step(
        step_id=f"{experiment_id}_step_01_input",
        name="Receive Input",
        description="Parse raw input and validate content",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"Content length: {len(raw_content)} chars",
        output_summary="Validation passed",
        key_data={"inputLength": len(raw_content)},
        logs=["[1/7] Receive input", f"  Length: {len(raw_content)} chars", "  Status: passed"],
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
            logs=["[2/7] Structure content", "  ERROR: content is required"],
        )
        steps.append(step2)
        all_logs.extend(step2.logs)
        return _build_failed_result(experiment_id, method_category, steps, all_logs)

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
        key_data={
            "leadLength": len(structured.get("lead", "")),
            "itemCount": structured.get("totalItems", 0),
        },
        logs=["[2/7] Structure content", f"  Items: {structured.get('totalItems', 0)}"],
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
        logs=["[3/7] Extract key points", f"  Points: {len(kps_list)}"],
        artifacts=[artifact_kp],
    )
    steps.append(step3)
    all_logs.extend(step3.logs)

    # Step 4: build Remotion props
    try:
        remotion_props = build_remotion_props(experiment_id, structured, key_points, params)
        all_logs.append(f"[4/7] Build Remotion props: {len(kps_list)} keypoints, {remotion_props.get('durationSec', 45)}s")
    except Exception as e:
        step4 = make_step(
            step_id=f"{experiment_id}_step_04_props",
            name="Build Remotion Props",
            description="Build Remotion props JSON",
            status=ProductionStepStatus.FAILED,
            input_summary="structured + key_points",
            output_summary=f"Failed: {e}",
            logs=[f"[4/7] Build Remotion props", f"  ERROR: {e}"],
        )
        steps.append(step4)
        all_logs.extend(step4.logs)
        return _build_failed_result(experiment_id, method_category, steps, all_logs)

    artifact_props = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_props",
        type=ArtifactType.MANIFEST,
        title="Remotion Props",
        summary=f"title={remotion_props.get('title')}, {len(remotion_props.get('keyPoints', []))} keyPoints",
        payload=remotion_props,
    )
    step4 = make_step(
        step_id=f"{experiment_id}_step_04_props",
        name="Build Remotion Props",
        description="Build Remotion props JSON for AiNewsVideo template",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="structured + key_points + params",
        output_summary=f"title={remotion_props.get('title')}, {len(remotion_props.get('keyPoints', []))} keyPoints",
        key_data={
            "title": remotion_props.get("title"),
            "subtitle": remotion_props.get("subtitle"),
            "keyPointCount": len(remotion_props.get("keyPoints", [])),
            "durationSec": remotion_props.get("durationSec", 45),
            "stylePreset": remotion_props.get("stylePreset"),
        },
        logs=[
            f"[4/7] Build Remotion props",
            f"  title: {remotion_props.get('title')}",
            f"  keyPoints: {len(remotion_props.get('keyPoints', []))}",
            f"  durationSec: {remotion_props.get('durationSec', 45)}",
        ],
        artifacts=[artifact_props],
    )
    steps.append(step4)
    all_logs.extend(step4.logs)

    # Step 5: check Remotion environment
    env_available, env_msg = check_remotion_available()
    if not env_available:
        step5 = make_step(
            step_id=f"{experiment_id}_step_05_env",
            name="Check Remotion Environment",
            description="Verify Node.js / npx remotion availability",
            status=ProductionStepStatus.FAILED,
            input_summary="node + npx + remotion",
            output_summary=f"Environment not available: {env_msg}",
            logs=[f"[5/7] Check Remotion environment", f"  ERROR: {env_msg}"],
        )
        steps.append(step5)
        all_logs.extend(step5.logs)
        all_warnings.append(env_msg)
        return _build_failed_result(
            experiment_id,
            method_category,
            steps,
            all_logs,
            extra_warnings=[env_msg],
        )

    step5 = make_step(
        step_id=f"{experiment_id}_step_05_env",
        name="Check Remotion Environment",
        description="Verify Node.js / npx remotion availability",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="node + npx + remotion",
        output_summary="Remotion environment available",
        logs=["[5/7] Check Remotion environment", "  OK: Remotion environment available"],
    )
    steps.append(step5)
    all_logs.extend(step5.logs)

    # Step 6: run Remotion render
    render_result = render_remotion_video(experiment_id, remotion_props, timeout=300)

    if render_result.get("success"):
        step6 = make_step(
            step_id=f"{experiment_id}_step_06_render",
            name="Remotion Render",
            description="Execute npx remotion render to generate MP4",
            status=ProductionStepStatus.SUCCEEDED,
            input_summary="remotion_props.json",
            output_summary=f"Success: {render_result.get('videoUrl', '')}",
            key_data={
                "videoUrl": render_result.get("videoUrl", ""),
                "manifestUrl": render_result.get("manifestUrl", ""),
            },
            logs=render_result.get("logs", []),
        )
    else:
        step6 = make_step(
            step_id=f"{experiment_id}_step_06_render",
            name="Remotion Render",
            description="Execute npx remotion render to generate MP4",
            status=ProductionStepStatus.FAILED,
            input_summary="remotion_props.json",
            output_summary=f"Failed: {render_result.get('message', 'unknown error')}",
            logs=render_result.get("logs", []),
        )
        all_warnings.extend(render_result.get("warnings", []))

    steps.append(step6)
    all_logs.extend(step6.logs)

    video_url = render_result.get("videoUrl", "")
    manifest_url = render_result.get("manifestUrl", "")

    # Step 7: write manifest and conclusion
    manifest = {
        "experimentId": experiment_id,
        "method": method_category,
        "engine": "remotion",
        "resolution": "1080x1920",
        "fps": 30,
        "durationSec": remotion_props.get("durationSec", 45),
        "stylePreset": remotion_props.get("stylePreset", "ai_frontier_dark"),
        "outputVideoUrl": video_url,
        "coverUrl": "",
        "props": remotion_props,
        "createdAt": datetime.utcnow().isoformat(),
        "renderSuccess": render_result.get("success", False),
        "renderMessage": render_result.get("message", ""),
        "manifestUrl": manifest_url,
    }
    manifest_path = write_manifest(experiment_id, manifest)
    manifest_url = path_to_url(manifest_path)

    manifest_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_manifest",
        type=ArtifactType.MANIFEST,
        title="Experiment Manifest",
        summary=f"Path: {manifest_path}",
        payload=manifest,
    )

    conclusion_payload = {
        "method": method_category,
        "engine": "remotion",
        "totalSteps": 7,
        "renderSuccess": render_result.get("success", False),
        "warnings": all_warnings,
        "renderMessage": render_result.get("message", ""),
    }

    conclusion_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_conclusion",
        type=ArtifactType.EVALUATION,
        title="Conclusion",
        summary=f"Remotion render {'succeeded' if video_url else 'failed'}",
        payload=conclusion_payload,
    )

    step7 = make_step(
        step_id=f"{experiment_id}_step_07_conclusion",
        name="Generate Conclusion",
        description="Write manifest and finalize result",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="7 steps completed",
        output_summary=f"Manifest: {manifest_path.name}",
        key_data={
            "renderSuccess": render_result.get("success", False),
            "videoUrl": video_url,
            "manifestUrl": manifest_url,
        },
        logs=[
            "[7/7] Generate conclusion",
            f"  VideoUrl: {video_url}",
            f"  ManifestUrl: {manifest_url}",
            f"  Render success: {render_result.get('success', False)}",
        ],
        artifacts=[manifest_artifact, conclusion_artifact],
    )
    steps.append(step7)
    all_logs.extend(step7.logs)

    # Asset info
    assets = {
        "method": method_category,
        "engine": "remotion",
        "resolution": "1080x1920",
        "fps": 30,
        "format": "mp4",
        "codec": "h264",
        "durationSec": remotion_props.get("durationSec", 45),
        "keyPointCount": len(remotion_props.get("keyPoints", [])),
        "stylePreset": remotion_props.get("stylePreset", "ai_frontier_dark"),
        "renderSuccess": render_result.get("success", False),
        "renderMessage": render_result.get("message", ""),
        "routeReal": True,
    }

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=video_url,
        coverUrl="",
        assets=assets,
        logs=all_logs,
        provider="Remotion",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "engine": "remotion",
            "stack": ["React", "Remotion", "FFmpeg"],
            "status": "real_success" if video_url else "real_failed",
            "renderResult": render_result,
            "riskAssessment": {
                "accuracy": "high - text precise via React templates",
                "stability": "medium - depends on Node/Chrome environment",
                "visualAppeal": "high - React animations and transitions",
                "productization": "high - batch cost very low",
            },
            "productizationRecommendation": "recommended" if video_url else "failed",
        },
        productionSteps=steps,
    )


def _build_failed_result(
    experiment_id: str,
    method_category: str,
    steps: list,
    logs: list,
    extra_warnings: list = None,
) -> VideoExperimentResult:
    """Build a failed result."""
    warnings = list(extra_warnings or [])
    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl="",
        coverUrl="",
        assets={
            "method": method_category,
            "engine": "remotion",
            "status": "failed",
            "routeReal": True,
        },
        logs=logs,
        provider="Remotion",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "engine": "remotion",
            "status": "failed",
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
