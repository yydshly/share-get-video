"""
tests/test_video_lab_module_contract.py

V1.0 contract tests for Video Lab module freeze (hardened).

Covers:
- ErrorEnvelope.to_dict structure is stable
- error_response() returns success=false / status=failed / contractStatus / error / logs / warnings / artifacts / rawOutput
- RunContext auto-generates runId / experimentId
- RunContext defaults include logs / warnings
- ExperimentManifest success has schemaVersion=video-lab-experiment-v1
- ExperimentManifest failed includes error
- write_experiment_manifest writes under RUNTIME_DIR
- manifestUrl uses PUBLIC_RUNTIME_URL_PREFIX
- VisualProfile unknown profile falls back to ai_frontier_dark
- merge_visual_profile: explicit overrides beat profile defaults
- /clip-preview response has success/status/contractStatus/artifacts/error/rawOutput
- /clip-preview writes manifest even on failure
- /visual-compose on dependency failure returns unified failed/error structure
- /visual-compose outer exception returns V1 error envelope (not HTTP 500)
- result.logs merged into response.logs
- V1 artifacts contains finalVideoUrl / coverUrl / audioUrl / srtUrl / manifestUrl
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────
# 1. ErrorEnvelope structure
# ─────────────────────────────────────────
class TestErrorEnvelope:
    def test_to_dict_has_all_required_fields(self):
        from app.video_lab.errors import ErrorEnvelope

        env = ErrorEnvelope(
            type="RenderError",
            code="VIDEO_LAB_RENDER_FAILED",
            message="Remotion render failed",
            stage="visual_render",
            route="template_programmatic_render",
            recoverable=True,
            details={"code": 1},
        )
        d = env.to_dict()
        assert d["type"] == "RenderError"
        assert d["code"] == "VIDEO_LAB_RENDER_FAILED"
        assert d["message"] == "Remotion render failed"
        assert d["stage"] == "visual_render"
        assert d["route"] == "template_programmatic_render"
        assert d["recoverable"] is True
        assert d["details"] == {"code": 1}

    def test_make_error_returns_dict(self):
        from app.video_lab.errors import make_error

        err = make_error(
            "Something went wrong",
            type="ConfigError",
            code="VIDEO_LAB_CONFIG_ERROR",
            stage="config",
        )
        assert isinstance(err, dict)
        assert err["type"] == "ConfigError"
        assert err["code"] == "VIDEO_LAB_CONFIG_ERROR"
        assert err["message"] == "Something went wrong"

    def test_error_response_has_all_v1_fields(self):
        from app.video_lab.errors import error_response

        resp = error_response(
            message="Render failed",
            type="RenderError",
            code="VIDEO_LAB_RENDER_FAILED",
            stage="visual_render",
            route="template_programmatic_render",
            run_id="run_abc12345",
            experiment_id="exp_xyz",
            mode="compose",
            logs=["log line 1"],
            warnings=["warning line 1"],
        )
        assert resp["success"] is False
        assert resp["status"] == "failed"
        assert resp["runId"] == "run_abc12345"
        assert resp["experimentId"] == "exp_xyz"
        assert resp["mode"] == "compose"
        assert resp["routeId"] == "template_programmatic_render"
        assert resp["artifacts"] == {}
        assert resp["logs"] == ["log line 1"]
        assert resp["warnings"] == ["warning line 1"]
        assert resp["error"]["type"] == "RenderError"
        assert resp["rawOutput"] == {}


# ─────────────────────────────────────────
# 2. RunContext auto-generates IDs
# ─────────────────────────────────────────
class TestRunContext:
    def test_auto_generates_run_id(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="preview", route_id="template_programmatic_render")
        assert ctx.run_id != ""
        assert ctx.run_id.startswith("run_")

    def test_auto_generates_experiment_id(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="compose", route_id="local_frame_compose")
        assert ctx.experiment_id != ""
        assert ctx.experiment_id.startswith("exp_")

    def test_defaults_have_logs_and_warnings(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="probe", route_id="ai_asset_then_compose")
        assert isinstance(ctx.logs, list)
        assert isinstance(ctx.warnings, list)
        assert ctx.logs == []
        assert ctx.warnings == []

    def test_to_dict_has_schema_version(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="sweep", route_id="template_programmatic_render")
        d = ctx.to_dict()
        assert d["schemaVersion"] == "video-lab-run-context-v1"
        assert "runId" in d
        assert "experimentId" in d
        assert "mode" in d
        assert "routeId" in d
        assert "status" in d
        assert "artifacts" in d
        assert "logs" in d
        assert "warnings" in d

    def test_to_response_base(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="preview", route_id="local_frame_compose")
        ctx.log("line 1")
        ctx.warn("warn 1")
        base = ctx.to_response_base()
        assert base["mode"] == "preview"
        assert base["routeId"] == "local_frame_compose"
        assert base["logs"] == ["line 1"]
        assert base["warnings"] == ["warn 1"]

    def test_log_and_warn_helpers(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="compose", route_id="template_programmatic_render")
        ctx.log("step 1 completed")
        ctx.warn("disk space low")
        assert ctx.logs == ["step 1 completed"]
        assert ctx.warnings == ["disk space low"]

    def test_mark_success_updates_status(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="compose", route_id="template_programmatic_render")
        assert ctx.status == "running"
        ctx.mark_success()
        assert ctx.status == "success"

    def test_mark_failed_updates_status(self):
        from app.video_lab.run_context import RunContext

        ctx = RunContext(mode="preview", route_id="template_programmatic_render")
        assert ctx.status == "running"
        ctx.mark_failed()
        assert ctx.status == "failed"


# ─────────────────────────────────────────
# 3. ExperimentManifest
# ─────────────────────────────────────────
class TestExperimentManifest:
    def test_success_has_schema_version(self):
        from app.video_lab.experiment_manifest import build_experiment_manifest

        m = build_experiment_manifest(
            experiment_id="exp_test",
            run_id="run_test",
            mode="compose",
            route_id="template_programmatic_render",
            status="success",
        )
        assert m["schemaVersion"] == "video-lab-experiment-v1"
        assert m["experimentId"] == "exp_test"
        assert m["runId"] == "run_test"
        assert m["mode"] == "compose"
        assert m["status"] == "success"

    def test_failed_includes_error(self):
        from app.video_lab.experiment_manifest import build_experiment_manifest
        from app.video_lab.errors import make_error

        err = make_error("TTS failed", type="TTSError", code="VIDEO_LAB_TTS_FAILED")
        m = build_experiment_manifest(
            experiment_id="exp_test",
            run_id="run_test",
            mode="compose",
            route_id="template_programmatic_render",
            status="failed",
            error=err,
        )
        assert m["status"] == "failed"
        assert m["error"] is not None
        assert m["error"]["type"] == "TTSError"

    def test_manifest_has_all_artifact_slots(self):
        from app.video_lab.experiment_manifest import build_experiment_manifest

        m = build_experiment_manifest(
            experiment_id="exp_test",
            run_id="run_test",
            mode="compose",
            route_id="template_programmatic_render",
            status="success",
        )
        arts = m["artifacts"]
        assert "cover" in arts
        assert "frames" in arts
        assert "silentVideo" in arts
        assert "audio" in arts
        assert "subtitles" in arts
        assert "finalVideo" in arts
        assert "manifest" in arts

    def test_write_writes_under_runtime_dir(self, monkeypatch, tmp_path):
        import importlib
        import app.video_lab.config as config_module
        import app.video_lab.renderers.file_store as file_store_module
        import app.video_lab.experiment_manifest as manifest_module

        custom_runtime = tmp_path / "test-runtime"
        custom_runtime.mkdir()

        monkeypatch.setenv("VIDEO_LAB_RUNTIME_DIR", str(custom_runtime))
        monkeypatch.setenv("PUBLIC_RUNTIME_URL_PREFIX", "/runtime")

        importlib.reload(config_module)
        importlib.reload(file_store_module)
        importlib.reload(manifest_module)

        from app.video_lab.experiment_manifest import write_experiment_manifest
        from app.video_lab.config import RUNTIME_DIR

        m = {
            "schemaVersion": "video-lab-experiment-v1",
            "experimentId": "exp_write_test",
            "runId": "run_write_test",
            "mode": "compose",
            "routeId": "template_programmatic_render",
            "status": "success",
            "artifacts": {},
            "logs": [],
            "warnings": [],
            "error": None,
            "rawOutput": {},
            "createdAt": "2024-01-01T00:00:00",
        }

        result = write_experiment_manifest("exp_write_test", m)

        assert Path(result["path"]).exists()
        assert result["url"].startswith("/runtime/")
        assert "exp_write_test" in result["path"]

        # Restore
        monkeypatch.delenv("VIDEO_LAB_RUNTIME_DIR", raising=False)
        monkeypatch.delenv("PUBLIC_RUNTIME_URL_PREFIX", raising=False)
        importlib.reload(config_module)
        importlib.reload(file_store_module)
        importlib.reload(manifest_module)


# ─────────────────────────────────────────
# 4. VisualProfile
# ─────────────────────────────────────────
class TestVisualProfile:
    def test_unknown_profile_falls_back_to_default(self):
        from app.video_lab.renderers.visual_profiles import get_visual_profile, DEFAULT_PROFILE_ID

        profile, warnings = get_visual_profile("nonexistent_profile_xyz")
        assert profile["id"] == DEFAULT_PROFILE_ID
        assert len(warnings) == 1
        assert "nonexistent_profile_xyz" in warnings[0]

    def test_none_profile_falls_back_to_default(self):
        from app.video_lab.renderers.visual_profiles import get_visual_profile, DEFAULT_PROFILE_ID

        profile, warnings = get_visual_profile(None)
        assert profile["id"] == DEFAULT_PROFILE_ID
        assert warnings == []

    def test_known_profile_no_warning(self):
        from app.video_lab.renderers.visual_profiles import get_visual_profile

        profile, warnings = get_visual_profile("data_card_dense")
        assert profile["id"] == "data_card_dense"
        assert warnings == []

    def test_merge_overrides_beat_defaults(self):
        from app.video_lab.renderers.visual_profiles import merge_visual_profile

        merged, warnings = merge_visual_profile(
            "ai_frontier_dark",
            {"motionIntensity": "low", "showDataViz": False},
        )
        assert merged["motionIntensity"] == "low"
        assert merged["showDataViz"] is False
        # un-overridden defaults still present
        assert merged["contentAlign"] == "center"
        assert merged["visualProfile"] == "ai_frontier_dark"

    def test_merge_unknown_profile_warns(self):
        from app.video_lab.renderers.visual_profiles import merge_visual_profile

        merged, warnings = merge_visual_profile(
            "totally_unknown_profile",
            {"showDataViz": True},
        )
        assert merged["visualProfile"] == "ai_frontier_dark"
        assert any("totally_unknown_profile" in w for w in warnings)

    def test_all_profiles_have_required_keys(self):
        from app.video_lab.renderers.visual_profiles import VISUAL_PROFILES

        required_keys = {"id", "label", "description", "defaults"}
        for pid, profile in VISUAL_PROFILES.items():
            assert required_keys.issubset(profile.keys()), f"{pid} missing keys"
            assert isinstance(profile["defaults"], dict)


# ─────────────────────────────────────────
# 5. /clip-preview contract (mocked)
# ─────────────────────────────────────────
class TestClipPreviewContract:
    def test_clip_preview_success_returns_v1_contract(self):
        from app.video_lab.router import clip_preview
        from app.video_lab.schemas import ClipPreviewRequest

        mock_result = {
            "success": True,
            "route": "template_programmatic_render",
            "clipUrl": "/runtime/video_lab/experiments/abc/clip.mp4",
            "warnings": [],
            "elapsedMs": 5000,
        }

        with patch("app.video_lab.renderers.frame_preview.render_clip_preview", return_value=mock_result):
            with patch("app.video_lab.router.write_experiment_manifest") as mock_write:
                mock_write.return_value = {"path": "/p/manifest.json", "url": "/runtime/manifest.json"}
                req = ClipPreviewRequest(
                    visualRoute="template_programmatic_render",
                    content="Test content",
                    params={"clipSeconds": 3},
                )
                resp = clip_preview(req)

        assert resp["success"] is True
        assert resp["status"] == "success"
        assert resp["contractStatus"] == "success"
        assert "runId" in resp
        assert "experimentId" in resp
        assert "artifacts" in resp
        assert resp["artifacts"]["videoUrl"] == "/runtime/video_lab/experiments/abc/clip.mp4"
        assert "manifestUrl" in resp["artifacts"]
        assert "error" in resp
        assert resp["error"] is None
        assert "rawOutput" in resp
        # Manifest should have been written
        mock_write.assert_called_once()

    def test_clip_preview_failure_returns_v1_contract(self):
        from app.video_lab.router import clip_preview
        from app.video_lab.schemas import ClipPreviewRequest

        mock_result = {
            "success": False,
            "route": "template_programmatic_render",
            "message": "Remotion render failed: Chrome failed to launch",
            "warnings": [],
            "elapsedMs": 3000,
        }

        with patch("app.video_lab.renderers.frame_preview.render_clip_preview", return_value=mock_result):
            with patch("app.video_lab.router.write_experiment_manifest") as mock_write:
                mock_write.return_value = {"path": "/p/manifest.json", "url": "/runtime/manifest.json"}
                req = ClipPreviewRequest(
                    visualRoute="template_programmatic_render",
                    content="Test content",
                    params={},
                )
                resp = clip_preview(req)

        assert resp["success"] is False
        assert resp["status"] == "failed"
        assert resp["contractStatus"] == "failed"
        assert "runId" in resp
        assert "experimentId" in resp
        assert "artifacts" in resp
        assert resp["artifacts"] == {"videoUrl": "", "coverUrl": "", "manifestUrl": "/runtime/manifest.json"}
        assert "error" in resp
        assert resp["error"] is not None
        assert resp["error"]["type"] == "RenderError"
        assert "Chrome failed to launch" in resp["error"]["message"]
        mock_write.assert_called_once()  # manifest written even on failure

    def test_clip_preview_exception_returns_v1_contract(self):
        from app.video_lab.router import clip_preview
        from app.video_lab.schemas import ClipPreviewRequest

        with patch(
            "app.video_lab.renderers.frame_preview.render_clip_preview",
            side_effect=RuntimeError("Unexpected error"),
        ):
            with patch("app.video_lab.router.write_experiment_manifest") as mock_write:
                mock_write.return_value = {"path": "/p/manifest.json", "url": "/runtime/manifest.json"}
                req = ClipPreviewRequest(
                    visualRoute="template_programmatic_render",
                    content="Test content",
                    params={},
                )
                resp = clip_preview(req)

        assert resp["success"] is False
        assert resp["status"] == "failed"
        assert resp["contractStatus"] == "failed"
        assert "runId" in resp
        assert "experimentId" in resp
        assert "error" in resp
        assert resp["error"]["code"] == "VIDEO_LAB_INTERNAL_ERROR"

    def test_clip_preview_visual_profile_warning_merged(self):
        """Unknown visualProfile in params adds warning to response."""
        from app.video_lab.router import clip_preview
        from app.video_lab.schemas import ClipPreviewRequest

        mock_result = {
            "success": True,
            "route": "template_programmatic_render",
            "clipUrl": "/runtime/video_lab/experiments/abc/clip.mp4",
            "warnings": [],
            "elapsedMs": 5000,
        }

        with patch("app.video_lab.renderers.frame_preview.render_clip_preview", return_value=mock_result):
            with patch("app.video_lab.router.write_experiment_manifest") as mock_write:
                mock_write.return_value = {"path": "/p/manifest.json", "url": "/runtime/manifest.json"}
                req = ClipPreviewRequest(
                    visualRoute="template_programmatic_render",
                    content="Test content",
                    params={"visualProfile": "nonexistent_profile_xyz"},
                )
                resp = clip_preview(req)

        # Unknown profile should have produced a warning
        assert resp["success"] is True
        assert any("nonexistent_profile_xyz" in w for w in resp["warnings"])


# ─────────────────────────────────────────
# 6. /visual-compose contract (mocked)
# ─────────────────────────────────────────
class TestVisualComposeContract:
    def test_visual_compose_success_returns_v1_fields(self):
        from app.video_lab.router import _run_visual_compose

        mock_result = MagicMock()
        mock_result.rawOutput = {"status": "succeeded", "quality": {"overallScore": 0.85}}
        mock_result.assets = {"audioDurationSec": 45.0, "subtitleCount": 12}
        mock_result.productionSteps = []
        mock_result.logs = ["step 1 done", "step 2 done"]
        mock_result.videoUrl = "/runtime/video_lab/experiments/abc/final.mp4"
        mock_result.coverUrl = "/runtime/video_lab/experiments/abc/cover.jpg"

        with patch(
            "app.video_lab.adapters.tts_subtitle_compose.run_tts_subtitle_compose",
            return_value=mock_result,
        ):
            with patch("app.video_lab.quality.quality_log.append_record"):
                with patch(
                    "app.video_lab.router.write_experiment_manifest",
                    return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
                ) as mock_write:
                    resp = _run_visual_compose(
                        "Test content", "template_programmatic_render", {}
                    )

        assert resp["success"] is True
        assert resp["status"] == "succeeded"
        assert resp["contractStatus"] == "success"
        assert "runId" in resp
        assert "experimentId" in resp
        assert "artifacts" in resp
        assert "finalVideoUrl" in resp["artifacts"]
        assert "coverUrl" in resp["artifacts"]
        assert "audioUrl" in resp["artifacts"]
        assert "srtUrl" in resp["artifacts"]
        assert "manifestUrl" in resp["artifacts"]
        assert resp["artifacts"]["finalVideoUrl"] == "/runtime/video_lab/experiments/abc/final.mp4"
        assert "error" in resp
        assert resp["error"] is None
        assert "rawOutput" in resp
        # result.logs should be merged into response.logs
        assert any("step 1 done" in l for l in resp["logs"])
        mock_write.assert_called_once()

    def test_visual_compose_failure_returns_error_envelope(self):
        from app.video_lab.router import _run_visual_compose

        mock_result = MagicMock()
        mock_result.rawOutput = {
            "status": "failed",
            "error": "MiniMax API key not configured",
        }
        mock_result.assets = {}
        mock_result.productionSteps = []
        mock_result.logs = []

        with patch(
            "app.video_lab.adapters.tts_subtitle_compose.run_tts_subtitle_compose",
            return_value=mock_result,
        ):
            with patch(
                "app.video_lab.router.write_experiment_manifest",
                return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
            ):
                resp = _run_visual_compose(
                    "Test content", "template_programmatic_render", {}
                )

        assert resp["success"] is False
        assert resp["status"] == "failed"
        assert resp["contractStatus"] == "failed"
        assert "runId" in resp
        assert "experimentId" in resp
        assert "error" in resp
        assert resp["error"] is not None
        assert "artifacts" in resp
        assert "rawOutput" in resp
        # V1 artifacts should still have available assets
        assert "finalVideoUrl" in resp["artifacts"]

    def test_visual_compose_visual_profile_unknown_warns(self):
        """Unknown visualProfile adds warning to response but does not fail."""
        from app.video_lab.router import _run_visual_compose

        mock_result = MagicMock()
        mock_result.rawOutput = {"status": "succeeded", "quality": {}}
        mock_result.assets = {}
        mock_result.productionSteps = []
        mock_result.logs = []
        mock_result.videoUrl = "/runtime/video_lab/experiments/abc/final.mp4"
        mock_result.coverUrl = ""

        with patch(
            "app.video_lab.adapters.tts_subtitle_compose.run_tts_subtitle_compose",
            return_value=mock_result,
        ):
            with patch("app.video_lab.quality.quality_log.append_record"):
                with patch(
                    "app.video_lab.router.write_experiment_manifest",
                    return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
                ):
                    resp = _run_visual_compose(
                        "Test content",
                        "template_programmatic_render",
                        {"visualProfile": "nonexistent_profile_xyz"},
                    )

        assert resp["success"] is True
        assert any("nonexistent_profile_xyz" in w for w in resp["warnings"])

    def test_visual_compose_result_logs_merged(self):
        """result.logs are deduplicated and merged into response.logs."""
        from app.video_lab.router import _run_visual_compose

        mock_result = MagicMock()
        mock_result.rawOutput = {"status": "succeeded", "quality": {}}
        mock_result.assets = {}
        mock_result.productionSteps = []
        mock_result.logs = ["factory step alpha", "factory step beta"]
        mock_result.videoUrl = "/runtime/video_lab/experiments/abc/final.mp4"
        mock_result.coverUrl = ""

        with patch(
            "app.video_lab.adapters.tts_subtitle_compose.run_tts_subtitle_compose",
            return_value=mock_result,
        ):
            with patch("app.video_lab.quality.quality_log.append_record"):
                with patch(
                    "app.video_lab.router.write_experiment_manifest",
                    return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
                ):
                    resp = _run_visual_compose("Test content", "template_programmatic_render", {})

        assert "factory step alpha" in resp["logs"]
        assert "factory step beta" in resp["logs"]


class TestVisualComposeOuterException:
    def test_visual_compose_outer_exception_returns_v1_envelope(self):
        """visual_compose outer exception returns V1 error envelope, not HTTP 500."""
        from app.video_lab.router import visual_compose
        from app.video_lab.schemas import VisualComposeRequest

        with patch(
            "app.video_lab.router._run_visual_compose",
            side_effect=RuntimeError("Database connection failed"),
        ):
            req = VisualComposeRequest(
                content="Test content",
                visualRoute="template_programmatic_render",
                params={},
            )
            resp = visual_compose(req)

        # Must be a V1 response, not an HTTPException
        assert resp["success"] is False
        assert resp["status"] == "failed"
        assert resp["contractStatus"] == "failed"
        assert "runId" in resp
        assert "experimentId" in resp
        assert "error" in resp
        assert resp["error"]["code"] == "VIDEO_LAB_INTERNAL_ERROR"
        assert resp["error"]["type"] == "RuntimeError"
        assert "artifacts" in resp
        assert resp["artifacts"] == {}
        assert "rawOutput" in resp
