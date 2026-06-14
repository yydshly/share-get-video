"""
Chain: remotion_tts_video
V0.3.4.1: Remotion silent video + MiniMax TTS + SRT + FFmpeg = final MP4

Complete chain:
1. run_remotion_template → silent MP4
2. generate_voiceover → segments
3. MiniMaxTTSClient.generate() → voiceover.mp3
4. generate_srt_from_segments → subtitles.srt
5. compose_av_with_subtitles → final_with_audio.mp4
"""

from datetime import datetime
from pathlib import Path

from app.video_lab.chains.models import ChainResult, ChainStatus
from app.video_lab.chains import write_chain_manifest
from app.video_lab.adapters.remotion_template import run_remotion_template
from app.video_lab.planners.voiceover_planner import generate_voiceover
from app.video_lab.planners.subtitle_planner import generate_srt_from_segments, generate_ass_from_segments
from app.video_lab.providers.minimax import MiniMaxTTSClient
from app.video_lab.renderers.file_store import (
    get_experiment_dir,
    path_to_url,
    ensure_runtime_exists,
)
from app.video_lab.renderers.ffmpeg_av_composer import (
    compose_av_with_subtitles,
    compose_video_with_audio,
    check_ffmpeg_available,
)
from app.video_lab.renderers.render_params import resolve_resolution


def run_remotion_tts_video(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> ChainResult:
    """
    Complete Remotion + TTS chain: silent video + voiceover + subtitles → final MP4.

    Critical: must NOT return the raw Remotion silent video as finalVideoUrl.
    Only the audio-subtitled final MP4 counts as succeeded.
    """
    chain_id = "remotion_tts_video"
    start_time = datetime.utcnow()
    logs = []
    warnings = []
    all_errors = []

    ensure_runtime_exists()
    exp_dir = get_experiment_dir(experiment_id)

    raw_content = input_payload.get("content", "")
    target_duration = params.get("targetDuration", 45)
    aspect_ratio = params.get("aspectRatio", "9:16")
    resolution = resolve_resolution(aspect_ratio)

    logs.append(f"[{chain_id}] Starting chain execution")
    logs.append(f"  experiment_id={experiment_id}")
    logs.append(f"  visual_source=Remotion template")
    logs.append(f"  audio_source=MiniMax TTS")
    logs.append(f"  subtitle_mode=SRT")

    # ── Step 1: Generate Remotion silent video ──────────────────────────
    logs.append("[Step 1] Generating Remotion silent video...")
    try:
        remotion_result = run_remotion_template(
            experiment_id=experiment_id,
            test_case_id=test_case_id,
            input_payload=input_payload,
            params=params,
        )
    except Exception as e:
        logs.append(f"  ERROR: {e}")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="remotion_render",
            failed_reason=str(e),
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    # Extract silent video URL from remotion result
    silent_video_url = getattr(remotion_result, "videoUrl", "") or ""
    silent_video_path_str = ""

    # Find the actual file path from manifest artifact
    for step in getattr(remotion_result, "productionSteps", []):
        for art in getattr(step, "artifacts", []):
            art_dict = art.to_dict() if hasattr(art, "to_dict") else art
            if art_dict.get("type") == "manifest":
                silent_video_path_str = art_dict.get("payload", {}).get("outputVideo", "")

    if not silent_video_path_str and silent_video_url:
        # Try to derive path from URL
        if silent_video_url.startswith("/runtime/"):
            silent_video_path_str = "runtime/" + silent_video_url[len("/runtime/"):]

    if not silent_video_path_str:
        logs.append("  ERROR: Could not determine Remotion output video path")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="remotion_render",
            failed_reason="Remotion render succeeded but no video path found",
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    silent_video_path = Path(silent_video_path_str)
    silent_video_url = path_to_url(silent_video_path)
    logs.append(f"  Silent video: {silent_video_path}")

    # ── Step 2: Generate voiceover plan ─────────────────────────────────
    logs.append("[Step 2] Generating voiceover plan...")
    try:
        from app.video_lab.planners.content_structurer import structure_content
        from app.video_lab.planners.key_point_extractor import extract_key_points

        structured = structure_content(raw_content, test_case_id)
        key_points = extract_key_points(structured, target_duration)
        kps_list = key_points.get("keyPoints", key_points.get("key_points", []))
        key_points["keyPoints"] = kps_list

        voiceover_result = generate_voiceover(structured, key_points, target_duration)
        voiceover_text = voiceover_result.get("voiceoverText", "")
        segments = voiceover_result.get("segments", [])
    except Exception as e:
        logs.append(f"  ERROR: {e}")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="voiceover_planning",
            failed_reason=str(e),
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    if not voiceover_text:
        logs.append("  ERROR: Empty voiceover text")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="voiceover_planning",
            failed_reason="Generated voiceover text is empty",
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    logs.append(f"  Voiceover text length: {len(voiceover_text)} chars, segments: {len(segments)}")

    # ── Step 3: MiniMax TTS generate audio ──────────────────────────────
    logs.append("[Step 3] Generating MiniMax TTS audio...")
    tts_client = MiniMaxTTSClient()
    if not tts_client.is_configured():
        logs.append("  ERROR: MINIMAX_API_KEY not configured")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="minimax_tts",
            failed_reason="MINIMAX_API_KEY not configured",
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    audio_path = exp_dir / "voiceover.mp3"
    try:
        tts_result = tts_client.generate(text=voiceover_text, output_path=audio_path)
        if not tts_result.get("success"):
            logs.append(f"  ERROR: TTS generation failed: {tts_result.get('message', 'unknown')}")
            return ChainResult(
                chain_id=chain_id,
                chain_name="Remotion TTS 视频",
                status=ChainStatus.FAILED,
                failed_step="minimax_tts",
                failed_reason=f"TTS failed: {tts_result.get('message', 'unknown')}",
                visual_source="Remotion template",
                audio_source="MiniMax TTS",
                subtitle_mode="SRT",
                logs=logs,
                warnings=warnings,
                elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                created_at=start_time,
            )
        audio_url = path_to_url(audio_path)
        audio_duration_sec = float(tts_result.get("durationSec", 0))
        logs.append(f"  Audio: {audio_path}, duration: {audio_duration_sec}s")
    except Exception as e:
        logs.append(f"  ERROR: {e}")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="minimax_tts",
            failed_reason=str(e),
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    # ── Step 4: Generate SRT + ASS subtitles ─────────────────────────────
    logs.append("[Step 4] Generating SRT + ASS subtitles...")
    srt_dir = exp_dir / "subtitles"
    srt_dir.mkdir(parents=True, exist_ok=True)
    srt_path = srt_dir / "subtitles.srt"
    ass_path = srt_dir / "subtitles.ass"
    try:
        srt_result = generate_srt_from_segments(segments, output_path=srt_path)
        srt_url = srt_result.get("srtUrl", "")
        ass_result = generate_ass_from_segments(
            segments,
            output_path=ass_path,
            play_res_x=resolution[0],
            play_res_y=resolution[1],
        )
        subtitle_renderer = "ass"
        subtitle_style = {
            "renderer": "ass",
            "playResX": resolution[0],
            "playResY": resolution[1],
            "fontSize": ass_result.get("style", {}).get("font_size"),
            "marginV": ass_result.get("style", {}).get("margin_v"),
        }
        logs.append(
            f"  SRT: {srt_path.name}, ASS: {ass_path.name}, "
            f"PlayRes {ass_result.get('playResX')}x{ass_result.get('playResY')}, "
            f"fontSize={subtitle_style['fontSize']}"
        )
    except Exception as e:
        logs.append(f"  ERROR: {e}")
        # Non-fatal: we can still compose without subtitles
        warnings.append(f"Subtitle generation failed, continuing without subtitles: {e}")
        srt_path = None
        ass_path = None
        srt_url = ""
        subtitle_renderer = "none"
        subtitle_style = {}

    # ── Step 5: FFmpeg compose final with audio + subtitles ──────────────
    logs.append("[Step 5] FFmpeg compose final video with audio + subtitles...")

    if not check_ffmpeg_available():
        logs.append("  ERROR: FFmpeg not available")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="ffmpeg_composition",
            failed_reason="FFmpeg not available",
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT" if srt_path else "none",
            audio_url=audio_url,
            srt_url=srt_url,
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    final_output = exp_dir / "final_with_audio.mp4"
    subtitle_fallback = False

    # Determine burn-in from params (default True)
    burn_in = bool(params.get("subtitle", {}).get("burnIn", True)) if isinstance(params.get("subtitle"), dict) else True

    if srt_path or ass_path:
        av_result = compose_av_with_subtitles(
            video_path=silent_video_path,
            audio_path=audio_path,
            srt_path=srt_path,
            ass_path=ass_path,
            output_path=final_output,
            resolution=resolution,
            burn_in=burn_in,
            timeout=300,
        )
        if not av_result.get("success"):
            warnings.append(f"Subtitle burn-in failed: {av_result.get('message', '')}, fallback to audio-only")
            subtitle_fallback = True
    else:
        av_result = {"success": False}

    if subtitle_fallback or not srt_path:
        av_result = compose_video_with_audio(
            video_path=silent_video_path,
            audio_path=audio_path,
            output_path=final_output,
            resolution=resolution,
            timeout=300,
        )

    if not av_result.get("success"):
        logs.append(f"  ERROR: FFmpeg composition failed: {av_result.get('message', '')}")
        return ChainResult(
            chain_id=chain_id,
            chain_name="Remotion TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="ffmpeg_composition",
            failed_reason=f"FFmpeg composition failed: {av_result.get('message', '')}",
            visual_source="Remotion template",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT" if not subtitle_fallback else "audio_only",
            audio_url=audio_url,
            srt_url=srt_url,
            logs=logs,
            warnings=warnings,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    final_video_url = path_to_url(final_output)
    manifest_url, _ = write_chain_manifest(
        experiment_id=experiment_id,
        chain_id=chain_id,
        status="succeeded",
        final_video_url=final_video_url,
        silent_video_url=silent_video_url,
        audio_url=audio_url,
        srt_url=srt_url,
        subtitle_burned=not subtitle_fallback,
        audio_duration_sec=audio_duration_sec,
        visual_duration_sec=float(target_duration),
        extra={
            "visual_source": "Remotion template",
            "audio_source": "MiniMax TTS",
            "subtitle_mode": "SRT" if not subtitle_fallback else "audio_only",
            "subtitle_renderer": av_result.get("subtitle_renderer", "none") if not subtitle_fallback else "none",
            "subtitle_style": av_result.get("subtitle_style", {}) if not subtitle_fallback else {},
            "warnings": warnings,
        },
    )

    logs.append(f"  SUCCESS: finalVideoUrl={final_video_url}")

    return ChainResult(
        chain_id=chain_id,
        chain_name="Remotion TTS 视频",
        status=ChainStatus.SUCCEEDED,
        final_video_url=final_video_url,
        has_visual=True,
        has_audio=True,
        has_readable_text=bool(srt_path and srt_url),
        audio_url=audio_url,
        srt_url=srt_url,
        manifest_url=manifest_url,
        visual_source="Remotion template",
        audio_source="MiniMax TTS",
        subtitle_mode="SRT" if not subtitle_fallback else "audio_only",
        logs=logs,
        warnings=warnings,
        elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
        created_at=start_time,
    )
