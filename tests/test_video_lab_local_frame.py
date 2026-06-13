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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
