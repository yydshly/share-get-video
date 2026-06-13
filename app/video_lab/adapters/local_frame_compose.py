"""
Adapter: local_frame_compose
Local image frame synthesis + FFmpeg - real rendering version
"""

from datetime import datetime
from pathlib import Path

from app.video_lab.models import (
    VideoExperimentResult,
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
from app.video_lab.renderers.file_store import (
    get_experiment_dir,
    get_frames_dir,
    ensure_runtime_exists,
    path_to_url,
    write_manifest,
)
from app.video_lab.renderers.local_frame_renderer import generate_frames
from app.video_lab.renderers.ffmpeg_composer import check_ffmpeg_available, compose_video_from_frames


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


def run_local_frame_compose(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    Real local frame synthesis with Pillow + FFmpeg.
    """
    method_category = "local_frame_compose"
    raw_content = input_payload.get("content", "")
    target_duration = params.get("targetDuration", 45)
    aspect_ratio = params.get("aspectRatio", "9:16")
    resolution = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)

    steps = []
    all_logs = []
    all_warnings = []

    # Ensure runtime directory exists
    ensure_runtime_exists()
    exp_dir = get_experiment_dir(experiment_id)
    frames_dir = get_frames_dir(experiment_id)

    # Step 1: receive input
    step1 = make_step(
        step_id=f"{experiment_id}_step_01_input",
        name="Receive Input",
        description="Parse raw input and validate content",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"Content length: {len(raw_content)} chars",
        output_summary="Validation passed",
        key_data={"inputLength": len(raw_content)},
        logs=["[1/12] Receive input", f"  Length: {len(raw_content)} chars", "  Status: passed"],
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
            logs=["[2/12] Structure content", "  ERROR: content is required"],
        )
        steps.append(step2)
        all_logs.extend(step2.logs)
        return _build_failed_result(experiment_id, method_category, steps, all_logs)

    structured = structure_content(raw_content, test_case_id)
    artifact_normalized = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_normalized",
        type=ArtifactType.NORMALIZED_CONTENT,
        title="Structured Content",
        summary=f"Lead + {structured['totalItems']} items",
        payload=structured,
    )
    step2 = make_step(
        step_id=f"{experiment_id}_step_02_structure",
        name="Structure Content",
        description="Split raw text into structured format",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="Raw text",
        output_summary=f"Lead + {structured['totalItems']} items",
        key_data={"leadLength": len(structured.get("lead", "")), "itemCount": structured.get("totalItems", 0)},
        logs=["[2/12] Structure content", f"  Items: {structured.get('totalItems', 0)}"],
        artifacts=[artifact_normalized],
    )
    steps.append(step2)
    all_logs.extend(step2.logs)

    # Step 3: extract key points
    key_points = extract_key_points(structured, target_duration)
    artifact_kp = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_keypoints",
        type=ArtifactType.KEY_POINTS,
        title="Key Points",
        summary=f"Selected {key_points.get('totalPoints', 0)} from {key_points.get('selectedFrom', 0)}",
        payload=key_points,
    )
    step3 = make_step(
        step_id=f"{experiment_id}_step_03_keypoints",
        name="Extract Key Points",
        description="Extract key information points based on target duration",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{structured['totalItems']} content items",
        output_summary=f"Selected {key_points['totalPoints']} key points",
        key_data={"totalPoints": key_points.get("totalPoints", 0), "selectedFrom": key_points.get("selectedFrom", 0)},
        logs=["[3/12] Extract key points", f"  Selected: {key_points.get('totalPoints', 0)}"],
        artifacts=[artifact_kp],
    )
    steps.append(step3)
    all_logs.extend(step3.logs)

    # Step 4: video strategy
    step4 = make_step(
        step_id=f"{experiment_id}_step_04_strategy",
        name="Determine Video Strategy",
        description="Decide video expression strategy based on test case type",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"Test case: {test_case_id}",
        output_summary="Structured info display strategy selected",
        key_data={"testCase": test_case_id, "strategy": "structured_info_display", "aspectRatio": aspect_ratio},
        logs=["[4/12] Determine video strategy", f"  Strategy: structured_info_display"],
    )
    steps.append(step4)
    all_logs.extend(step4.logs)

    # Step 5: select method
    step5 = make_step(
        step_id=f"{experiment_id}_step_05_method",
        name="Select Method",
        description=f"Route to local_frame_compose method",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="Waiting for method selection",
        output_summary="Method: local_frame_compose (Pillow + FFmpeg)",
        key_data={"methodCategory": method_category, "renderer": "Pillow + FFmpeg"},
        logs=["[5/12] Select method", f"  Method: {method_category}"],
    )
    steps.append(step5)
    all_logs.extend(step5.logs)

    # Step 6: generate script
    script = generate_script(key_points, aspect_ratio, target_duration)
    artifact_script = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_script",
        type=ArtifactType.SCRIPT,
        title="Video Script",
        summary=f"{script['totalSegments']} segments, estimated {script['estimatedDuration']}s",
        payload=script,
    )
    step6 = make_step(
        step_id=f"{experiment_id}_step_06_script",
        name="Generate Script",
        description="Generate video script from key points",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{key_points['totalPoints']} key points",
        output_summary=f"{script['totalSegments']} segments",
        key_data={"totalSegments": script.get("totalSegments", 0)},
        logs=["[6/12] Generate script", f"  Segments: {script.get('totalSegments', 0)}"],
        artifacts=[artifact_script],
    )
    steps.append(step6)
    all_logs.extend(step6.logs)

    # Step 7: generate storyboard
    storyboard = generate_storyboard(script, method_category)
    artifact_sb = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_storyboard",
        type=ArtifactType.STORYBOARD,
        title="Storyboard",
        summary=f"{storyboard['totalFrames']} frames",
        payload=storyboard,
    )
    step7 = make_step(
        step_id=f"{experiment_id}_step_07_storyboard",
        name="Generate Storyboard",
        description="Convert script to frame descriptions",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{script['totalSegments']} script segments",
        output_summary=f"{storyboard['totalFrames']} frames",
        key_data={"totalFrames": storyboard.get("totalFrames", 0)},
        logs=["[7/12] Generate storyboard", f"  Frames: {storyboard.get('totalFrames', 0)}"],
        artifacts=[artifact_sb],
    )
    steps.append(step7)
    all_logs.extend(step7.logs)

    # Step 8: subtitle/text plan
    subtitle_plan = generate_subtitle_plan(script, include_voiceover=False)
    voiceover_plan = generate_voiceover_plan(script)
    artifact_sub = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_subtitle",
        type=ArtifactType.SUBTITLE_PLAN,
        title="Subtitle Plan",
        summary=f"{subtitle_plan['totalSegments']} subtitle segments",
        payload=subtitle_plan,
    )
    artifact_vo = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_voiceover",
        type=ArtifactType.VOICEOVER_PLAN,
        title="Voiceover Plan",
        summary=f"{voiceover_plan['totalSegments']} voiceover segments",
        payload=voiceover_plan,
    )
    step8 = make_step(
        step_id=f"{experiment_id}_step_08_subtitle",
        name="Generate Text Plan",
        description="Plan text burning into frames",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{script['totalSegments']} script segments",
        output_summary=f"{subtitle_plan['totalSegments']} subtitle segments (text burn-in)",
        key_data={"subtitleSegments": subtitle_plan.get("totalSegments", 0)},
        logs=["[8/12] Generate text plan", "  Method: Pillow text burn-in"],
        artifacts=[artifact_sub, artifact_vo],
    )
    steps.append(step8)
    all_logs.extend(step8.logs)

    # Step 9: asset plan
    step9 = make_step(
        step_id=f"{experiment_id}_step_09_assets",
        name="Plan Frame Assets",
        description="Plan frame sequence: cover + keypoint frames + summary",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{key_points['totalPoints']} key points",
        output_summary=f"Plan {key_points.get('totalPoints', 0) + 2} frames",
        key_data={"estimatedFrames": key_points.get("totalPoints", 0) + 2, "renderer": "Pillow", "outputFormat": "PNG"},
        logs=["[9/12] Plan frame assets", f"  Frames: {key_points.get('totalPoints', 0) + 2}"],
    )
    steps.append(step9)
    all_logs.extend(step9.logs)

    # Step 10: Pillow generate PNG frames
    frame_result = generate_frames(
        experiment_id=experiment_id,
        structured=structured,
        key_points=key_points,
        target_duration_sec=target_duration,
        resolution=resolution,
    )

    frame_artifacts = []
    for frame in frame_result.get("frames", []):
        frame_path = Path(frame["path"]) if isinstance(frame["path"], str) else frame["path"]
        frame_artifacts.append(
            VideoProductionArtifact(
                artifact_id=f"{experiment_id}_art_frame_{frame.get('frame_name', frame.get('type', 'unknown'))}",
                type=ArtifactType.FRAME_IMAGE,
                title=f"Frame: {frame.get('frame_name', frame.get('type', 'unknown'))}",
                summary=f"Path: {frame['path']}",
                payload={"path": str(frame["path"]), "url": path_to_url(frame_path), "type": frame.get("type")},
            )
        )
    all_warnings.extend(frame_result.get("warnings", []))

    cover_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_cover",
        type=ArtifactType.COVER_IMAGE,
        title="Cover Frame",
        summary=f"Path: {frame_result.get('cover')}",
        payload={
            "path": str(frame_result.get("cover")),
            "url": path_to_url(frame_result.get("cover", "")) if frame_result.get("cover") else "",
            "type": "cover",
        },
    )
    frame_artifacts.append(cover_artifact)

    step10 = make_step(
        step_id=f"{experiment_id}_step_10_pillow",
        name="Pillow Generate PNG Frames",
        description="Generate info card PNG frames with Pillow",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"Target {target_duration}s, resolution {resolution}",
        output_summary=f"Generated {frame_result['total_frames']} frames",
        key_data={
            "totalFrames": frame_result.get("total_frames", 0),
            "resolution": f"{resolution[0]}x{resolution[1]}",
            "totalDurationSec": frame_result.get("total_duration_sec", 0),
        },
        logs=[
            "[10/12] Pillow generate PNG frames",
            f"  Frames: {frame_result.get('total_frames', 0)}",
            f"  Resolution: {resolution[0]}x{resolution[1]}",
            f"  Output: {frames_dir}",
        ],
        artifacts=frame_artifacts,
    )
    steps.append(step10)
    all_logs.extend(step10.logs)

    # Step 11: FFmpeg compose MP4
    output_mp4 = exp_dir / "output.mp4"
    ffmpeg_result = compose_video_from_frames(
        frames_dir=frames_dir,
        output_path=output_mp4,
        duration_per_frame=frame_result.get("duration_per_frame", {}),
        fps=30,
        resolution=resolution,
        timeout=300,
    )

    video_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_video",
        type=ArtifactType.VIDEO_OUTPUT,
        title="Output Video",
        summary=f"Path: {output_mp4}",
        payload={"path": str(output_mp4), "url": path_to_url(output_mp4), "ffmpegSuccess": ffmpeg_result.get("success", False)},
    )

    if ffmpeg_result.get("success"):
        step11 = make_step(
            step_id=f"{experiment_id}_step_11_ffmpeg",
            name="FFmpeg Compose MP4",
            description="Compose MP4 using FFmpeg concat demuxer",
            status=ProductionStepStatus.SUCCEEDED,
            input_summary=f"{frame_result['total_frames']} frames",
            output_summary=f"Success: {output_mp4.name}",
            key_data={
                "ffmpegVersion": ffmpeg_result.get("version", "unknown"),
                "outputPath": str(output_mp4),
                "outputUrl": path_to_url(output_mp4),
                "ffmpegCommand": ffmpeg_result.get("ffmpeg_command", ""),
                "ffmpegMessage": ffmpeg_result.get("message", ""),
            },
            logs=[
                "[11/12] FFmpeg compose MP4",
                f"  FFmpeg: {ffmpeg_result.get('version', 'unknown')}",
                f"  Output: {output_mp4.name}",
            ],
            artifacts=[video_artifact],
        )
    else:
        step11 = make_step(
            step_id=f"{experiment_id}_step_11_ffmpeg",
            name="FFmpeg Compose MP4",
            description="FFmpeg composition failed",
            status=ProductionStepStatus.FAILED,
            input_summary=f"{frame_result['total_frames']} frames",
            output_summary=f"FFmpeg failed: {str(ffmpeg_result.get('message', 'unknown error'))[:100]}",
            key_data={
                "ffmpegVersion": ffmpeg_result.get("version", "not_found"),
                "error": ffmpeg_result.get("message", "unknown error"),
                "ffmpegCommand": ffmpeg_result.get("ffmpeg_command", ""),
                "ffmpegMessage": ffmpeg_result.get("message", ""),
            },
            logs=[
                "[11/12] FFmpeg compose MP4",
                f"  ERROR: {str(ffmpeg_result.get('message', 'unknown error'))[:200]}",
            ],
            artifacts=[video_artifact],
        )

    steps.append(step11)
    all_logs.extend(step11.logs)

    # Step 12: conclusion and manifest
    # Compute path before building dict so manifestUrl is IN the written file
    manifest_path = get_experiment_dir(experiment_id) / "manifest.json"
    manifest_url = path_to_url(manifest_path)
    manifest = {
        "experimentId": experiment_id,
        "method": method_category,
        "resolution": f"{resolution[0]}x{resolution[1]}",
        "fps": 30,
        "durationSec": frame_result.get("total_duration_sec", target_duration),
        "totalFrames": frame_result.get("total_frames", 0),
        "frameCount": len(frame_result.get("frames", [])),
        "outputVideo": str(output_mp4),
        "outputVideoUrl": path_to_url(output_mp4),
        "cover": str(frame_result.get("cover", "")),
        "coverUrl": path_to_url(frame_result.get("cover", "")) if frame_result.get("cover") else "",
        "createdAt": datetime.utcnow().isoformat(),
        "ffmpegSuccess": ffmpeg_result.get("success", False),
        "ffmpegVersion": ffmpeg_result.get("version", "unknown"),
        "ffmpegCommand": ffmpeg_result.get("ffmpeg_command", ""),
        "ffmpegMessage": ffmpeg_result.get("message", ""),
        "warnings": all_warnings,
        "manifestUrl": manifest_url,
    }
    write_manifest(experiment_id, manifest)

    manifest_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_manifest",
        type=ArtifactType.MANIFEST,
        title="Experiment Manifest",
        summary=f"Path: {manifest_path}",
        payload=manifest,
    )

    succeeded_count = sum(1 for s in steps if s.status == ProductionStepStatus.SUCCEEDED)
    conclusion_payload = {
        "method": method_category,
        "totalSteps": 12,
        "succeededSteps": succeeded_count,
        "recommendation": "recommended" if ffmpeg_result.get("success") else "failed",
        "ffmpegSuccess": ffmpeg_result.get("success", False),
        "warnings": all_warnings,
        "nextVersion": "V0.2.1: optimize local video aesthetics",
    }

    conclusion_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_conclusion",
        type=ArtifactType.EVALUATION,
        title="Conclusion",
        summary=f"Completed {succeeded_count}/12 steps",
        payload=conclusion_payload,
    )

    step12 = make_step(
        step_id=f"{experiment_id}_step_12_conclusion",
        name="Generate Conclusion",
        description="Summarize experiment results and write manifest",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="12 steps completed",
        output_summary=f"Manifest: {manifest_path.name}",
        key_data={"succeededSteps": succeeded_count, "ffmpegSuccess": ffmpeg_result.get("success", False)},
        logs=[
            "[12/12] Generate conclusion",
            f"  Steps: {succeeded_count}/12",
            f"  FFmpeg: {'success' if ffmpeg_result.get('success') else 'failed'}",
            f"  Manifest: {manifest_path.name}",
        ],
        artifacts=[manifest_artifact, conclusion_artifact],
    )
    steps.append(step12)
    all_logs.extend(step12.logs)

    all_logs.extend([
        "",
        "[Method Characteristics]",
        "  Cost: low | Control: high | Stability: high | Productization: high",
        "  Suitable: structured info display, text cards, captions",
        "  Not suitable: high realism, creative motion",
    ])

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=path_to_url(output_mp4) if ffmpeg_result.get("success") else "",
        coverUrl=path_to_url(frame_result.get("cover", "")) if frame_result.get("cover") else "",
        assets={
            "frameCount": frame_result.get("total_frames", 0),
            "fps": 30,
            "resolution": f"{resolution[0]}x{resolution[1]}",
            "format": "mp4",
            "codec": "libx264",
            "method": method_category,
            "ffmpegSuccess": ffmpeg_result.get("success", False),
        },
        logs=all_logs,
        provider="Pillow + FFmpeg",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "frameEngine": "Pillow",
            "synthesizer": "FFmpeg",
            "status": "real_success" if ffmpeg_result.get("success") else "ffmpeg_failed",
            "ffmpegVersion": ffmpeg_result.get("version", "unknown"),
            "ffmpegSuccess": ffmpeg_result.get("success", False),
            "warnings": all_warnings,
            "riskAssessment": {
                "accuracy": "high - text precise and controllable",
                "stability": "high - batch consistent",
                "visualAppeal": "medium - limited visual ceiling",
                "productization": "high - low cost, easy to scale",
            },
            "productizationRecommendation": "recommended" if ffmpeg_result.get("success") else "failed",
        },
        productionSteps=steps,
    )


def _build_failed_result(experiment_id: str, method_category: str, steps: list, logs: list) -> VideoExperimentResult:
    """Build a failed result."""
    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl="",
        coverUrl="",
        assets={"method": method_category, "status": "failed"},
        logs=logs,
        provider="Pillow + FFmpeg",
        adapter=method_category,
        rawOutput={
            "method": method_category,
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
