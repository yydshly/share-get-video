"""
Chain: hyperframes_tts_video
V0.3.4.1: HyperFrames HTML → manual HeyGen render → MP4

Current status: manual_required
This chain generates HTML but cannot produce final MP4 without human operation.
"""

from datetime import datetime

from app.video_lab.chains.models import ChainResult, ChainStatus
from app.video_lab.adapters.hyperframes_html_render import run_hyperframes_html_render


def run_hyperframes_tts_video(
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
) -> ChainResult:
    """
    HyperFrames chain - always returns manual_required.

    Flow:
    1. Generate HTML via hyperframes_html_render adapter
    2. Return with status=manual_required, htmlUrl populated
    3. User must paste HTML into HeyGen HyperFrames plugin and render MP4
    4. Final MP4 URL must be manually specified/recorded

    This chain does NOT produce finalVideoUrl automatically.
    """
    chain_id = "hyperframes_tts_video"
    start_time = datetime.utcnow()
    logs = []

    logs.append(f"[{chain_id}] Starting chain execution")
    logs.append(f"  experiment_id={experiment_id}")
    logs.append(f"  visual_source=HyperFrames HTML")
    logs.append(f"  audio_source=none (manual TTS not yet integrated)")
    logs.append(f"  subtitle_mode=none")
    logs.append(f"  status=manual_required (needs HeyGen HyperFrames render)")

    # Run the existing hyperframes HTML render adapter
    try:
        adapter_result = run_hyperframes_html_render(
            experiment_id=experiment_id,
            test_case_id=test_case_id,
            input_payload=input_payload,
            params=params,
        )
    except Exception as e:
        logs.append(f"  ERROR: {e}")
        return ChainResult(
            chain_id=chain_id,
            chain_name="HyperFrames HTML 视频",
            status=ChainStatus.FAILED,
            failed_step="hyperframes_html_render",
            failed_reason=str(e),
            visual_source="HyperFrames HTML",
            audio_source="none",
            subtitle_mode="none",
            logs=logs,
            elapsed_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            created_at=start_time,
        )

    # Extract HTML URL from adapter result
    html_url = ""
    manifest_url = ""

    for step in getattr(adapter_result, "production_steps", []):
        for art in getattr(step, "artifacts", []):
            art_dict = art.to_dict() if hasattr(art, "to_dict") else art
            payload = art_dict.get("payload", {})
            if art_dict.get("type") == "manifest":
                manifest_url = payload.get("manifestUrl", "")
                html_url = payload.get("htmlUrl", "")

    # Also check rawOutput for htmlUrl
    raw_output = getattr(adapter_result, "rawOutput", {}) or {}
    if not html_url:
        html_url = raw_output.get("htmlUrl", "")

    elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    logs.append(f"  htmlUrl={html_url}")
    logs.append(f"  manifestUrl={manifest_url}")
    logs.append(f"  Next step: paste HTML into HeyGen HyperFrames plugin to render MP4")

    return ChainResult(
        chain_id=chain_id,
        chain_name="HyperFrames HTML 视频",
        status=ChainStatus.MANUAL_REQUIRED,
        html_url=html_url,
        final_video_url="",  # No automatic final MP4
        has_visual=False,  # HTML is not a video
        has_audio=False,
        has_readable_text=False,
        manifest_url=manifest_url,
        failed_reason="需要人工将 HTML 放入 HeyGen HyperFrames 渲染后上传/指定 MP4",
        visual_source="HyperFrames HTML",
        audio_source="none",
        subtitle_mode="none",
        logs=logs,
        elapsed_ms=elapsed_ms,
        created_at=start_time,
    )
