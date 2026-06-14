"""
Chain Registry
V0.3.4.1: Registry of all complete video generation chains
"""

from app.video_lab.chains.models import ChainDefinition


# All registered chains
_CHAIN_REGISTRY: list[ChainDefinition] = [
    ChainDefinition(
        chain_id="local_frame_tts_video",
        name="本地帧 TTS 视频",
        visual_route="local_frame_compose",
        audio_provider="minimax_tts",
        subtitle_mode="srt",
        generation_mode="auto",
        final_output_required=True,
        requires_tts=True,
    ),
    ChainDefinition(
        chain_id="remotion_tts_video",
        name="Remotion TTS 视频",
        visual_route="template_programmatic_render",
        audio_provider="minimax_tts",
        subtitle_mode="srt",
        generation_mode="auto",
        final_output_required=True,
        requires_tts=True,
    ),
    ChainDefinition(
        chain_id="hyperframes_tts_video",
        name="HyperFrames HTML 视频",
        visual_route="hyperframes_html_render",
        audio_provider="none",
        subtitle_mode="none",
        generation_mode="manual",
        final_output_required=True,
        requires_tts=False,
    ),
]


def get_chain(chain_id: str) -> ChainDefinition | None:
    """Get chain definition by ID."""
    for chain in _CHAIN_REGISTRY:
        if chain.chain_id == chain_id:
            return chain
    return None


def list_chains() -> list[ChainDefinition]:
    """List all registered chains."""
    return list(_CHAIN_REGISTRY)


def run_chain(
    chain_id: str,
    experiment_id: str,
    test_case_id: str,
    input_payload: dict,
    params: dict,
):
    """
    Run a complete video generation chain by ID.

    Returns ChainResult dict with chainId, status, finalVideoUrl, hasVisual,
    hasAudio, hasReadableText, audioUrl, srtUrl, manifestUrl, failedStep,
    failedReason.
    """
    if chain_id == "local_frame_tts_video":
        from app.video_lab.chains.local_frame_tts_video import run_local_frame_tts_video
        return run_local_frame_tts_video(experiment_id, test_case_id, input_payload, params)
    elif chain_id == "remotion_tts_video":
        from app.video_lab.chains.remotion_tts_video import run_remotion_tts_video
        return run_remotion_tts_video(experiment_id, test_case_id, input_payload, params)
    elif chain_id == "hyperframes_tts_video":
        from app.video_lab.chains.hyperframes_tts_video import run_hyperframes_tts_video
        return run_hyperframes_tts_video(experiment_id, test_case_id, input_payload, params)
    else:
        from app.video_lab.chains.models import ChainResult, ChainStatus
        return ChainResult(
            chain_id=chain_id,
            chain_name=chain_id,
            status=ChainStatus.FAILED,
            failed_step="registry",
            failed_reason=f"Unknown chain: {chain_id}",
        )
