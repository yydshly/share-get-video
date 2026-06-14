"""
Chain: local_frame_tts_video
V0.3.4.1: Pillow frames + MiniMax TTS + SRT + FFmpeg = final MP4

Reuses run_tts_subtitle_compose adapter.
"""

import os
from datetime import datetime

from app.video_lab.chains.models import ChainResult, ChainStatus
from app.video_lab.chains import write_chain_manifest
from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
from app.video_lab.providers.minimax import MiniMaxTTSClient


def run_local_frame_tts_video(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> ChainResult:
    """
    Complete chain: Pillow frames + MiniMax TTS + SRT + FFmpeg → final MP4.

    Returns ChainResult with:
    - status: succeeded (if final MP4 generated) or failed
    - finalVideoUrl: path to final_with_audio.mp4
    - hasVisual: True
    - hasAudio: True
    - hasReadableText: True (SRT subtitles)
    - audioUrl: voiceover.mp3 path
    - srtUrl: subtitles.srt path
    """
    chain_id = "local_frame_tts_video"
    start_time = datetime.utcnow()
    logs = []
    warnings = []

    # Check TTS availability first
    tts_client = MiniMaxTTSClient()
    if not tts_client.is_configured():
        return ChainResult(
            chain_id=chain_id,
            chain_name="本地帧 TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="minimax_tts",
            failed_reason="MINIMAX_API_KEY not configured",
            visual_source="Pillow frames",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    logs.append(f"[{chain_id}] Starting chain execution")
    logs.append(f"  experiment_id={experiment_id}")
    logs.append(f"  visual_source=Pillow frames")
    logs.append(f"  audio_source=MiniMax TTS")
    logs.append(f"  subtitle_mode=SRT")

    # Run the existing TTS subtitle compose adapter
    adapter_result = run_tts_subtitle_compose(
        experiment_id=experiment_id,
        test_case_id=test_case_id,
        input_payload=input_payload,
        params=params,
    )

    elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    # Extract intermediate artifacts from adapter result
    audio_url = ""
    srt_url = ""
    manifest_url = ""
    final_video_url = ""

    for step in getattr(adapter_result, "productionSteps", []):
        for art in getattr(step, "artifacts", []):
            art_dict = art.to_dict() if hasattr(art, "to_dict") else art
            payload = art_dict.get("payload", {})
            if art_dict.get("type") == "manifest":
                manifest_url = payload.get("manifestUrl", "")
                audio_url = payload.get("audioUrl", "")
                srt_url = payload.get("srtUrl", "")
                final_video_url = payload.get("outputVideoUrl", "")

    # Determine status from adapter result
    adapter_video_url = getattr(adapter_result, "videoUrl", "") or ""
    raw_output = getattr(adapter_result, "rawOutput", {}) or {}

    # The final video should be the outputVideoUrl from manifest (final_with_audio.mp4)
    # not the silent video URL from intermediate steps
    if not final_video_url and adapter_video_url:
        # Fallback: use adapter's videoUrl if manifest wasn't properly populated
        final_video_url = adapter_video_url

    # Check if TTS actually succeeded by looking at the audioUrl
    if manifest_url or audio_url or srt_url:
        # We have some output - check if it's the final video
        if final_video_url:
            # Get audio duration from adapter result assets
            audio_duration_sec = 0.0
            assets = getattr(adapter_result, "assets", {}) or {}
            if isinstance(assets, dict):
                audio_duration_sec = float(assets.get("audioDurationSec", 0))

            # Write chain_manifest.json with final output info
            chain_manifest_url, _ = write_chain_manifest(
                experiment_id=experiment_id,
                chain_id=chain_id,
                status="succeeded",
                final_video_url=final_video_url,
                silent_video_url="",
                audio_url=audio_url,
                srt_url=srt_url,
                subtitle_burned=bool(assets.get("subtitleBurned", True)),
                audio_duration_sec=audio_duration_sec,
                visual_duration_sec=audio_duration_sec,  # visual aligns to audio
                extra={
                    "visual_source": "Pillow frames",
                    "audio_source": "MiniMax TTS",
                    "subtitle_mode": "SRT",
                    "subtitle_renderer": assets.get("subtitleRenderer", "ass"),
                    "subtitle_style": assets.get("subtitleStyle", {}),
                },
            )

            logs.append(f"  finalVideoUrl={final_video_url}")
            logs.append(f"  audioUrl={audio_url}")
            logs.append(f"  srtUrl={srt_url}")
            return ChainResult(
                chain_id=chain_id,
                chain_name="本地帧 TTS 视频",
                status=ChainStatus.SUCCEEDED,
                final_video_url=final_video_url,
                has_visual=True,
                has_audio=True,
                has_readable_text=True,
                audio_url=audio_url,
                srt_url=srt_url,
                manifest_url=chain_manifest_url,
                visual_source="Pillow frames",
                audio_source="MiniMax TTS",
                subtitle_mode="SRT",
                logs=logs,
                warnings=warnings,
                elapsed_ms=elapsed_ms,
                created_at=start_time,
            )
        else:
            # Has intermediate artifacts but no final video
            warnings.append("Intermediate artifacts present but no final MP4 URL")
            return ChainResult(
                chain_id=chain_id,
                chain_name="本地帧 TTS 视频",
                status=ChainStatus.INCOMPLETE,
                audio_url=audio_url,
                srt_url=srt_url,
                manifest_url=manifest_url,
                failed_step="ffmpeg_composition",
                failed_reason="No final video URL in result",
                visual_source="Pillow frames",
                audio_source="MiniMax TTS",
                subtitle_mode="SRT",
                logs=logs,
                warnings=warnings,
                elapsed_ms=elapsed_ms,
                created_at=start_time,
            )
    else:
        # TTS chain failed
        failed_reason = raw_output.get("status", "Unknown error")
        return ChainResult(
            chain_id=chain_id,
            chain_name="本地帧 TTS 视频",
            status=ChainStatus.FAILED,
            failed_step="tts_subtitle_compose",
            failed_reason=f"TTS chain failed: {failed_reason}",
            visual_source="Pillow frames",
            audio_source="MiniMax TTS",
            subtitle_mode="SRT",
            logs=logs,
            warnings=warnings,
            elapsed_ms=elapsed_ms,
            created_at=start_time,
        )
