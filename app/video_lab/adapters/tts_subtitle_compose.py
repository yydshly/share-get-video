"""
Adapter: tts_subtitle_compose
MiniMax TTS + 字幕 + 视频合成 - V0.3.3 Real Route

Flow:
    1. Receive input
    2. Structure content
    3. Extract key points
    4. Generate voiceover plan
    5. MiniMax TTS generate audio
    6. Generate SRT subtitles
    7. Generate silent video (via local_frame_renderer)
    8. FFmpeg compose audio + subtitles
    9. Output MP4
    10. Write manifest
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
from app.video_lab.planners.voiceover_planner import generate_voiceover
from app.video_lab.planners.subtitle_planner import generate_srt_from_segments
from app.video_lab.providers.minimax import MiniMaxTTSClient, MiniMaxTTSError
from app.video_lab.renderers.file_store import (
    get_experiment_dir,
    ensure_runtime_exists,
    path_to_url,
    write_manifest,
)
from app.video_lab.renderers.local_frame_renderer import generate_frames
from app.video_lab.renderers.ffmpeg_av_composer import compose_av_with_subtitles, check_ffmpeg_available
from app.video_lab.renderers.render_params import parse_local_frame_params, resolve_resolution


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


def run_tts_subtitle_compose(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    TTS + Subtitle + Video composition adapter.
    V0.3.3: Uses MiniMax TTS for voiceover generation.
    """
    method_category = "tts_subtitle_compose"
    raw_content = input_payload.get("content", "")

    parse_result = parse_local_frame_params(params)
    if not parse_result.is_valid:
        step_err = make_step(
            step_id=f"{experiment_id}_step_00_params",
            name="Parse Parameters",
            description="Validate render parameters",
            status=ProductionStepStatus.FAILED,
            input_summary="Raw params",
            output_summary=f"Parameter error: {parse_result.error}",
            logs=[f"[0/?] Parse parameters", f"  ERROR: {parse_result.error}"],
        )
        return _build_failed_result(experiment_id, method_category, [step_err], parse_result.error)

    render_params = parse_result.params
    target_duration = render_params.target_duration
    aspect_ratio = render_params.aspect_ratio
    resolution = resolve_resolution(aspect_ratio)

    steps = []
    all_logs = []
    all_warnings: list[str] = []
    tts_client = MiniMaxTTSClient()

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
        logs=["[1/9] Receive input", f"  Length: {len(raw_content)} chars"],
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
            logs=["[2/9] Structure content", "  ERROR: content is required"],
        )
        steps.append(step2)
        all_logs.extend(step2.logs)
        return _build_failed_result(experiment_id, method_category, steps, "content is required")

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
        logs=["[2/9] Structure content", f"  Items: {structured.get('totalItems', 0)}"],
        artifacts=[artifact_normalized],
    )
    steps.append(step2)
    all_logs.extend(step2.logs)

    # Step 3: extract key points
    key_points = extract_key_points(structured, target_duration)
    kps_list = key_points.get("keyPoints", [])
    if len(kps_list) > render_params.key_point_count:
        kps_list = kps_list[: render_params.key_point_count]
    key_points["keyPoints"] = kps_list
    key_points["key_points"] = kps_list
    key_points["totalPoints"] = len(kps_list)

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
        logs=["[3/9] Extract key points", f"  Points: {len(kps_list)}"],
        artifacts=[artifact_kp],
    )
    steps.append(step3)
    all_logs.extend(step3.logs)

    # Step 4: generate voiceover plan
    voiceover_result = generate_voiceover(structured, key_points, target_duration)
    artifact_vo = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_voiceover",
        type=ArtifactType.VOICEOVER_PLAN,
        title="Voiceover Plan",
        summary=f"{len(voiceover_result.get('segments', []))} segments, ~{voiceover_result.get('estimatedDurationSec', 0)}s",
        payload=voiceover_result,
    )
    step4 = make_step(
        step_id=f"{experiment_id}_step_04_voiceover",
        name="Generate Voiceover Plan",
        description="Generate voiceover script from key points",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{len(kps_list)} key points",
        output_summary=f"Estimated {voiceover_result.get('estimatedDurationSec', 0)}s",
        key_data={
            "estimatedDurationSec": voiceover_result.get("estimatedDurationSec", 0),
            "segmentCount": len(voiceover_result.get("segments", [])),
        },
        logs=["[4/9] Generate voiceover plan", f"  Segments: {len(voiceover_result.get('segments', []))}"],
        artifacts=[artifact_vo],
    )
    steps.append(step4)
    all_logs.extend(step4.logs)

    # Step 5: MiniMax TTS generate audio
    voiceover_text = voiceover_result.get("voiceoverText", "")
    audio_dir = exp_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / "voiceover.mp3"

    if not tts_client.is_configured():
        step5 = make_step(
            step_id=f"{experiment_id}_step_05_tts",
            name="MiniMax TTS Generate Audio",
            description="Call MiniMax TTS API to generate voiceover audio",
            status=ProductionStepStatus.FAILED,
            input_summary="Voiceover text length",
            output_summary="Failed: MINIMAX_API_KEY not set",
            key_data={"apiKeySet": False, "error": "Missing MINIMAX_API_KEY"},
            logs=["[5/9] MiniMax TTS", "  ERROR: MINIMAX_API_KEY not configured"],
        )
        steps.append(step5)
        all_logs.extend(step5.logs)
        return _build_failed_result(experiment_id, method_category, steps, "MINIMAX_API_KEY not configured")

    tts_result = tts_client.generate(
        text=voiceover_text,
        output_path=audio_path,
    )

    if not tts_result.get("success"):
        step5 = make_step(
            step_id=f"{experiment_id}_step_05_tts",
            name="MiniMax TTS Generate Audio",
            description="Call MiniMax TTS API to generate voiceover audio",
            status=ProductionStepStatus.FAILED,
            input_summary=f"Voiceover text: {len(voiceover_text)} chars",
            output_summary=f"Failed: {tts_result.get('providerMessage', 'unknown')}",
            key_data={
                "apiKeySet": True,
                "success": False,
                "error": tts_result.get("providerMessage", ""),
            },
            logs=[
                "[5/9] MiniMax TTS",
                f"  ERROR: {tts_result.get('providerMessage', 'unknown')}",
            ],
        )
        steps.append(step5)
        all_logs.extend(step5.logs)
        return _build_failed_result(experiment_id, method_category, steps, tts_result.get("providerMessage", "TTS failed"))

    artifact_audio = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_audio",
        type=ArtifactType.VOICEOVER_PLAN,
        title="Voiceover Audio",
        summary=f"Duration: {tts_result.get('durationSec', 0)}s",
        payload={
            "path": tts_result.get("audioPath", ""),
            "url": path_to_url(Path(tts_result.get("audioPath", ""))),
            "durationSec": tts_result.get("durationSec", 0),
        },
    )
    step5 = make_step(
        step_id=f"{experiment_id}_step_05_tts",
        name="MiniMax TTS Generate Audio",
        description="Call MiniMax TTS API to generate voiceover audio",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"Voiceover text: {len(voiceover_text)} chars",
        output_summary=f"Success: {tts_result.get('durationSec', 0)}s audio",
        key_data={
            "apiKeySet": True,
            "success": True,
            "durationSec": tts_result.get("durationSec", 0),
            "providerMessage": tts_result.get("providerMessage", ""),
        },
        logs=[
            "[5/9] MiniMax TTS",
            f"  Duration: {tts_result.get('durationSec', 0)}s",
            f"  Path: {tts_result.get('audioPath', '')}",
        ],
        artifacts=[artifact_audio],
    )
    steps.append(step5)
    all_logs.extend(step5.logs)

    # Step 6: generate SRT subtitles
    segments = voiceover_result.get("segments", [])
    subtitle_dir = exp_dir / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    srt_path = subtitle_dir / "subtitles.srt"

    srt_result = generate_srt_from_segments(segments, output_path=srt_path)
    artifact_srt = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_srt",
        type=ArtifactType.SUBTITLE_PLAN,
        title="Subtitle SRT",
        summary=f"{len(srt_result.get('subtitles', []))} subtitle entries",
        payload={
            "path": srt_result.get("srtPath", ""),
            "url": srt_result.get("srtUrl", ""),
            "subtitleCount": len(srt_result.get("subtitles", [])),
        },
    )
    step6 = make_step(
        step_id=f"{experiment_id}_step_06_subtitles",
        name="Generate SRT Subtitles",
        description="Generate SRT subtitle file from voiceover segments",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{len(segments)} voiceover segments",
        output_summary=f"{len(srt_result.get('subtitles', []))} subtitle entries",
        key_data={"subtitleCount": len(srt_result.get("subtitles", []))},
        logs=["[6/9] Generate SRT subtitles", f"  Subtitles: {len(srt_result.get('subtitles', []))}"],
        artifacts=[artifact_srt],
    )
    steps.append(step6)
    all_logs.extend(step6.logs)

    # Step 7: generate silent video (reusing local_frame_renderer)
    frame_result = generate_frames(
        experiment_id=experiment_id,
        structured=structured,
        key_points=key_points,
        target_duration_sec=target_duration,
        resolution=resolution,
        enable_transitions=render_params.transition_enabled,
        transition_frames=render_params.transition_frames,
        highlight_mode=render_params.highlight_mode,
        include_overview=render_params.include_overview,
        include_summary=render_params.include_summary,
    )
    all_warnings.extend(frame_result.get("warnings", []))

    silent_video_path = exp_dir / "silent.mp4"
    frame_sequence = frame_result.get("frameSequence", [])
    duration_by_path = frame_result.get("durationByPath", {})

    from app.video_lab.renderers.ffmpeg_composer import compose_video_from_frame_sequence
    if frame_sequence and len(frame_sequence) > 0:
        ffmpeg_result = compose_video_from_frame_sequence(
            frame_sequence=frame_sequence,
            output_path=silent_video_path,
            duration_by_path=duration_by_path,
            fps=30,
            resolution=resolution,
            timeout=300,
        )
    else:
        from app.video_lab.renderers.file_store import get_frames_dir
        frames_dir = get_frames_dir(experiment_id)
        from app.video_lab.renderers.ffmpeg_composer import compose_video_from_frames
        ffmpeg_result = compose_video_from_frames(
            frames_dir=frames_dir,
            output_path=silent_video_path,
            duration_per_frame=frame_result.get("duration_per_frame", {}),
            fps=30,
            resolution=resolution,
            timeout=300,
        )

    if not ffmpeg_result.get("success"):
        step7 = make_step(
            step_id=f"{experiment_id}_step_07_silent_video",
            name="Generate Silent Video",
            description="Generate silent video from frames using Pillow + FFmpeg",
            status=ProductionStepStatus.FAILED,
            input_summary="Frames from local_frame_renderer",
            output_summary=f"FFmpeg failed: {ffmpeg_result.get('message', '')}",
            key_data={"ffmpegSuccess": False, "error": ffmpeg_result.get("message", "")},
            logs=["[7/9] Generate silent video", f"  ERROR: {ffmpeg_result.get('message', '')}"],
        )
        steps.append(step7)
        all_logs.extend(step7.logs)
        return _build_failed_result(experiment_id, method_category, steps, ffmpeg_result.get("message", "FFmpeg failed"))

    artifact_silent = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_silent",
        type=ArtifactType.VIDEO_OUTPUT,
        title="Silent Video",
        summary=f"Path: {silent_video_path}",
        payload={"path": str(silent_video_path), "url": path_to_url(silent_video_path)},
    )
    step7 = make_step(
        step_id=f"{experiment_id}_step_07_silent_video",
        name="Generate Silent Video",
        description="Generate silent video from frames using Pillow + FFmpeg",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="Frames from local_frame_renderer",
        output_summary=f"Success: {silent_video_path.name}",
        key_data={"ffmpegSuccess": True, "frameCount": frame_result.get("total_frames", 0)},
        logs=["[7/9] Generate silent video", f"  Frames: {frame_result.get('total_frames', 0)}", f"  Output: {silent_video_path.name}"],
        artifacts=[artifact_silent],
    )
    steps.append(step7)
    all_logs.extend(step7.logs)

    # Step 8: FFmpeg compose final with audio + subtitles
    if not check_ffmpeg_available():
        step8 = make_step(
            step_id=f"{experiment_id}_step_08_av_compose",
            name="FFmpeg AV Composition",
            description="Combine silent video + audio + subtitles",
            status=ProductionStepStatus.FAILED,
            input_summary="silent video + audio + srt",
            output_summary="Failed: FFmpeg not available",
            key_data={"ffmpegAvailable": False},
            logs=["[8/9] FFmpeg AV composition", "  ERROR: FFmpeg not available"],
        )
        steps.append(step8)
        all_logs.extend(step8.logs)
        return _build_failed_result(experiment_id, method_category, steps, "FFmpeg not available")

    final_output = exp_dir / "final_with_audio.mp4"
    av_result = compose_av_with_subtitles(
        video_path=silent_video_path,
        audio_path=audio_path,
        srt_path=srt_path,
        output_path=final_output,
        resolution=resolution,
        timeout=300,
    )

    if not av_result.get("success"):
        step8 = make_step(
            step_id=f"{experiment_id}_step_08_av_compose",
            name="FFmpeg AV Composition",
            description="Combine silent video + audio + subtitles",
            status=ProductionStepStatus.FAILED,
            input_summary="silent video + audio + srt",
            output_summary=f"FFmpeg AV failed: {av_result.get('message', '')}",
            key_data={"success": False, "error": av_result.get("message", "")},
            logs=["[8/9] FFmpeg AV composition", f"  ERROR: {av_result.get('message', '')}"],
        )
        steps.append(step8)
        all_logs.extend(step8.logs)
        return _build_failed_result(experiment_id, method_category, steps, av_result.get("message", "FFmpeg AV failed"))

    artifact_final = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_final",
        type=ArtifactType.VIDEO_OUTPUT,
        title="Final Video with Audio",
        summary=f"Path: {final_output}",
        payload={"path": str(final_output), "url": path_to_url(final_output)},
    )
    step8 = make_step(
        step_id=f"{experiment_id}_step_08_av_compose",
        name="FFmpeg AV Composition",
        description="Combine silent video + audio + subtitles",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="silent video + audio + srt",
        output_summary=f"Success: {final_output.name}",
        key_data={"success": True, "outputPath": str(final_output)},
        logs=["[8/9] FFmpeg AV composition", f"  Success: {final_output.name}"],
        artifacts=[artifact_final],
    )
    steps.append(step8)
    all_logs.extend(step8.logs)

    # Step 9: conclusion and manifest
    manifest_path = get_experiment_dir(experiment_id) / "manifest.json"
    manifest_url = path_to_url(manifest_path)
    manifest = {
        "experimentId": experiment_id,
        "method": method_category,
        "engine": "minimax-tts",
        "resolution": f"{resolution[0]}x{resolution[1]}",
        "fps": 30,
        "audioDurationSec": tts_result.get("durationSec", 0),
        "subtitleCount": len(srt_result.get("subtitles", [])),
        "outputVideo": str(final_output),
        "outputVideoUrl": path_to_url(final_output),
        "audioPath": str(audio_path),
        "audioUrl": path_to_url(audio_path),
        "srtPath": str(srt_path),
        "srtUrl": srt_result.get("srtUrl", ""),
        "silentVideo": str(silent_video_path),
        "createdAt": datetime.utcnow().isoformat(),
        "manifestUrl": manifest_url,
        "warnings": all_warnings,
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
        "totalSteps": 9,
        "succeededSteps": 9,
        "recommendation": "recommended",
        "audioDurationSec": tts_result.get("durationSec", 0),
        "subtitleCount": len(srt_result.get("subtitles", [])),
        "warnings": all_warnings,
    }

    conclusion_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_conclusion",
        type=ArtifactType.EVALUATION,
        title="Conclusion",
        summary=f"TTS+Subtitle route: {len(kps_list)} key points, {tts_result.get('durationSec', 0)}s audio",
        payload=conclusion_payload,
    )

    step9 = make_step(
        step_id=f"{experiment_id}_step_09_conclusion",
        name="Generate Conclusion",
        description="Write manifest and finalize result",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="9 steps completed",
        output_summary=f"Manifest: {manifest_path.name}",
        key_data={"succeededSteps": 9, "audioDurationSec": tts_result.get("durationSec", 0)},
        logs=["[9/9] Generate conclusion", f"  Audio: {tts_result.get('durationSec', 0)}s", f"  Manifest: {manifest_path.name}"],
        artifacts=[manifest_artifact, conclusion_artifact],
    )
    steps.append(step9)
    all_logs.extend(step9.logs)

    all_logs.extend([
        "",
        "[Method Characteristics]",
        "  Cost: medium | Control: high | Stability: medium | Productization: medium",
        "  Adds voiceover and subtitles to structured info display",
        "  Requires MiniMax API key for TTS",
    ])

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=path_to_url(final_output),
        coverUrl=path_to_url(frame_result.get("cover", "")) if frame_result.get("cover") else "",
        assets={
            "method": method_category,
            "engine": "minimax-tts",
            "resolution": f"{resolution[0]}x{resolution[1]}",
            "audioDurationSec": tts_result.get("durationSec", 0),
            "subtitleCount": len(srt_result.get("subtitles", [])),
            "format": "mp4",
        },
        logs=all_logs,
        provider="MiniMax TTS",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "engine": "minimax-tts",
            "status": "succeeded",
            "audioDurationSec": tts_result.get("durationSec", 0),
            "subtitleCount": len(srt_result.get("subtitles", [])),
            "ttsSuccess": True,
            "warnings": all_warnings,
            "riskAssessment": {
                "accuracy": "high - text precise and controllable",
                "stability": "medium - depends on TTS API stability",
                "visualAppeal": "high - adds voice and subtitles",
                "productization": "medium - requires TTS API key",
            },
            "productizationRecommendation": "recommended",
        },
        productionSteps=steps,
    )


def _build_failed_result(
    experiment_id: str,
    method_category: str,
    steps: list,
    error_msg: str,
) -> VideoExperimentResult:
    """Build a failed result."""
    logs = []
    for s in steps:
        logs.extend(s.logs)
    logs.append(f"Error: {error_msg}")
    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl="",
        coverUrl="",
        assets={"method": method_category, "status": "failed", "error": error_msg},
        logs=logs,
        provider="MiniMax TTS",
        adapter=method_category,
        rawOutput={
            "method": method_category,
            "status": "failed",
            "error": error_msg,
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
