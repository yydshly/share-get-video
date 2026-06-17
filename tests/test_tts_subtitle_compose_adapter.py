"""
Tests for run_tts_subtitle_compose adapter — V1.2.3 P1A fix.

Verifies that visual_route is resolved before Step 6 (subtitle generation),
preventing UnboundLocalError.
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
from app.video_lab.models import ProductionStepStatus


def _mock_visual_render_result():
    """Return a minimal mock VisualRenderResult."""
    result = MagicMock()
    result.success = True
    result.silent_video_path = str(Path(tempfile.gettempdir()) / "silent.mp4")
    result.silent_video_url = "file:///tmp/silent.mp4"
    result.cover_path = None
    result.frame_count = 30
    result.total_duration_sec = 10.0
    result.warnings = []
    result.logs = ["[visual] rendered 30 frames"]
    return result


def _mock_audio_result():
    """Return a minimal mock TTS audio result."""
    result = MagicMock()
    result.get.return_value = {
        "success": True,
        "audioPath": str(Path(tempfile.gettempdir()) / "voiceover.mp3"),
        "durationSec": 10.0,
        "providerMessage": "mocked",
    }
    return result


def _mock_av_compose_result():
    """Return a minimal mock AV compose result."""
    result = MagicMock()
    result.get.return_value = {
        "success": True,
        "subtitle_renderer": "ass",
        "subtitle_style": {},
        "bgm_enabled": False,
        "bgm_mode": "none",
        "bgm_volume": 0.0,
    }
    return result


class TestVisualRouteResolvedBeforeStep6:
    """Test: visual_route is bound before Step 6, not after."""

    @patch("app.video_lab.adapters.tts_subtitle_compose.MiniMaxTTSClient")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_av_with_subtitles")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_video_with_audio")
    @patch("app.video_lab.adapters.tts_subtitle_compose.write_manifest")
    @patch("app.video_lab.quality.assess_quality")
    @patch("app.video_lab.renderers.visual.get_visual_renderer")
    def test_ai_asset_route_no_unbound_error(
        self,
        mock_get_renderer,
        mock_assess,
        mock_compose_av,
        mock_compose_video,
        mock_write_manifest,
        MockTTSClient,
    ):
        """run_tts_subtitle_compose with visualRoute=ai_asset_then_compose must not raise UnboundLocalError."""
        mock_tts_instance = MagicMock()
        mock_tts_instance.is_configured.return_value = True
        mock_tts_instance.generate.return_value = {
            "success": True,
            "audioPath": str(Path(tempfile.gettempdir()) / "vo.mp3"),
            "durationSec": 10.0,
            "providerMessage": "mock",
        }
        MockTTSClient.return_value = mock_tts_instance

        # Setup mock visual renderer
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = _mock_visual_render_result()
        mock_get_renderer.return_value = mock_renderer

        # Setup mock AV compose
        mock_compose_av.return_value = _mock_av_compose_result()
        mock_compose_video.return_value = {"success": True}

        # Setup mock quality
        mock_assess.return_value = MagicMock(to_dict=lambda: {
            "overallScore": 0.8,
            "dimensionScores": {},
            "counts": {},
        })

        params = {
            "aspectRatio": "9:16",
            "targetDuration": 20,
            "keyPointCount": 2,
            "useLlmPlan": False,
            "visualRoute": "ai_asset_then_compose",
        }
        input_payload = {"content": "这是一段测试内容，用于验证字幕生成是否正常工作。"}

        # This must not raise UnboundLocalError
        result = run_tts_subtitle_compose(
            experiment_id="test_exp_001",
            test_case_id="test_case_001",
            input_payload=input_payload,
            params=params,
        )

        # Should have proceeded past Step 6 without UnboundLocalError
        step6 = next((s for s in result.productionSteps if s.id.endswith("_step_06_subtitles")), None)
        assert step6 is not None, "Step 6 not found — likely UnboundLocalError was raised before this point"
        assert step6.status == ProductionStepStatus.SUCCEEDED

    @patch("app.video_lab.adapters.tts_subtitle_compose.MiniMaxTTSClient")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_av_with_subtitles")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_video_with_audio")
    @patch("app.video_lab.adapters.tts_subtitle_compose.write_manifest")
    @patch("app.video_lab.quality.assess_quality")
    @patch("app.video_lab.renderers.visual.get_visual_renderer")
    def test_remotion_route_no_unbound_error(
        self,
        mock_get_renderer,
        mock_assess,
        mock_compose_av,
        mock_compose_video,
        mock_write_manifest,
        MockTTSClient,
    ):
        """run_tts_subtitle_compose with visualRoute=template_programmatic_render must not raise."""
        mock_tts_instance = MagicMock()
        mock_tts_instance.is_configured.return_value = True
        mock_tts_instance.generate.return_value = {
            "success": True,
            "audioPath": str(Path(tempfile.gettempdir()) / "vo.mp3"),
            "durationSec": 10.0,
            "providerMessage": "mock",
        }
        MockTTSClient.return_value = mock_tts_instance

        mock_renderer = MagicMock()
        mock_renderer.render.return_value = _mock_visual_render_result()
        mock_get_renderer.return_value = mock_renderer

        mock_compose_av.return_value = _mock_av_compose_result()
        mock_compose_video.return_value = {"success": True}
        mock_assess.return_value = MagicMock(to_dict=lambda: {
            "overallScore": 0.8,
            "dimensionScores": {},
            "counts": {},
        })

        params = {
            "aspectRatio": "9:16",
            "targetDuration": 20,
            "keyPointCount": 2,
            "useLlmPlan": False,
            "visualRoute": "template_programmatic_render",
        }
        result = run_tts_subtitle_compose(
            experiment_id="test_exp_002",
            test_case_id="test_case_002",
            input_payload={"content": "Remotion路线测试内容。"},
            params=params,
        )

        raw = result.rawOutput or {}
        assert "subtitleDiagnostics" in raw
        assert "subtitleStyle" in raw
        step6 = next((s for s in result.productionSteps if s.id.endswith("_step_06_subtitles")), None)
        assert step6 is not None
        assert step6.status == ProductionStepStatus.SUCCEEDED

    @patch("app.video_lab.adapters.tts_subtitle_compose.MiniMaxTTSClient")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_av_with_subtitles")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_video_with_audio")
    @patch("app.video_lab.adapters.tts_subtitle_compose.write_manifest")
    @patch("app.video_lab.quality.assess_quality")
    @patch("app.video_lab.renderers.visual.get_visual_renderer")
    def test_pillow_route_no_unbound_error(
        self,
        mock_get_renderer,
        mock_assess,
        mock_compose_av,
        mock_compose_video,
        mock_write_manifest,
        MockTTSClient,
    ):
        """run_tts_subtitle_compose with visualRoute=local_frame_compose must not raise."""
        mock_tts_instance = MagicMock()
        mock_tts_instance.is_configured.return_value = True
        mock_tts_instance.generate.return_value = {
            "success": True,
            "audioPath": str(Path(tempfile.gettempdir()) / "vo.mp3"),
            "durationSec": 10.0,
            "providerMessage": "mock",
        }
        MockTTSClient.return_value = mock_tts_instance

        mock_renderer = MagicMock()
        mock_renderer.render.return_value = _mock_visual_render_result()
        mock_get_renderer.return_value = mock_renderer

        mock_compose_av.return_value = _mock_av_compose_result()
        mock_compose_video.return_value = {"success": True}
        mock_assess.return_value = MagicMock(to_dict=lambda: {
            "overallScore": 0.8,
            "dimensionScores": {},
            "counts": {},
        })

        params = {
            "aspectRatio": "9:16",
            "targetDuration": 20,
            "keyPointCount": 2,
            "useLlmPlan": False,
            "visualRoute": "local_frame_compose",
        }
        result = run_tts_subtitle_compose(
            experiment_id="test_exp_003",
            test_case_id="test_case_003",
            input_payload={"content": "Pillow路线测试内容。"},
            params=params,
        )

        raw = result.rawOutput or {}
        assert "subtitleDiagnostics" in raw
        assert "subtitleStyle" in raw
        step6 = next((s for s in result.productionSteps if s.id.endswith("_step_06_subtitles")), None)
        assert step6 is not None
        assert step6.status == ProductionStepStatus.SUCCEEDED

    @patch("app.video_lab.adapters.tts_subtitle_compose.MiniMaxTTSClient")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_av_with_subtitles")
    @patch("app.video_lab.adapters.tts_subtitle_compose.compose_video_with_audio")
    @patch("app.video_lab.adapters.tts_subtitle_compose.write_manifest")
    @patch("app.video_lab.quality.assess_quality")
    @patch("app.video_lab.renderers.visual.get_visual_renderer")
    def test_step6_and_step7_use_same_effective_route(
        self,
        mock_get_renderer,
        mock_assess,
        mock_compose_av,
        mock_compose_video,
        mock_write_manifest,
        MockTTSClient,
    ):
        """Step 6 subtitle style route must match Step 7 visual route (no re-resolution)."""
        mock_tts_instance = MagicMock()
        mock_tts_instance.is_configured.return_value = True
        mock_tts_instance.generate.return_value = {
            "success": True,
            "audioPath": str(Path(tempfile.gettempdir()) / "vo.mp3"),
            "durationSec": 10.0,
            "providerMessage": "mock",
        }
        MockTTSClient.return_value = mock_tts_instance

        mock_renderer = MagicMock()
        mock_renderer.render.return_value = _mock_visual_render_result()
        mock_get_renderer.return_value = mock_renderer

        mock_compose_av.return_value = _mock_av_compose_result()
        mock_compose_video.return_value = {"success": True}
        mock_assess.return_value = MagicMock(to_dict=lambda: {
            "overallScore": 0.8,
            "dimensionScores": {},
            "counts": {},
        })

        params = {
            "aspectRatio": "9:16",
            "targetDuration": 20,
            "keyPointCount": 2,
            "useLlmPlan": False,
            "visualRoute": "ai_asset_then_compose",
        }
        result = run_tts_subtitle_compose(
            experiment_id="test_exp_004",
            test_case_id="test_case_004",
            input_payload={"content": "验证 Step 6 和 Step 7 使用相同 route 的测试内容。"},
            params=params,
        )

        # Step 6 log should contain the route
        step6 = next((s for s in result.productionSteps if s.id.endswith("_step_06_subtitles")), None)
        assert step6 is not None
        step6_log = " ".join(step6.logs)
        assert "ai_asset_then_compose" in step6_log, f"Step 6 should use ai_asset_then_compose, got: {step6_log}"

        # Step 7 log should also contain the same route
        step7 = next((s for s in result.productionSteps if s.id.endswith("_step_07_silent_video")), None)
        assert step7 is not None
        step7_log = " ".join(step7.logs)
        assert "ai_asset_then_compose" in step7_log, f"Step 7 should use ai_asset_then_compose, got: {step7_log}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
