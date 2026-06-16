"""
Tests for JobRun v1 contract (V1.0.4).

Covers:
- JobRun initialization fields
- mark_running / advance / mark_succeeded / mark_failed state transitions
- to_dict serialization shape
- visual-compose + clip-preview service responses include jobRun
- jobRun.runId / experimentId match response runId / experimentId
- visual-compose outer exception returns jobRun
- JobRun stage / status enums are restricted
"""

import re
import time
from unittest.mock import MagicMock, patch

import pytest


# ─── JobRun dataclass unit tests ────────────────────────────────────────────


def test_job_run_init_defaults():
    """JobRun initial state: pending/created/0%/empty logs/artifacts/no error."""
    from app.video_lab.job_run import (
        JobRun,
        JOB_STATUS_PENDING,
        JOB_STAGE_CREATED,
        STAGE_LABELS,
    )

    jr = JobRun(
        job_id="job_test",
        run_id="run_test",
        experiment_id="exp_test",
        mode="compose",
        route_id="local_frame_compose",
    )

    assert jr.job_id == "job_test"
    assert jr.run_id == "run_test"
    assert jr.experiment_id == "exp_test"
    assert jr.mode == "compose"
    assert jr.route_id == "local_frame_compose"
    assert jr.status == JOB_STATUS_PENDING
    assert jr.stage == JOB_STAGE_CREATED
    assert jr.progress == 0
    assert jr.stage_label == STAGE_LABELS[JOB_STAGE_CREATED]
    assert jr.logs == []
    assert jr.artifacts == {}
    assert jr.error is None
    # timestamps present and ISO 8601
    assert jr.created_at
    assert jr.updated_at


def test_job_run_mark_running_advances_state():
    from app.video_lab.job_run import (
        JobRun,
        JOB_STATUS_RUNNING,
        JOB_STAGE_PLANNING,
    )

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    jr.mark_running(stage=JOB_STAGE_PLANNING, progress=10)
    assert jr.status == JOB_STATUS_RUNNING
    assert jr.stage == JOB_STAGE_PLANNING
    assert jr.progress == 10


def test_job_run_advance_progress_clamped():
    from app.video_lab.job_run import JobRun, JOB_STAGE_TTS

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    jr.mark_running()
    # progress out of range should be clamped
    jr.advance(JOB_STAGE_TTS, 150)
    assert jr.progress == 100
    jr.advance(JOB_STAGE_TTS, -5)
    assert jr.progress == 0


def test_job_run_advance_rejects_unknown_stage():
    from app.video_lab.job_run import JobRun

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    with pytest.raises(ValueError, match="unknown stage"):
        jr.mark_running(stage="not_a_real_stage", progress=10)


def test_job_run_cannot_advance_from_terminal_state():
    from app.video_lab.job_run import JobRun, JOB_STAGE_TTS

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    jr.mark_succeeded()
    with pytest.raises(ValueError, match="terminal status"):
        jr.advance(JOB_STAGE_TTS, 50)


def test_job_run_mark_succeeded_sets_terminal_state():
    from app.video_lab.job_run import JobRun, JOB_STATUS_SUCCEEDED, JOB_STAGE_COMPLETED

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    jr.mark_succeeded()
    assert jr.status == JOB_STATUS_SUCCEEDED
    assert jr.stage == JOB_STAGE_COMPLETED
    assert jr.progress == 100


def test_job_run_mark_failed_records_error():
    from app.video_lab.job_run import JobRun, JOB_STATUS_FAILED, JOB_STAGE_FAILED

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    err = {"code": "X", "message": "boom"}
    jr.mark_failed(error=err)
    assert jr.status == JOB_STATUS_FAILED
    assert jr.stage == JOB_STAGE_FAILED
    assert jr.progress == 100
    assert jr.error == err


def test_job_run_log_appends_and_skips_empty():
    from app.video_lab.job_run import JobRun

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    jr.log("step 1")
    jr.log("step 2")
    jr.log("")
    assert jr.logs == ["step 1", "step 2"]


def test_job_run_set_artifact_stores_value():
    from app.video_lab.job_run import JobRun

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    jr.set_artifact("finalVideoUrl", "/runtime/v.mp4")
    jr.set_artifact("coverUrl", "/runtime/c.jpg")
    assert jr.artifacts["finalVideoUrl"] == "/runtime/v.mp4"
    assert jr.artifacts["coverUrl"] == "/runtime/c.jpg"


def test_job_run_to_dict_shape():
    from app.video_lab.job_run import JobRun

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    d = jr.to_dict()
    expected_keys = {
        "jobId", "runId", "experimentId", "mode", "routeId",
        "status", "stage", "progress", "stageLabel",
        "logs", "artifacts", "error",
        "createdAt", "updatedAt",
    }
    assert set(d.keys()) == expected_keys
    assert d["jobId"] == "j1"
    assert d["logs"] == []
    assert d["artifacts"] == {}
    assert d["error"] is None


def test_job_run_to_dict_returns_copies_not_refs():
    from app.video_lab.job_run import JobRun

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    jr.log("a")
    d = jr.to_dict()
    d["logs"].append("tampered")
    assert jr.logs == ["a"]  # not mutated
    d["artifacts"]["x"] = 1
    assert "x" not in jr.artifacts  # not mutated


def test_new_job_id_format():
    from app.video_lab.job_run import new_job_id

    jid = new_job_id()
    assert jid.startswith("job_")
    assert re.match(r"^job_[0-9a-f]{12}$", jid)


def test_job_run_updated_at_changes_on_transitions():
    from app.video_lab.job_run import JobRun

    jr = JobRun(
        job_id="j1", run_id="r1", experiment_id="e1",
        mode="compose", route_id="local_frame_compose",
    )
    initial = jr.updated_at
    time.sleep(0.01)
    jr.mark_running()
    assert jr.updated_at != initial
    # even updated at advance
    new_time = jr.updated_at
    time.sleep(0.01)
    jr.log("step")
    assert jr.updated_at != new_time


# ─── visual-compose service contract: response.jobRun ──────────────────────


def _make_compose_result(status="succeeded", videoUrl="/runtime/v.mp4", coverUrl="/runtime/c.jpg"):
    """Build a mock result object for run_tts_subtitle_compose."""
    mock = MagicMock()
    mock.rawOutput = {"status": status, "quality": {"overallScore": 0.85}}
    mock.assets = {"audioDurationSec": 30.0, "subtitleCount": 8}
    mock.productionSteps = []
    mock.logs = ["step 1 done"]
    mock.videoUrl = videoUrl
    mock.coverUrl = coverUrl
    return mock


def test_visual_compose_success_includes_job_run():
    """Successful visual-compose response must include jobRun with status=succeeded."""
    from app.video_lab.router import _run_visual_compose
    from app.video_lab.job_run import JOB_STATUS_SUCCEEDED

    mock_result = _make_compose_result(status="succeeded")

    with patch(
        "app.video_lab.services.visual_compose_service.run_tts_subtitle_compose",
        return_value=mock_result,
    ):
        with patch("app.video_lab.quality.quality_log.append_record"):
            with patch(
                "app.video_lab.services.visual_compose_service.write_experiment_manifest",
                return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
            ):
                resp = _run_visual_compose("Test content", "local_frame_compose", {})

    assert "jobRun" in resp
    jr = resp["jobRun"]
    assert jr["status"] == JOB_STATUS_SUCCEEDED
    assert jr["stage"] == "completed"
    assert jr["progress"] == 100
    assert jr["runId"] == resp["runId"]
    assert jr["experimentId"] == resp["experimentId"]
    assert jr["routeId"] == "local_frame_compose"
    assert jr["mode"] == "compose"
    # jobId present
    assert jr["jobId"].startswith("job_")


def test_visual_compose_failure_includes_job_run():
    """Failed visual-compose response must include jobRun with status=failed."""
    from app.video_lab.router import _run_visual_compose
    from app.video_lab.job_run import JOB_STATUS_FAILED

    mock_result = _make_compose_result(
        status="failed",
        videoUrl="",
        coverUrl="",
    )
    mock_result.rawOutput = {
        "status": "failed",
        "error": "MiniMax API key not configured",
    }
    mock_result.assets = {}

    with patch(
        "app.video_lab.services.visual_compose_service.run_tts_subtitle_compose",
        return_value=mock_result,
    ):
        with patch(
            "app.video_lab.services.visual_compose_service.write_experiment_manifest",
            return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
        ):
            resp = _run_visual_compose("Test content", "local_frame_compose", {})

    assert "jobRun" in resp
    jr = resp["jobRun"]
    assert jr["status"] == JOB_STATUS_FAILED
    assert jr["stage"] == "failed"
    assert jr["progress"] == 100
    assert jr["runId"] == resp["runId"]
    assert jr["experimentId"] == resp["experimentId"]
    # jobRun.error should be present and aligned with response.error
    assert jr["error"] is not None
    assert jr["error"]["code"] == "VIDEO_LAB_COMPOSE_FAILED"
    assert resp["error"]["code"] == "VIDEO_LAB_COMPOSE_FAILED"


def test_visual_compose_outer_exception_includes_job_run():
    """Outer-exception visual-compose response must include jobRun with status=failed."""
    from app.video_lab.router import visual_compose
    from app.video_lab.schemas import VisualComposeRequest
    from app.video_lab.job_run import JOB_STATUS_FAILED

    with patch(
        "app.video_lab.services.visual_compose_service.run_visual_compose_contract",
        side_effect=RuntimeError("Database connection failed"),
    ):
        req = VisualComposeRequest(
            content="Test content",
            visualRoute="local_frame_compose",
            params={},
        )
        resp = visual_compose(req)

    assert "jobRun" in resp
    jr = resp["jobRun"]
    assert jr["status"] == JOB_STATUS_FAILED
    assert jr["stage"] == "failed"
    assert jr["progress"] == 100
    assert jr["runId"] == resp["runId"]
    assert jr["experimentId"] == resp["experimentId"]
    assert jr["error"] is not None
    assert jr["error"]["code"] == "VIDEO_LAB_INTERNAL_ERROR"


def test_visual_compose_job_run_logs_progress():
    """JobRun logs should capture lifecycle events (start, stage, completion)."""
    from app.video_lab.router import _run_visual_compose

    mock_result = _make_compose_result(status="succeeded")

    with patch(
        "app.video_lab.services.visual_compose_service.run_tts_subtitle_compose",
        return_value=mock_result,
    ):
        with patch("app.video_lab.quality.quality_log.append_record"):
            with patch(
                "app.video_lab.services.visual_compose_service.write_experiment_manifest",
                return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
            ):
                resp = _run_visual_compose("Test content", "local_frame_compose", {})

    logs = resp["jobRun"]["logs"]
    # must include at least a start line and a factory log
    assert any("starting" in l for l in logs)
    assert any("[factory]" in l for l in logs)


def test_visual_compose_job_run_artifacts_on_success():
    """On success, jobRun.artifacts should include finalVideoUrl/coverUrl/manifestUrl."""
    from app.video_lab.router import _run_visual_compose

    mock_result = _make_compose_result(
        status="succeeded",
        videoUrl="/runtime/v.mp4",
        coverUrl="/runtime/c.jpg",
    )

    with patch(
        "app.video_lab.services.visual_compose_service.run_tts_subtitle_compose",
        return_value=mock_result,
    ):
        with patch("app.video_lab.quality.quality_log.append_record"):
            with patch(
                "app.video_lab.services.visual_compose_service.write_experiment_manifest",
                return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
            ):
                resp = _run_visual_compose("Test content", "local_frame_compose", {})

    artifacts = resp["jobRun"]["artifacts"]
    assert artifacts["finalVideoUrl"] == "/runtime/v.mp4"
    assert artifacts["coverUrl"] == "/runtime/c.jpg"
    assert artifacts["manifestUrl"] == "/runtime/manifest.json"


# ─── clip-preview service: response.jobRun ──────────────────────────────────


def test_clip_preview_success_includes_job_run():
    from app.video_lab.router import clip_preview
    from app.video_lab.schemas import ClipPreviewRequest
    from app.video_lab.job_run import JOB_STATUS_SUCCEEDED

    mock_result = {
        "success": True,
        "route": "local_frame_compose",
        "clipUrl": "/runtime/v.mp4",
        "warnings": [],
        "elapsedMs": 1500,
    }
    with patch(
        "app.video_lab.services.clip_preview_service.render_clip_preview",
        return_value=mock_result,
    ):
        with patch(
            "app.video_lab.services.clip_preview_service.write_experiment_manifest",
            return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
        ):
            req = ClipPreviewRequest(
                visualRoute="local_frame_compose",
                content="Test content",
                params={"clipSeconds": 3},
            )
            resp = clip_preview(req)

    assert "jobRun" in resp
    jr = resp["jobRun"]
    assert jr["status"] == JOB_STATUS_SUCCEEDED
    assert jr["stage"] == "completed"
    assert jr["runId"] == resp["runId"]
    assert jr["experimentId"] == resp["experimentId"]


def test_clip_preview_failure_includes_job_run():
    from app.video_lab.router import clip_preview
    from app.video_lab.schemas import ClipPreviewRequest
    from app.video_lab.job_run import JOB_STATUS_FAILED

    mock_result = {
        "success": False,
        "route": "local_frame_compose",
        "message": "render failed",
        "warnings": [],
        "elapsedMs": 800,
    }
    with patch(
        "app.video_lab.services.clip_preview_service.render_clip_preview",
        return_value=mock_result,
    ):
        with patch(
            "app.video_lab.services.clip_preview_service.write_experiment_manifest",
            return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
        ):
            req = ClipPreviewRequest(
                visualRoute="local_frame_compose",
                content="Test content",
                params={},
            )
            resp = clip_preview(req)

    assert "jobRun" in resp
    assert resp["jobRun"]["status"] == JOB_STATUS_FAILED
    assert resp["jobRun"]["stage"] == "failed"


def test_clip_preview_exception_includes_job_run():
    from app.video_lab.router import clip_preview
    from app.video_lab.schemas import ClipPreviewRequest
    from app.video_lab.job_run import JOB_STATUS_FAILED

    with patch(
        "app.video_lab.services.clip_preview_service.render_clip_preview",
        side_effect=RuntimeError("unexpected boom"),
    ):
        with patch(
            "app.video_lab.services.clip_preview_service.write_experiment_manifest",
            return_value={"path": "/p/manifest.json", "url": "/runtime/manifest.json"},
        ):
            req = ClipPreviewRequest(
                visualRoute="local_frame_compose",
                content="Test content",
                params={},
            )
            resp = clip_preview(req)

    assert "jobRun" in resp
    assert resp["jobRun"]["status"] == JOB_STATUS_FAILED
    assert resp["jobRun"]["error"] is not None
