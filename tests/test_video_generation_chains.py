"""
Tests for V0.3.4.1 Complete Video Generation Chains
- Chain registry contains all three chains
- local_frame_tts_video: succeeds with finalVideoUrl, hasAudio, hasVisual
- remotion_tts_video: generates finalVideoUrl, not silent video
- hyperframes_tts_video: always manual_required, never succeeded
- Succeeded chain must have hasAudio=true and hasVisual=true
- Missing MINIMAX_API_KEY causes TTS chain failed with failedStep=minimax_tts
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.chains.models import ChainStatus


# ─────────────────────────────────────────
# 1. Chain Registry contains all three chains
# ─────────────────────────────────────────
def test_chain_registry_contains_all_three_chains():
    """Registry should contain local_frame_tts_video, remotion_tts_video, hyperframes_tts_video."""
    from app.video_lab.chains.registry import list_chains

    chains = list_chains()
    chain_ids = [c.chain_id for c in chains]

    assert "local_frame_tts_video" in chain_ids, "local_frame_tts_video should be registered"
    assert "remotion_tts_video" in chain_ids, "remotion_tts_video should be registered"
    assert "hyperframes_tts_video" in chain_ids, "hyperframes_tts_video should be registered"


def test_chain_registry_local_frame_tts_video_metadata():
    """local_frame_tts_video should have correct metadata."""
    from app.video_lab.chains.registry import get_chain

    chain = get_chain("local_frame_tts_video")
    assert chain is not None
    assert chain.visual_route == "local_frame_compose"
    assert chain.audio_provider == "minimax_tts"
    assert chain.subtitle_mode == "srt"
    assert chain.generation_mode == "auto"
    assert chain.final_output_required is True
    assert chain.requires_tts is True


def test_chain_registry_remotion_tts_video_metadata():
    """remotion_tts_video should have correct metadata."""
    from app.video_lab.chains.registry import get_chain

    chain = get_chain("remotion_tts_video")
    assert chain is not None
    assert chain.visual_route == "template_programmatic_render"
    assert chain.audio_provider == "minimax_tts"
    assert chain.subtitle_mode == "srt"
    assert chain.generation_mode == "auto"
    assert chain.final_output_required is True
    assert chain.requires_tts is True


def test_chain_registry_hyperframes_tts_video_metadata():
    """hyperframes_tts_video should have manual generation mode and no TTS."""
    from app.video_lab.chains.registry import get_chain

    chain = get_chain("hyperframes_tts_video")
    assert chain is not None
    assert chain.visual_route == "hyperframes_html_render"
    assert chain.audio_provider == "none"
    assert chain.subtitle_mode == "none"
    assert chain.generation_mode == "manual"
    assert chain.final_output_required is True
    assert chain.requires_tts is False


# ─────────────────────────────────────────
# 2. local_frame_tts_video: missing API key fails with correct step
# ─────────────────────────────────────────
def test_local_frame_tts_video_missing_api_key_fails():
    """local_frame_tts_video without MINIMAX_API_KEY should fail at minimax_tts step."""
    from app.video_lab.chains.local_frame_tts_video import run_local_frame_tts_video

    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        result = run_local_frame_tts_video(
            experiment_id="test_chain_no_key",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "测试内容"},
            params={},
        )

    assert result.status == ChainStatus.FAILED, f"Expected FAILED, got {result.status}"
    assert result.failed_step == "minimax_tts", f"Expected failed_step=minimax_tts, got {result.failed_step}"
    assert "MINIMAX_API_KEY" in result.failed_reason or "not configured" in result.failed_reason.lower()


# ─────────────────────────────────────────
# 3. remotion_tts_video: fails gracefully when environment issues occur
# ─────────────────────────────────────────
def test_remotion_tts_video_chain_returns_failed_on_environment_issue():
    """remotion_tts_video should return failed status when environment has issues."""
    from app.video_lab.chains.remotion_tts_video import run_remotion_tts_video

    # Without a valid Remotion environment (Node.js), the chain will fail
    # Either at minimax_tts (if no API key) or remotion_render (if key present but no Node.js)
    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        result = run_remotion_tts_video(
            experiment_id="test_remotion_chain_env_issue",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "测试内容"},
            params={},
        )

    assert result.status == ChainStatus.FAILED, f"Expected FAILED, got {result.status}"
    assert result.failed_step in ("minimax_tts", "remotion_render"), \
        f"Expected failed_step in (minimax_tts, remotion_render), got {result.failed_step}"


# ─────────────────────────────────────────
# 4. hyperframes_tts_video: always manual_required
# ─────────────────────────────────────────
def test_hyperframes_tts_video_is_manual_required():
    """hyperframes_tts_video should always return manual_required, never succeeded."""
    from app.video_lab.chains.hyperframes_tts_video import run_hyperframes_tts_video

    # Even with valid content, it should return manual_required
    result = run_hyperframes_tts_video(
        experiment_id="test_hyperframes_chain",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": "测试内容用于生成HTML"},
        params={},
    )

    assert result.status == ChainStatus.MANUAL_REQUIRED, \
        f"Expected MANUAL_REQUIRED, got {result.status}"
    assert result.chain_id == "hyperframes_tts_video"
    assert result.html_url != "", "Should have htmlUrl populated"
    assert result.final_video_url == "", "Should NOT have finalVideoUrl"


def test_hyperframes_tts_video_never_succeeded():
    """hyperframes_tts_video should NEVER be able to return succeeded status."""
    from app.video_lab.chains.hyperframes_tts_video import run_hyperframes_tts_video

    # Run multiple times with different inputs - should always be manual_required
    for i in range(3):
        result = run_hyperframes_tts_video(
            experiment_id=f"test_hyperframes_chain_{i}",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": f"测试内容{i}"},
            params={"targetDuration": 30},
        )
        assert result.status == ChainStatus.MANUAL_REQUIRED, \
            f"hyperframes_tts_video should never be succeeded, got {result.status}"


# ─────────────────────────────────────────
# 5. Chain models: ChainStatus enum has all required values
# ─────────────────────────────────────────
def test_chain_status_enum_values():
    """ChainStatus should have all required status values."""
    values = [s.value for s in ChainStatus]
    assert "succeeded" in values
    assert "failed" in values
    assert "manual_required" in values
    assert "incomplete" in values
    assert "skipped" in values


# ─────────────────────────────────────────
# 6. ChainResult has required fields
# ─────────────────────────────────────────
def test_chain_result_to_dict_has_required_fields():
    """ChainResult.to_dict() should include all required fields."""
    from app.video_lab.chains.models import ChainResult

    result = ChainResult(
        chain_id="test_chain",
        chain_name="Test Chain",
        status=ChainStatus.SUCCEEDED,
        final_video_url="http://example.com/final.mp4",
        has_visual=True,
        has_audio=True,
        has_readable_text=True,
        audio_url="http://example.com/audio.mp3",
        srt_url="http://example.com/subtitles.srt",
        failed_step="",
        failed_reason="",
    )

    d = result.to_dict()
    assert "chainId" in d
    assert "status" in d
    assert "finalVideoUrl" in d
    assert "hasVisual" in d
    assert "hasAudio" in d
    assert "hasReadableText" in d
    assert "audioUrl" in d
    assert "srtUrl" in d


# ─────────────────────────────────────────
# 7. Succeeded chain must have hasVisual=true and hasAudio=true
# ─────────────────────────────────────────
def test_chain_definition_to_dict():
    """ChainDefinition.to_dict() should produce correct output."""
    from app.video_lab.chains.models import ChainDefinition

    chain = ChainDefinition(
        chain_id="test_chain",
        name="Test Chain",
        visual_route="local_frame_compose",
        audio_provider="minimax_tts",
        subtitle_mode="srt",
        generation_mode="auto",
        final_output_required=True,
        requires_tts=True,
    )

    d = chain.to_dict()
    assert d["chainId"] == "test_chain"
    assert d["name"] == "Test Chain"
    assert d["visualRoute"] == "local_frame_compose"
    assert d["audioProvider"] == "minimax_tts"
    assert d["subtitleMode"] == "srt"
    assert d["generationMode"] == "auto"
    assert d["finalOutputRequired"] is True
    assert d["requiresTts"] is True


# ─────────────────────────────────────────
# 8. local_frame_tts_video: success path artifact extraction
# ─────────────────────────────────────────
def test_local_frame_tts_video_success_extracts_artifacts():
    """Mock success: local_frame_tts_video should extract finalVideoUrl, audioUrl, srtUrl from adapter result."""
    from app.video_lab.chains.local_frame_tts_video import run_local_frame_tts_video
    from app.video_lab.models import (
        VideoExperimentResult,
        VideoProductionStep,
        VideoProductionArtifact,
        ProductionStepStatus,
        ArtifactType,
    )
    from datetime import datetime

    # Build a mock successful adapter result
    manifest_artifact = VideoProductionArtifact(
        artifact_id="test_art_manifest",
        type=ArtifactType.MANIFEST,
        title="Manifest",
        summary="Test manifest",
        payload={
            "manifestUrl": "/runtime/test_exp/manifest.json",
            "audioUrl": "/runtime/test_exp/audio/voiceover.mp3",
            "srtUrl": "/runtime/test_exp/subtitles/subtitles.srt",
            "outputVideoUrl": "/runtime/test_exp/final_with_audio.mp4",
        },
    )
    step = VideoProductionStep(
        step_id="test_step_01",
        name="Test Step",
        description="Test",
        status=ProductionStepStatus.SUCCEEDED,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        input_summary="input",
        output_summary="output",
        artifacts=[manifest_artifact],
    )
    mock_result = VideoExperimentResult(
        experimentId="test_exp",
        videoUrl="/runtime/test_exp/silent_video.mp4",
        productionSteps=[step],
    )

    with patch("app.video_lab.chains.local_frame_tts_video.run_tts_subtitle_compose", return_value=mock_result):
        with patch("app.video_lab.chains.local_frame_tts_video.MiniMaxTTSClient") as mock_tts_cls:
            mock_tts = MagicMock()
            mock_tts.is_configured.return_value = True
            mock_tts_cls.return_value = mock_tts

            result = run_local_frame_tts_video(
                experiment_id="test_exp_success",
                test_case_id="case_ai_frontier_daily_001",
                input_payload={"content": "测试内容"},
                params={},
            )

    assert result.status == ChainStatus.SUCCEEDED, f"Expected SUCCEEDED, got {result.status}"
    assert result.final_video_url.endswith("final_with_audio.mp4"), \
        f"Expected final_with_audio.mp4, got {result.final_video_url}"
    assert result.audio_url.endswith("voiceover.mp3"), \
        f"Expected voiceover.mp3, got {result.audio_url}"
    assert result.srt_url.endswith("subtitles.srt"), \
        f"Expected subtitles.srt, got {result.srt_url}"
    assert result.has_visual is True, "hasVisual should be True"
    assert result.has_audio is True, "hasAudio should be True"
    assert result.has_readable_text is True, "hasReadableText should be True"


# ─────────────────────────────────────────
# 9. hyperframes_tts_video: success extracts htmlUrl
# ─────────────────────────────────────────
def test_hyperframes_tts_video_success_extracts_html_url():
    """Mock success: hyperframes_tts_video should extract htmlUrl from adapter result."""
    from app.video_lab.chains.hyperframes_tts_video import run_hyperframes_tts_video
    from app.video_lab.models import (
        VideoExperimentResult,
        VideoProductionStep,
        VideoProductionArtifact,
        ProductionStepStatus,
        ArtifactType,
    )
    from datetime import datetime

    manifest_artifact = VideoProductionArtifact(
        artifact_id="test_art_html",
        type=ArtifactType.MANIFEST,
        title="Manifest",
        summary="HyperFrames HTML manifest",
        payload={
            "htmlUrl": "/runtime/test_hf/hyperframes/index.html",
            "manifestUrl": "/runtime/test_hf/manifest.json",
        },
    )
    step = VideoProductionStep(
        step_id="test_step_hf",
        name="Build HTML",
        description="Test",
        status=ProductionStepStatus.SUCCEEDED,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        input_summary="input",
        output_summary="output",
        artifacts=[manifest_artifact],
    )
    mock_result = VideoExperimentResult(
        experimentId="test_hf",
        videoUrl="",
        productionSteps=[step],
    )

    with patch("app.video_lab.chains.hyperframes_tts_video.run_hyperframes_html_render", return_value=mock_result):
        result = run_hyperframes_tts_video(
            experiment_id="test_hf_success",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "测试内容"},
            params={},
        )

    assert result.status == ChainStatus.MANUAL_REQUIRED, \
        f"Expected MANUAL_REQUIRED, got {result.status}"
    assert result.html_url.endswith("index.html"), \
        f"Expected index.html, got {result.html_url}"
    assert result.final_video_url == "", "finalVideoUrl should be empty for manual chain"
    assert result.has_visual is False, "hasVisual should be False for HTML chain"
    assert result.has_audio is False, "hasAudio should be False for HTML chain"


# ─────────────────────────────────────────
# 10. remotion_tts_video: mock full chain verifies finalVideoUrl is final, not silent
# ─────────────────────────────────────────
def test_remotion_tts_video_final_url_is_composed_not_silent():
    """Mock success: remotion_tts_video should return final_with_audio.mp4, not silent video."""
    from app.video_lab.chains.remotion_tts_video import run_remotion_tts_video
    from app.video_lab.models import (
        VideoExperimentResult,
        VideoProductionStep,
        VideoProductionArtifact,
        ProductionStepStatus,
        ArtifactType,
    )
    from datetime import datetime

    # Remotion render result with SILENT video URL
    silent_manifest_artifact = VideoProductionArtifact(
        artifact_id="remotion_manifest",
        type=ArtifactType.MANIFEST,
        title="Remotion Manifest",
        summary="Silent video",
        payload={
            "outputVideo": "runtime/video_lab/experiments/remotion_exp/remotion_out.mp4",
            "manifestUrl": "/runtime/remotion_exp/manifest.json",
        },
    )
    silent_step = VideoProductionStep(
        step_id="remotion_step",
        name="Remotion Render",
        description="Rendered silent video",
        status=ProductionStepStatus.SUCCEEDED,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        input_summary="input",
        output_summary="silent video",
        artifacts=[silent_manifest_artifact],
    )
    mock_remotion_result = VideoExperimentResult(
        experimentId="remotion_exp",
        videoUrl="/runtime/remotion_exp/remotion_out.mp4",  # This is SILENT
        productionSteps=[silent_step],
    )

    # FFmpeg compose result
    mock_av_result = MagicMock()
    mock_av_result.get.return_value = {"success": True}

    with patch("app.video_lab.chains.remotion_tts_video.run_remotion_template", return_value=mock_remotion_result):
        with patch("app.video_lab.chains.remotion_tts_video.MiniMaxTTSClient") as mock_tts_cls:
            mock_tts = MagicMock()
            mock_tts.is_configured.return_value = True
            mock_tts.generate.return_value = {
                "success": True,
                "audioPath": "runtime/video_lab/experiments/remotion_exp/audio.mp3",
                "audioUrl": "/runtime/remotion_exp/audio.mp3",
                "durationSec": 45,
            }
            mock_tts_cls.return_value = mock_tts

            with patch("app.video_lab.chains.remotion_tts_video.compose_av_with_subtitles", return_value={"success": True}):
                with patch("app.video_lab.chains.remotion_tts_video.compose_video_with_audio", return_value={"success": True}):
                    with patch("app.video_lab.chains.remotion_tts_video.generate_voiceover", return_value={
                        "voiceoverText": "测试旁白",
                        "segments": [{"index": 1, "text": "测试旁白", "startSec": 0, "durationSec": 5}],
                    }):
                        with patch("app.video_lab.chains.remotion_tts_video.generate_srt_from_segments", return_value={
                            "subtitles": [], "srtUrl": "/runtime/remotion_exp/srt.srt",
                        }):
                            with patch("app.video_lab.chains.remotion_tts_video.check_ffmpeg_available", return_value=True):
                                with patch("app.video_lab.chains.remotion_tts_video.path_to_url", side_effect=lambda p: f"/runtime/{str(p).replace('runtime/', '')}"):
                                    result = run_remotion_tts_video(
                                        experiment_id="remotion_exp_final",
                                        test_case_id="case_ai_frontier_daily_001",
                                        input_payload={"content": "测试内容"},
                                        params={},
                                    )

    assert result.status == ChainStatus.SUCCEEDED, f"Expected SUCCEEDED, got {result.status}"
    # The final URL must NOT be the silent remotion video
    assert "final_with_audio.mp4" in result.final_video_url, \
        f"Expected final_with_audio.mp4 in URL, got {result.final_video_url}"
    assert "remotion_out.mp4" not in result.final_video_url, \
        "finalVideoUrl should NOT be the raw Remotion silent video"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
