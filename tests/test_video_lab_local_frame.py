"""
Tests for local_frame_compose real rendering
"""

import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.text_layout import wrap_text, truncate_text, split_title_and_body, find_chinese_font
from app.video_lab.renderers.file_store import (
    get_experiment_dir,
    ensure_runtime_exists,
    path_to_url,
    write_manifest,
)
from app.video_lab.renderers.ffmpeg_composer import check_ffmpeg_available, get_ffmpeg_version


# ─────────────────────────────────────────────
# Text Layout Tests
# ─────────────────────────────────────────────
def test_wrap_text_basic():
    """wrap_text should limit text width."""
    text = "这是一个测试文本"
    font, _ = find_chinese_font(36)
    class FakeDraw:
        def textbbox(self, pos, text, font=None):
            return (0, 0, len(text) * 20, 20)
    result = wrap_text(text, font, 200, FakeDraw())
    assert isinstance(result, list)
    assert len(result) >= 1


def test_truncate_text():
    """truncate_text should limit chars."""
    text = "这是一个很长的标题"
    result = truncate_text(text, 5)
    assert len(result) <= 5


def test_split_title_and_body():
    """split_title_and_body should split at max_chars."""
    text = "这是一个测试文本"
    title, body = split_title_and_body(text, max_title_chars=5)
    assert len(title) <= 5
    assert title + body == text


def test_find_chinese_font_returns_font():
    """find_chinese_font should return a font."""
    font, warnings = find_chinese_font(36)
    assert font is not None
    assert isinstance(warnings, list)


# ─────────────────────────────────────────────
# File Store Tests
# ─────────────────────────────────────────────
def test_ensure_runtime_exists():
    """ensure_runtime_exists should create directory."""
    ensure_runtime_exists()
    from app.video_lab.renderers.file_store import RUNTIME_BASE
    assert RUNTIME_BASE.exists() or RUNTIME_BASE.is_dir()


def test_path_to_url():
    """path_to_url should convert path to URL format."""
    url = path_to_url("runtime/video_lab/experiments/exp_abc/output.mp4")
    assert url.startswith("/runtime/")


def test_write_and_read_manifest():
    """write_manifest should create file."""
    ensure_runtime_exists()
    manifest = {
        "experimentId": "exp_test_manifest",
        "method": "local_frame_compose",
        "resolution": "1080x1920",
    }
    path = write_manifest("exp_test_manifest", manifest)
    assert path.exists()


# ─────────────────────────────────────────────
# FFmpeg Tests
# ─────────────────────────────────────────────
def test_check_ffmpeg_returns_bool():
    """check_ffmpeg_available should return bool."""
    result = check_ffmpeg_available()
    assert isinstance(result, bool)


def test_get_ffmpeg_version():
    """get_ffmpeg_version should return string."""
    version = get_ffmpeg_version()
    assert isinstance(version, str)


# ─────────────────────────────────────────────
# Integration Test
# ─────────────────────────────────────────────
def test_local_frame_compose_with_empty_content():
    """Empty content should return failed result."""
    from app.video_lab.adapters.local_frame_compose import run_local_frame_compose

    result = run_local_frame_compose(
        experiment_id="exp_empty_test",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": ""},
        params={"targetDuration": 45},
    )
    assert result.adapter == "local_frame_compose"
    # Should have failed step
    failed_steps = [s for s in result.productionSteps if s.status.value == "failed"]
    assert len(failed_steps) > 0


def test_local_frame_compose_produces_steps():
    """local_frame_compose should produce 12 steps."""
    from app.video_lab.adapters.local_frame_compose import run_local_frame_compose

    result = run_local_frame_compose(
        experiment_id="exp_steps_test",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": "Test content"},
        params={"targetDuration": 10},
    )
    assert len(result.productionSteps) == 12
    # At least step 1, 2, 3, 4, 5 should succeed
    succeeded = [s for s in result.productionSteps if s.status.value == "succeeded"]
    assert len(succeeded) >= 5


def test_local_frame_compose_has_artifacts():
    """local_frame_compose should produce artifacts."""
    from app.video_lab.adapters.local_frame_compose import run_local_frame_compose

    result = run_local_frame_compose(
        experiment_id="exp_artifact_test",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": "Test content for artifact check"},
        params={"targetDuration": 10},
    )
    all_artifacts = []
    for step in result.productionSteps:
        all_artifacts.extend(step.artifacts)
    assert len(all_artifacts) > 0


# ─────────────────────────────────────────────
# path_to_url Tests
# ─────────────────────────────────────────────
def test_path_to_url_keeps_video_lab_experiments_prefix():
    """path_to_url should preserve the full /runtime/video_lab/experiments/ prefix."""
    from app.video_lab.renderers.file_store import path_to_url
    url = path_to_url("runtime/video_lab/experiments/exp_abc/output.mp4")
    assert url == "/runtime/video_lab/experiments/exp_abc/output.mp4"


def test_path_to_url_windows_path():
    """path_to_url should handle Windows-style backslash paths."""
    from app.video_lab.renderers.file_store import path_to_url
    url = path_to_url("runtime\\video_lab\\experiments\\exp_abc\\output.mp4")
    assert url == "/runtime/video_lab/experiments/exp_abc/output.mp4"


def test_path_to_url_nested_experiment_dir():
    """path_to_url should handle deeper experiment paths."""
    from app.video_lab.renderers.file_store import path_to_url
    url = path_to_url("runtime/video_lab/experiments/exp_xyz_123/frames/frame_001.png")
    assert url == "/runtime/video_lab/experiments/exp_xyz_123/frames/frame_001.png"


# ─────────────────────────────────────────────
# FFmpeg Failure → Experiment Status Tests
# ─────────────────────────────────────────────
def test_experiment_runner_sets_failed_when_ffmpeg_fails(monkeypatch):
    """ExperimentRunner should set status=failed when FFmpeg composition fails."""
    from app.video_lab.experiment_runner import ExperimentRunner
    from app.video_lab.models import ExperimentStatus, ProductionStepStatus

    # Patch compose_video_from_frames to return a failure
    class FakeResult:
        def get(self, key, default=None):
            return {"success": False, "message": "FFmpeg error", "version": "test", "ffmpeg_command": "fake cmd"}.get(key, default)

    def fake_compose(*args, **kwargs):
        return {"success": False, "message": "FFmpeg error", "version": "test", "ffmpeg_command": "fake cmd"}

    monkeypatch.setattr("app.video_lab.adapters.local_frame_compose.compose_video_from_frames", fake_compose)

    runner = ExperimentRunner()
    exp = runner.create_experiment(
        test_case_id="case_ai_frontier_daily_001",
        method_id="method_local_frame_compose",
        title="FFmpeg Failure Test",
        input_payload={"content": "Test content for ffmpeg failure"},
        params={"targetDuration": 10},
    )
    result = runner.run_experiment(exp.id)

    # Verify experiment status is FAILED
    assert exp.status == ExperimentStatus.FAILED, f"Expected FAILED, got {exp.status}"
    assert exp.errorMessage is not None and exp.errorMessage != ""


def test_experiment_runner_ffmpeg_failure_has_failed_step(monkeypatch):
    """FFmpeg failure should produce a failed production step."""
    from app.video_lab.experiment_runner import ExperimentRunner
    from app.video_lab.models import ProductionStepStatus

    def fake_compose(*args, **kwargs):
        return {"success": False, "message": "FFmpeg error", "version": "test", "ffmpeg_command": "fake cmd"}

    monkeypatch.setattr("app.video_lab.adapters.local_frame_compose.compose_video_from_frames", fake_compose)

    runner = ExperimentRunner()
    exp = runner.create_experiment(
        test_case_id="case_ai_frontier_daily_001",
        method_id="method_local_frame_compose",
        title="FFmpeg Failure Step Test",
        input_payload={"content": "Test content for failed step check"},
        params={"targetDuration": 10},
    )
    result = runner.run_experiment(exp.id)

    failed_steps = [s for s in result.productionSteps if s.status == ProductionStepStatus.FAILED]
    assert len(failed_steps) > 0, "Expected at least one failed production step"


# ─────────────────────────────────────────────
# Artifact Type Tests
# ─────────────────────────────────────────────
def test_local_frame_compose_uses_video_output_artifact_type():
    """Successful local_frame_compose should produce a video_output artifact, not mock_video."""
    from app.video_lab.adapters.local_frame_compose import run_local_frame_compose
    from app.video_lab.models import ArtifactType

    result = run_local_frame_compose(
        experiment_id="exp_artifact_type_test",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": "Test content for artifact type check"},
        params={"targetDuration": 10},
    )

    all_artifacts = []
    for step in result.productionSteps:
        all_artifacts.extend(step.artifacts)

    video_artifacts = [a for a in all_artifacts if a.type == ArtifactType.VIDEO_OUTPUT]
    mock_artifacts = [a for a in all_artifacts if a.type == ArtifactType.MOCK_VIDEO]

    # Should have at least one video_output artifact
    assert len(video_artifacts) > 0, f"Expected video_output artifact, found types: {[a.type.value for a in all_artifacts]}"
    # Should NOT have any mock_video artifacts from local_frame_compose
    assert len(mock_artifacts) == 0, "local_frame_compose should not produce mock_video artifacts"


def test_local_frame_compose_manifest_contains_ffmpeg_command():
    """Manifest should contain ffmpegCommand and ffmpegMessage."""
    from app.video_lab.adapters.local_frame_compose import run_local_frame_compose

    result = run_local_frame_compose(
        experiment_id="exp_manifest_ffmpeg_test",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": "Test content for manifest ffmpeg fields"},
        params={"targetDuration": 10},
    )

    # Find manifest artifact
    manifest_artifacts = [s for s in result.productionSteps if s.name == "Generate Conclusion"]
    assert len(manifest_artifacts) > 0
    manifest_artifact = manifest_artifacts[0].artifacts[0]

    manifest_payload = manifest_artifact.payload
    assert "ffmpegCommand" in manifest_payload, "manifest should contain ffmpegCommand"
    assert "ffmpegMessage" in manifest_payload, "manifest should contain ffmpegMessage"


def test_local_frame_compose_step11_contains_ffmpeg_command():
    """Step 11 (FFmpeg Compose) keyData should contain ffmpegCommand and ffmpegMessage."""
    from app.video_lab.adapters.local_frame_compose import run_local_frame_compose

    result = run_local_frame_compose(
        experiment_id="exp_step11_ffmpeg_cmd_test",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": "Test content for step 11 ffmpeg command check"},
        params={"targetDuration": 10},
    )

    step11 = [s for s in result.productionSteps if "FFmpeg" in s.name][0]
    assert "ffmpegCommand" in step11.keyData, "Step 11 keyData should contain ffmpegCommand"
    assert "ffmpegMessage" in step11.keyData, "Step 11 keyData should contain ffmpegMessage"


# ─────────────────────────────────────────────
# Cleanup Test
# ─────────────────────────────────────────────
def test_cleanup_experiment_runtime():
    """cleanup_experiment_runtime should remove experiment directory."""
    from app.video_lab.renderers.file_store import (
        ensure_runtime_exists,
        get_experiment_dir,
        cleanup_experiment_runtime,
        write_manifest,
    )

    # Create a real experiment runtime
    ensure_runtime_exists()
    test_exp_id = "exp_cleanup_test"

    # Write a manifest to create files
    write_manifest(test_exp_id, {"experimentId": test_exp_id, "method": "local_frame_compose"})

    # Verify it exists
    exp_dir = get_experiment_dir(test_exp_id)
    assert exp_dir.exists(), f"Expected {exp_dir} to exist before cleanup"

    # Cleanup
    removed = cleanup_experiment_runtime(test_exp_id)
    assert removed is True, "cleanup_experiment_runtime should return True when dir existed"
    assert not exp_dir.exists(), f"Expected {exp_dir} to not exist after cleanup"


def test_cleanup_experiment_runtime_returns_false_when_missing():
    """cleanup_experiment_runtime should return False when dir does not exist; must not create the dir."""
    from app.video_lab.renderers.file_store import cleanup_experiment_runtime, RUNTIME_BASE

    experiment_id = "exp_cleanup_missing_test"
    exp_dir = RUNTIME_BASE / experiment_id

    # Ensure it does not exist
    import shutil
    if exp_dir.exists():
        shutil.rmtree(exp_dir)

    result = cleanup_experiment_runtime(experiment_id)

    assert result is False, "cleanup_experiment_runtime should return False when dir is missing"
    assert not exp_dir.exists(), "cleanup_experiment_runtime must NOT create the directory when missing"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
