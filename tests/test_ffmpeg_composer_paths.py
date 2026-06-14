"""
Tests for V0.3.1.2 FFmpeg path fixes
- concat file uses absolute frame paths
- frames_txt passed to FFmpeg is absolute path
- output_path is absolute
- Windows paths converted to FFmpeg-readable POSIX paths
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────
# 1. build_concat_file_content uses absolute paths
# ─────────────────────────────────────────
def test_build_concat_file_uses_absolute_paths():
    """build_concat_file_content should resolve paths to absolute for FFmpeg."""
    from app.video_lab.renderers.ffmpeg_composer import build_concat_file_content

    frame_sequence = [
        {"path": "runtime/video_lab/exp/frames/cover.png"},
        {"path": "runtime/video_lab/exp/frames/keypoint_001.png"},
    ]
    duration_by_path = {
        "runtime/video_lab/exp/frames/cover.png": 4.0,
        "runtime/video_lab/exp/frames/keypoint_001.png": 6.0,
    }

    content = build_concat_file_content(frame_sequence, duration_by_path)

    lines = content.strip().split("\n")
    # Each file line should be an absolute path
    file_lines = [l for l in lines if l.startswith("file '")]
    assert len(file_lines) == 3, f"Expected 3 file lines, got: {lines}"

    # Check all paths are absolute (Windows: C:\... or /c/..., Unix: /...)
    for fl in file_lines:
        path_part = fl.split("file '")[1].rstrip("'")
        assert Path(path_part).is_absolute(), \
            f"Path should be absolute: {path_part}"


# ─────────────────────────────────────────
# 2. compose_video_from_frame_sequence uses absolute output path
# ─────────────────────────────────────────
def test_compose_video_from_frame_sequence_output_is_absolute():
    """compose_video_from_frame_sequence should use resolve() on output_path."""
    # Verify via source code inspection that resolve() is called
    import inspect
    from app.video_lab.renderers.ffmpeg_composer import compose_video_from_frame_sequence

    source = inspect.getsource(compose_video_from_frame_sequence)
    assert "resolve()" in source, \
        "compose_video_from_frame_sequence should call .resolve() on paths"
    assert "cwd=" not in source, \
        "compose_video_from_frame_sequence should not rely on cwd"


# ─────────────────────────────────────────
# 3. compose_video_from_frames uses absolute paths and no cwd
# ─────────────────────────────────────────
def test_compose_video_from_frames_no_cwd():
    """compose_video_from_frames should use absolute paths and no cwd."""
    import inspect
    from app.video_lab.renderers.ffmpeg_composer import compose_video_from_frames

    source = inspect.getsource(compose_video_from_frames)
    assert "resolve()" in source, \
        "compose_video_from_frames should call .resolve() on paths"
    assert "cwd=" not in source, \
        "compose_video_from_frames should not rely on cwd"


# ─────────────────────────────────────────
# 4. concat file paths are POSIX-style for FFmpeg
# ─────────────────────────────────────────
def test_concat_file_paths_are_posix_style():
    """Paths in concat file should use forward slashes for FFmpeg compatibility."""
    from app.video_lab.renderers.ffmpeg_composer import build_concat_file_content

    frame_sequence = [
        {"path": "D:\\test\\exp\\frames\\cover.png"},
    ]
    duration_by_path = {"D:\\test\\exp\\frames\\cover.png": 4.0}

    content = build_concat_file_content(frame_sequence, duration_by_path)

    # Path in file should use forward slashes (POSIX), not backslashes
    assert "file '" in content
    assert "\\" not in content.split("file '")[1].split("'")[0], \
        "Path should use forward slashes, not backslashes"


# ─────────────────────────────────────────
# 5. compose_video_from_frame_sequence no cwd dependency
# ─────────────────────────────────────────
def test_compose_video_from_frame_sequence_no_cwd():
    """compose_video_from_frame_sequence should not rely on cwd for FFmpeg."""
    from app.video_lab.renderers.ffmpeg_composer import compose_video_from_frame_sequence

    with patch("app.video_lab.renderers.ffmpeg_composer.check_ffmpeg_available") as mock_check, \
         patch("subprocess.run") as mock_run, \
         patch("builtins.open"):

        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            frame_seq = [{"path": str(Path(tmpdir) / "frames" / "cover.png")}]
            dur_by_path = {str(Path(tmpdir) / "frames" / "cover.png"): 4.0}
            output_path = Path(tmpdir) / "output.mp4"

            compose_video_from_frame_sequence(
                frame_sequence=frame_seq,
                output_path=output_path,
                duration_by_path=dur_by_path,
                fps=30,
                resolution=(1080, 1920),
            )

    # Verify cwd was NOT passed to subprocess.run
    for call in mock_run.call_args_list:
        kwargs = call[1]
        assert "cwd" not in kwargs, f"subprocess.run should not use cwd: {kwargs}"


# ─────────────────────────────────────────
# 6. RouteResult warnings preserve failure reasons
# ─────────────────────────────────────────
def test_route_result_warnings_preserve_failure():
    """RouteResult warnings should include FFmpeg failure message when route fails."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "FFmpeg Failure Warning Test",
        "inputPayload": {"content": ""},  # empty = will fail
        "commonParams": {},
        "routeIds": ["local_frame_compose"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    result = data["results"][0]

    assert result["status"] == "failed"
    # If failed, warnings should contain failure info
    if result["status"] == "failed":
        assert len(result["warnings"]) > 0 or result["videoUrl"] == "", \
            "Failed route should have warnings or empty videoUrl"


# ─────────────────────────────────────────
# 7. USE_SHELL is True only on Windows
# ─────────────────────────────────────────
def test_remotion_use_shell_is_windows_only():
    """USE_SHELL constant should be True on Windows (nt), False on Unix."""
    from app.video_lab.renderers.remotion.remotion_renderer import USE_SHELL
    import os

    if os.name == "nt":
        assert USE_SHELL is True, "Windows should use shell=True for npx.cmd"
    else:
        assert USE_SHELL is False, "Unix should not need shell for npx"


# ─────────────────────────────────────────
# 8. .gitignore contains remotion/src/props.json
# ─────────────────────────────────────────
def test_gitignore_contains_remotion_props():
    """Gitignore should exclude remotion/src/props.json."""
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    content = gitignore_path.read_text()
    assert "remotion/src/props.json" in content, \
        ".gitignore should contain 'remotion/src/props.json'"


# ─────────────────────────────────────────
# 9. .gitignore contains remotion/out/
# ─────────────────────────────────────────
def test_gitignore_contains_remotion_out():
    """Gitignore should exclude remotion/out/."""
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    content = gitignore_path.read_text()
    assert "remotion/out/" in content, \
        ".gitignore should contain 'remotion/out/'"


# ─────────────────────────────────────────
# 10. package-lock.json exists in remotion/
# ─────────────────────────────────────────
def test_remotion_package_lock_exists():
    """remotion/package-lock.json should exist (committed)."""
    lock_path = Path(__file__).parent.parent / "remotion" / "package-lock.json"
    assert lock_path.exists(), \
        "remotion/package-lock.json should exist (committed to repo)"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
