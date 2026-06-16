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
from app.video_lab.planners.subtitle_planner import generate_srt_from_segments, generate_ass_from_segments, DEFAULT_ASS_STYLE
from app.video_lab.planners.source_bound_plan import (
    build_source_bound_plan_from_information_summary,
    build_structured_from_information_summary_plan,
)
from app.video_lab.providers.minimax import MiniMaxTTSClient, MiniMaxTTSError
from app.video_lab.renderers.file_store import (
    get_experiment_dir,
    ensure_runtime_exists,
    path_to_url,
    write_manifest,
)
from app.video_lab.renderers.ffmpeg_av_composer import compose_av_with_subtitles, compose_video_with_audio, check_ffmpeg_available
from app.video_lab.renderers.render_params import parse_local_frame_params, resolve_resolution
from app.video_lab.renderers.visual import (
    VisualRenderRequest,
    get_visual_renderer,
    resolve_visual_route,
    DEFAULT_VISUAL_ROUTE,
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


def _is_source_bound_information_summary(params: dict) -> bool:
    return (
        isinstance(params, dict)
        and params.get("generationMode") == "information_summary"
        and params.get("sourceBound") is True
        and params.get("allowNewFacts") is False
        and params.get("strictSourceMode") is True
        and isinstance(params.get("informationSummaryPlan"), dict)
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
    is_source_bound_information_summary = _is_source_bound_information_summary(params)
    source_bound_provenance: dict = {}
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
    if not raw_content and not is_source_bound_information_summary:
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

    if is_source_bound_information_summary:
        info_plan = params["informationSummaryPlan"]
        structured = build_structured_from_information_summary_plan(info_plan)
    else:
        info_plan = None
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
        description="Build structured format",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="informationSummaryPlan" if is_source_bound_information_summary else "Raw text",
        output_summary=f"Lead + {structured.get('totalItems', 0)} items",
        key_data={"leadLength": len(structured.get("lead", "")), "itemCount": structured.get("totalItems", 0)},
        logs=(
            ["[2/9] Structure content", f"  Items: {structured.get('totalItems', 0)}", "  Source: informationSummaryPlan"]
            if is_source_bound_information_summary
            else ["[2/9] Structure content", f"  Items: {structured.get('totalItems', 0)}"]
        ),
        artifacts=[artifact_normalized],
    )
    steps.append(step2)
    all_logs.extend(step2.logs)

    # Step 3: plan shots (LLM 规划展示方式，失败回退确定性)；构建 key_points
    if is_source_bound_information_summary:
        plan = build_source_bound_plan_from_information_summary(
            info_plan or {},
            target_duration_sec=float(target_duration),
        )
    else:
        from app.video_lab.planners.llm_content_planner import plan_shots
        use_llm_plan = params.get("useLlmPlan", True) if isinstance(params, dict) else True
        plan = plan_shots(
            raw_content,
            max_items=render_params.key_point_count,
            test_case_id=test_case_id,
            use_llm=use_llm_plan,
            target_duration_sec=float(target_duration),  # V0.8.3: 旁白时长预算
        )
    plan_shots_list = plan.get("shots", [])
    if is_source_bound_information_summary:
        source_bound_provenance = {
            "generationMode": "information_summary",
            "sourceBound": True,
            "allowNewFacts": False,
            "strictSourceMode": True,
            "planSource": "informationSummaryPlan",
            "planItemCount": len(plan_shots_list),
            "inputFingerprint": params.get("inputFingerprint", ""),
        }
    # 用规划好的封面标题作为 lead（封面更干净）
    if plan.get("coverTitle"):
        structured["lead"] = plan["coverTitle"]

    kps_list = []
    for i, s in enumerate(plan_shots_list, 1):
        kps_list.append({
            "index": i,
            "headline": s.get("headline", ""),
            "display": s.get("display", ""),
            "narration": s.get("narration", ""),
            "title": s.get("headline", ""),
            "body": s.get("display", ""),
            "source": "",
            "category": "",
            # V0.3.6-b2: carry emphasisTerms through to key_points
            "emphasisTerms": s.get("emphasisTerms", []),
            # 主题自适应：语义基调
            "tone": s.get("tone", ""),
            # V0.3.6-quality-p0: carry metrics through to key_points
            "metrics": s.get("metrics", []),
        })
    key_points = {
        "keyPoints": kps_list,
        "key_points": kps_list,
        "totalPoints": len(kps_list),
        "selectedFrom": len(kps_list),
        "planSource": plan.get("source", "fallback"),
    }
    all_logs.append(f"  plan source: {plan.get('source')}, shots: {len(kps_list)}")

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

    # Step 4: build voiceover from plan (opening + per-shot narration + closing)
    # 每段对应一张画面，便于音画时序对齐；字幕也与之一致
    vo_parts = []
    opening = (plan.get("opening") or "").strip()
    closing = (plan.get("closing") or "").strip()
    if opening:
        vo_parts.append(opening)
    for s in plan_shots_list:
        vo_parts.append((s.get("narration") or s.get("display") or s.get("headline") or "").strip())
    if closing:
        vo_parts.append(closing)

    vo_segments = []
    cursor = 0.0
    for idx, text in enumerate(vo_parts, 1):
        est = max(2.5, len(text) * 0.28)  # 估算，TTS 后会按真实音频重缩放
        vo_segments.append({"index": idx, "text": text, "startSec": round(cursor, 2), "durationSec": round(est, 2)})
        cursor += est
    voiceover_result = {
        "voiceoverText": " ".join(p for p in vo_parts if p),
        "segments": vo_segments,
        "estimatedDurationSec": round(cursor, 2),
        "hasOpening": bool(opening),
        "hasClosing": bool(closing),
    }
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
        type=ArtifactType.AUDIO_OUTPUT,
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

    # Rescale subtitle timeline to the REAL TTS audio duration to avoid drift.
    # 旁白段时长是估算的，与真实 TTS 时长脱节会导致字幕比音频早/晚结束。
    real_audio_dur = float(tts_result.get("durationSec", 0) or 0)
    segments = voiceover_result.get("segments", [])
    if real_audio_dur > 0 and segments:
        last = segments[-1]
        estimated_total = float(last.get("startSec", 0)) + float(last.get("durationSec", 0))
        if estimated_total > 0:
            scale = real_audio_dur / estimated_total
            for seg in segments:
                seg["startSec"] = round(float(seg.get("startSec", 0)) * scale, 2)
                seg["durationSec"] = round(float(seg.get("durationSec", 0)) * scale, 2)
            voiceover_result["segments"] = segments
            voiceover_result["estimatedDurationSec"] = round(real_audio_dur, 2)
            all_logs.append(f"  Rescaled subtitle timeline x{scale:.2f} to match audio {real_audio_dur:.1f}s")

    # Step 6: generate SRT + ASS subtitles
    subtitle_dir = exp_dir / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    srt_path = subtitle_dir / "subtitles.srt"
    ass_path = subtitle_dir / "subtitles.ass"

    srt_result = generate_srt_from_segments(segments, output_path=srt_path)
    ass_result = generate_ass_from_segments(
        segments,
        output_path=ass_path,
        play_res_x=resolution[0],
        play_res_y=resolution[1],
    )
    artifact_srt = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_srt",
        type=ArtifactType.SUBTITLE_FILE,
        title="Subtitle SRT",
        summary=f"{len(srt_result.get('subtitles', []))} subtitle entries",
        payload={
            "path": srt_result.get("srtPath", ""),
            "url": srt_result.get("srtUrl", ""),
            "subtitleCount": len(srt_result.get("subtitles", [])),
        },
    )
    artifact_ass = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_ass",
        type=ArtifactType.SUBTITLE_FILE,
        title="Subtitle ASS",
        summary=f"ASS, {len(ass_result.get('subtitles', []))} entries, fontSize={ass_result.get('style', {}).get('font_size')}",
        payload={
            "path": ass_result.get("assPath", ""),
            "url": ass_result.get("assUrl", ""),
            "playResX": ass_result.get("playResX"),
            "playResY": ass_result.get("playResY"),
            "style": ass_result.get("style", {}),
            "renderer": "ass",
        },
    )
    step6 = make_step(
        step_id=f"{experiment_id}_step_06_subtitles",
        name="Generate Subtitles (SRT + ASS)",
        description="Generate SRT and ASS subtitle files from voiceover segments",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"{len(segments)} voiceover segments",
        output_summary=f"{len(srt_result.get('subtitles', []))} entries (SRT + ASS)",
        key_data={"subtitleCount": len(srt_result.get("subtitles", []))},
        logs=[
            "[6/9] Generate subtitles",
            f"  SRT: {srt_path.name}, ASS: {ass_path.name}",
            f"  ASS PlayRes: {ass_result.get('playResX')}x{ass_result.get('playResY')}, fontSize={ass_result.get('style', {}).get('font_size')}",
        ],
        artifacts=[artifact_srt, artifact_ass],
    )
    steps.append(step6)
    all_logs.extend(step6.logs)

    # Step 7: generate silent video via pluggable VisualRenderer
    # 视觉路线可插拔：默认 local_frame_compose (Pillow)，可用 params.visualRoute 切换
    # （如 template_programmatic_render = Remotion）。下游 TTS/字幕/合成保持共享。
    visual_route = resolve_visual_route(params)
    renderer = get_visual_renderer(visual_route)
    if renderer is None:
        renderer = get_visual_renderer(DEFAULT_VISUAL_ROUTE)
        visual_route = DEFAULT_VISUAL_ROUTE

    # 画面时长对齐真实音频时长（成片为 audio_preserved），避免画面比音频短一截
    visual_target = real_audio_dur if real_audio_dur > 0 else target_duration
    visual_request = VisualRenderRequest(
        experiment_id=experiment_id,
        structured=structured,
        key_points=key_points,
        target_duration_sec=visual_target,
        resolution=resolution,
        params=params or {},
        audio_duration_sec=float(tts_result.get("durationSec", 0)),
        voiceover_segments=segments,  # 已按真实音频重缩放，用于画面/配音时序对齐
        test_case_id=test_case_id,
        input_payload=input_payload,
    )
    visual_result = renderer.render(visual_request)
    all_warnings.extend(visual_result.warnings)
    all_logs.extend(visual_result.logs)

    if not visual_result.success:
        step7 = make_step(
            step_id=f"{experiment_id}_step_07_silent_video",
            name="Generate Silent Video",
            description=f"Generate silent video via visual route '{visual_route}'",
            status=ProductionStepStatus.FAILED,
            input_summary=f"Visual route: {visual_route}",
            output_summary=f"Visual render failed: {visual_result.message}",
            key_data={"visualRoute": visual_route, "success": False, "error": visual_result.message},
            logs=["[7/9] Generate silent video", f"  route={visual_route}", f"  ERROR: {visual_result.message}"],
        )
        steps.append(step7)
        all_logs.extend(step7.logs)
        return _build_failed_result(experiment_id, method_category, steps, visual_result.message or "Visual render failed")

    silent_video_path = Path(visual_result.silent_video_path)
    cover_path = visual_result.cover_path

    artifact_silent = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_silent",
        type=ArtifactType.VIDEO_OUTPUT,
        title="Silent Video",
        summary=f"Path: {silent_video_path}",
        payload={
            "path": str(silent_video_path),
            "url": visual_result.silent_video_url or path_to_url(silent_video_path),
            "visualRoute": visual_route,
        },
    )
    step7 = make_step(
        step_id=f"{experiment_id}_step_07_silent_video",
        name="Generate Silent Video",
        description=f"Generate silent video via visual route '{visual_route}'",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary=f"Visual route: {visual_route}",
        output_summary=f"Success: {silent_video_path.name} (route={visual_route})",
        key_data={
            "visualRoute": visual_route,
            "success": True,
            "frameCount": visual_result.frame_count,
            "visualDurationSec": visual_result.total_duration_sec,
        },
        logs=["[7/9] Generate silent video", f"  route={visual_route}", f"  Output: {silent_video_path.name}"],
        artifacts=[artifact_silent],
    )
    steps.append(step7)
    all_logs.extend(step7.logs)

    # Step 8: FFmpeg compose final with audio + subtitles
    # First try with subtitles, fallback to audio-only if subtitle burn-in fails
    subtitle_burned = False
    subtitle_fallback = False

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

    # Try with subtitles first (ASS preferred, SRT fallback)
    av_result = compose_av_with_subtitles(
        video_path=silent_video_path,
        audio_path=audio_path,
        srt_path=srt_path,
        ass_path=ass_path,
        output_path=final_output,
        resolution=resolution,
        burn_in=render_params.burn_in if hasattr(render_params, "burn_in") else True,
        timeout=300,
        bgm_params=params,  # BGM params from top-level params dict (V0.3.8)
    )

    if not av_result.get("success"):
        # Fallback: try audio-only (subtitle burn-in failed on Windows FFmpeg)
        all_warnings.append(f"Subtitle burn-in failed: {av_result.get('message', '')}, fallback to audio-only")
        av_result = compose_video_with_audio(
            video_path=silent_video_path,
            audio_path=audio_path,
            output_path=final_output,
            resolution=resolution,
            timeout=300,
            bgm_params=params,  # BGM params from top-level params dict (V0.3.8)
        )
        subtitle_fallback = True
        if av_result.get("success"):
            all_logs.append("  Fallback: audio-only composition (subtitle burn-in skipped)")

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

    # Success
    subtitle_burned = not subtitle_fallback

    artifact_final = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_final",
        type=ArtifactType.VIDEO_OUTPUT,
        title="Final Video with Audio",
        summary=f"Path: {final_output}",
        payload={
            "path": str(final_output),
            "url": path_to_url(final_output),
            "subtitleBurned": subtitle_burned,
            "subtitleFallback": subtitle_fallback,
        },
    )
    step8 = make_step(
        step_id=f"{experiment_id}_step_08_av_compose",
        name="FFmpeg AV Composition",
        description="Combine silent video + audio + subtitles",
        status=ProductionStepStatus.SUCCEEDED,
        input_summary="silent video + audio + srt",
        output_summary=f"Success: {final_output.name} (subtitleBurned={subtitle_burned})",
        key_data={
            "success": True,
            "outputPath": str(final_output),
            "subtitleBurned": subtitle_burned,
            "subtitleFallback": subtitle_fallback,
        },
        logs=[
            f"[8/9] FFmpeg AV composition",
            f"  Success: {final_output.name}",
            f"  subtitleBurned={subtitle_burned}, subtitleFallback={subtitle_fallback}",
        ],
        artifacts=[artifact_final],
    )
    steps.append(step8)
    all_logs.extend(step8.logs)

    # Quality assessment - 自动判定视频质量（确定性检查）
    from app.video_lab.quality import assess_quality
    quality_report = assess_quality(
        source_content=raw_content,
        structured=structured,
        key_points=key_points,
        voiceover=voiceover_result,
        audio_duration_sec=float(tts_result.get("durationSec", 0)),
        subtitle_count=len(srt_result.get("subtitles", [])),
        subtitle_burned=subtitle_burned,
        visual_duration_sec=float(visual_result.total_duration_sec),
        has_cover=bool(cover_path),
        frame_count=int(visual_result.frame_count),
        warnings=all_warnings,
        target_duration_sec=float(target_duration),
    )
    quality_dict = quality_report.to_dict()

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
        "subtitleRenderer": av_result.get("subtitle_renderer", "none"),
        "subtitleStyle": av_result.get("subtitle_style", {}),
        "subtitleBurned": subtitle_burned,
        "subtitleFallback": subtitle_fallback,
        "outputVideo": str(final_output),
        "outputVideoUrl": path_to_url(final_output),
        "audioPath": str(audio_path),
        "audioUrl": path_to_url(audio_path),
        "srtPath": str(srt_path),
        "srtUrl": srt_result.get("srtUrl", ""),
        "assPath": ass_result.get("assPath", ""),
        "assUrl": ass_result.get("assUrl", ""),
        "silentVideo": str(silent_video_path),
        "createdAt": datetime.utcnow().isoformat(),
        "manifestUrl": manifest_url,
        "warnings": all_warnings,
        "quality": quality_dict,
        "bgm": {
            "enabled": av_result.get("bgm_enabled", False),
            "mode": av_result.get("bgm_mode", "none"),
            "volume": av_result.get("bgm_volume", 0.0),
        },
    }
    if source_bound_provenance:
        manifest.update(source_bound_provenance)
    write_manifest(experiment_id, manifest)

    # V0.8.2: Add planDebug to manifest for cheap post-hoc diagnosis
    # (coverTitle / opening / closing / per-shot headline/display/narration/tone/
    #  emphasisTerms/metrics + voiceover segment timeline). Does not affect
    # generation logic; only enriches the manifest on disk so users can open
    # manifestUrl and trace "title wrong / number missing / audio-visual drift".
    try:
        _plan_debug_shots = []
        for _i, _s in enumerate(plan_shots_list, 1):
            _plan_debug_shots.append({
                "index": _i,
                "headline": _s.get("headline", ""),
                "display": _s.get("display", ""),
                "narration": _s.get("narration", ""),
                "tone": _s.get("tone", ""),
                "emphasisTerms": list(_s.get("emphasisTerms", []) or []),
                "metrics": list(_s.get("metrics", []) or []),
            })
        _plan_debug_segments = []
        for _seg in segments:
            _plan_debug_segments.append({
                "index": _seg.get("index"),
                "text": _seg.get("text", ""),
                "startSec": _seg.get("startSec", 0),
                "durationSec": _seg.get("durationSec", 0),
            })

        # V0.8.3: budgetDebug — narration 字数预算 vs 实际音频时长
        _opening_len = len(opening) if opening else 0
        _closing_len = len(closing) if closing else 0
        _narration_lengths = [len((s.get("narration") or "").strip()) for s in plan_shots_list]
        _total_vo_chars = _opening_len + sum(_narration_lengths) + _closing_len
        _actual_audio = float(tts_result.get("durationSec", 0) or 0) if "tts_result" in locals() else 0.0
        _target_dur = float(target_duration) if target_duration else 0.0
        # V0.8.3: 超预算 = 实际音频超过目标时长 10%（允许 TTS 节奏浮动）
        _over_budget = bool(_actual_audio > 0 and _target_dur > 0 and _actual_audio > _target_dur * 1.1)
        _budget_debug = {
            "targetDurationSec": _target_dur,
            "openingLength": _opening_len,
            "closingLength": _closing_len,
            "narrationLengths": _narration_lengths,
            "totalVoiceoverChars": _total_vo_chars,
            "actualAudioDurationSec": round(_actual_audio, 2),
            "overBudget": _over_budget,
        }

        manifest["planDebug"] = {
            "planSource": plan.get("source", "fallback"),
            "coverTitle": plan.get("coverTitle", ""),
            "opening": opening,
            "closing": closing,
            "shotCount": len(plan_shots_list),
            "shots": _plan_debug_shots,
            "voiceoverSegments": _plan_debug_segments,
            "budgetDebug": _budget_debug,
        }
        if source_bound_provenance:
            manifest["planDebug"]["sourceBoundProvenance"] = source_bound_provenance
        # Persist updated manifest (with planDebug) back to disk
        write_manifest(experiment_id, manifest)
    except Exception as _e:  # pragma: no cover - diagnostic-only, must never break flow
        all_logs.append(f"  [V0.8.2] planDebug write skipped: {_e}")

    quality_artifact = VideoProductionArtifact(
        artifact_id=f"{experiment_id}_art_quality",
        type=ArtifactType.EVALUATION,
        title="Quality Report",
        summary=f"overall={quality_dict['overallScore']} | {quality_dict['counts']}",
        payload=quality_dict,
    )

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
        "subtitleBurned": subtitle_burned,
        "subtitleFallback": subtitle_fallback,
        "bgmEnabled": av_result.get("bgm_enabled", False),
        "bgmMode": av_result.get("bgm_mode", "none"),
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
        artifacts=[manifest_artifact, conclusion_artifact, quality_artifact],
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
        coverUrl=path_to_url(cover_path) if cover_path else "",
        assets={
            "method": method_category,
            "engine": "minimax-tts",
            "resolution": f"{resolution[0]}x{resolution[1]}",
            "audioDurationSec": tts_result.get("durationSec", 0),
            "subtitleCount": len(srt_result.get("subtitles", [])),
            "subtitleBurned": subtitle_burned,
            "subtitleFallback": subtitle_fallback,
            "subtitleRenderer": av_result.get("subtitle_renderer", "none"),
            "subtitleStyle": av_result.get("subtitle_style", {}),
            "bgmEnabled": av_result.get("bgm_enabled", False),
            "bgmMode": av_result.get("bgm_mode", "none"),
            "bgmVolume": av_result.get("bgm_volume", 0.0),
            "format": "mp4",
            "qualityScore": quality_dict["overallScore"],
            "qualityDimensions": quality_dict["dimensionScores"],
            **source_bound_provenance,
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
            "subtitleBurned": subtitle_burned,
            "subtitleFallback": subtitle_fallback,
            "ttsSuccess": True,
            "warnings": all_warnings,
            "quality": quality_dict,
            **source_bound_provenance,
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
