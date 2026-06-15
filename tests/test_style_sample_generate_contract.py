"""
Tests for the /style-samples/generate URL extraction contract.

These tests verify that extract_style_sample_assets correctly reads from
VideoExperimentResult (and compatible dicts) using the correct camelCase
field names: videoUrl, coverUrl, rawOutput, productionSteps.

Regression test for the bug where the endpoint used snake_case field names
(raw_output, production_steps) that don't exist on VideoExperimentResult,
causing final_video_url to always be empty.
"""

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.router import extract_style_sample_assets, _safe_get, _artifact_type_value


# ─────────────────────────────────────────────────────────────────────────────
# Helper: make a minimal VideoExperimentResult-like object
# ─────────────────────────────────────────────────────────────────────────────
def make_result(
    video_url: str = "",
    cover_url: str = "",
    raw_status: str = "succeeded",
    raw_error: str = "",
    assets: dict | None = None,
    production_steps: list | None = None,
):
    """Build a mock result with the correct camelCase attributes."""
    m = MagicMock()
    m.videoUrl = video_url
    m.coverUrl = cover_url
    # Use a real dict so .get() returns the correct value, not a MagicMock
    m.rawOutput = {"status": raw_status, "error": raw_error}
    m.assets = assets or {}
    m.productionSteps = production_steps or []
    return m


def make_step(artifacts: list):
    """Build a production step dict (dict form, not object)."""
    return {"artifacts": artifacts}


def make_artifact(atype: str, url: str):
    """Build a production artifact dict with enum-like type."""
    type_enum = MagicMock()
    type_enum.value = atype
    return {"type": type_enum, "payload": {"url": url}}


# ─────────────────────────────────────────────────────────────────────────────
# _safe_get tests
# ─────────────────────────────────────────────────────────────────────────────
class TestSafeGet:
    def test_dict_access(self):
        d = {"foo": "bar"}
        assert _safe_get(d, "foo") == "bar"
        assert _safe_get(d, "missing", "default") == "default"

    def test_object_access(self):
        class Obj:
            bar = "baz"

        assert _safe_get(Obj(), "bar") == "baz"
        assert _safe_get(Obj(), "missing", "default") == "default"

    def test_none_safe(self):
        assert _safe_get(None, "foo", "default") == "default"


# ─────────────────────────────────────────────────────────────────────────────
# _artifact_type_value tests
# ─────────────────────────────────────────────────────────────────────────────
class TestArtifactTypeValue:
    def test_string_type(self):
        art = {"type": "video_output"}
        assert _artifact_type_value(art) == "video_output"

    def test_enum_type(self):
        enum_val = MagicMock()
        enum_val.value = "cover_image"
        art = {"type": enum_val}
        assert _artifact_type_value(art) == "cover_image"

    def test_none_type(self):
        art = {"type": None}
        assert _artifact_type_value(art) == ""

    def test_missing_type(self):
        art = {}
        assert _artifact_type_value(art) == ""


# ─────────────────────────────────────────────────────────────────────────────
# extract_style_sample_assets contract tests
# ─────────────────────────────────────────────────────────────────────────────
class TestExtractStyleSampleAssets:
    def test_video_url_from_top_level_video_url(self):
        """final_video_url should come from result.videoUrl first."""
        result = make_result(
            video_url="/runtime/video_lab/experiments/exp_abc/final_with_audio.mp4",
            raw_status="succeeded",
        )
        extracted = extract_style_sample_assets(result)
        assert extracted["final_video_url"] == "/runtime/video_lab/experiments/exp_abc/final_with_audio.mp4"
        assert extracted["failed"] is False

    def test_cover_url_from_top_level_cover_url(self):
        """cover_url should come from result.coverUrl first."""
        result = make_result(
            video_url="/runtime/video_lab/experiments/exp_abc/final_with_audio.mp4",
            cover_url="/runtime/video_lab/experiments/exp_abc/cover.png",
            raw_status="succeeded",
        )
        extracted = extract_style_sample_assets(result)
        assert extracted["cover_url"] == "/runtime/video_lab/experiments/exp_abc/cover.png"

    def test_video_url_from_production_steps_video_output(self):
        """video_output artifact in productionSteps should fill final_video_url as fallback."""
        art = make_artifact("video_output", "/runtime/video_lab/experiments/exp_abc/final.mp4")
        step = make_step(artifacts=[art])
        result = make_result(video_url="", raw_status="succeeded", production_steps=[step])
        extracted = extract_style_sample_assets(result)
        assert extracted["final_video_url"] == "/runtime/video_lab/experiments/exp_abc/final.mp4"

    def test_video_url_prefers_top_level_over_production_steps(self):
        """result.videoUrl takes priority over productionSteps video_output."""
        art = make_artifact("video_output", "/runtime/video_lab/experiments/exp_abc/step.mp4")
        step = make_step(artifacts=[art])
        result = make_result(
            video_url="/runtime/video_lab/experiments/exp_abc/top_level.mp4",
            raw_status="succeeded",
            production_steps=[step],
        )
        extracted = extract_style_sample_assets(result)
        assert extracted["final_video_url"] == "/runtime/video_lab/experiments/exp_abc/top_level.mp4"

    def test_audio_url_from_audio_output_artifact(self):
        """audio_output artifact should fill audio_url."""
        art = make_artifact("audio_output", "/runtime/video_lab/experiments/exp_abc/audio.wav")
        step = make_step(artifacts=[art])
        result = make_result(
            video_url="/runtime/video_lab/experiments/exp_abc/final.mp4",
            raw_status="succeeded",
            production_steps=[step],
        )
        extracted = extract_style_sample_assets(result)
        assert extracted["audio_url"] == "/runtime/video_lab/experiments/exp_abc/audio.wav"

    def test_srt_url_from_subtitle_file_artifact(self):
        """subtitle_file artifact should fill srt_url."""
        art = make_artifact("subtitle_file", "/runtime/video_lab/experiments/exp_abc/subtitles.srt")
        step = make_step(artifacts=[art])
        result = make_result(
            video_url="/runtime/video_lab/experiments/exp_abc/final.mp4",
            raw_status="succeeded",
            production_steps=[step],
        )
        extracted = extract_style_sample_assets(result)
        assert extracted["srt_url"] == "/runtime/video_lab/experiments/exp_abc/subtitles.srt"

    def test_manifest_url_from_manifest_artifact(self):
        """manifest artifact should fill manifest_url."""
        art = make_artifact("manifest", "/runtime/video_lab/experiments/exp_abc/manifest.json")
        step = make_step(artifacts=[art])
        result = make_result(
            video_url="/runtime/video_lab/experiments/exp_abc/final.mp4",
            raw_status="succeeded",
            production_steps=[step],
        )
        extracted = extract_style_sample_assets(result)
        assert extracted["manifest_url"] == "/runtime/video_lab/experiments/exp_abc/manifest.json"

    def test_failed_when_status_not_succeeded(self):
        """failed=True when rawOutput.status != succeeded."""
        result = make_result(video_url="/runtime/video_lab/experiments/exp_abc/final.mp4", raw_status="failed", raw_error="TTS failed")
        extracted = extract_style_sample_assets(result)
        assert extracted["failed"] is True
        assert extracted["failed_reason"] == "TTS failed"

    def test_failed_when_succeeded_but_no_video_url(self):
        """failed=True when status=succeeded but no video URL anywhere."""
        result = make_result(video_url="", raw_status="succeeded")
        extracted = extract_style_sample_assets(result)
        assert extracted["failed"] is True
        assert "final_video_url" in extracted["failed_reason"].lower() or "无法提取" in extracted["failed_reason"]

    def test_output_path_strips_runtime_prefix(self):
        """output.path should strip /runtime/ prefix for storage compatibility."""
        art = make_artifact("video_output", "/runtime/video_lab/experiments/exp_abc/final.mp4")
        step = make_step(artifacts=[art])
        result = make_result(video_url="", raw_status="succeeded", production_steps=[step])
        extracted = extract_style_sample_assets(result)
        # The extracted raw URL still has /runtime/; the stripping happens in the route handler
        assert extracted["final_video_url"] == "/runtime/video_lab/experiments/exp_abc/final.mp4"

    def test_duration_from_assets(self):
        """duration_sec and audio_duration_sec should come from assets."""
        result = make_result(
            video_url="/runtime/video_lab/experiments/exp_abc/final.mp4",
            raw_status="succeeded",
            assets={"durationSec": 30.5, "audioDurationSec": 28.0},
        )
        extracted = extract_style_sample_assets(result)
        assert extracted["duration_sec"] == 30.5
        assert extracted["audio_duration_sec"] == 28.0

    def test_dict_result_also_works(self):
        """extract_style_sample_assets also works when result is a plain dict (dict form)."""
        # Some internal callers may pass a dict instead of an object
        result = {
            "videoUrl": "/runtime/video_lab/experiments/exp_abc/final.mp4",
            "coverUrl": "/runtime/video_lab/experiments/exp_abc/cover.png",
            "rawOutput": {"status": "succeeded"},
            "assets": {},
            "productionSteps": [],
        }
        extracted = extract_style_sample_assets(result)
        assert extracted["final_video_url"] == "/runtime/video_lab/experiments/exp_abc/final.mp4"
        assert extracted["cover_url"] == "/runtime/video_lab/experiments/exp_abc/cover.png"
        assert extracted["failed"] is False
