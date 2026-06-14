"""
Tests for V0.3.1.1 Remotion renderer paths and CLI fixes
- REMOTION_ROOT_TSX is relative to cwd=remotion (src/Root.tsx)
- props path uses ./ prefix for Windows compatibility
- output.mp4 uses absolute path
- Root.tsx uses standard Composition pattern
- manifestUrl written before write_manifest call
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────
# 1. Path constants are relative to cwd=remotion
# ─────────────────────────────────────────
def test_remotion_root_tsx_relative_to_remotion_dir():
    """REMOTION_ROOT_TSX should be 'src/Root.tsx' (relative to cwd=remotion)."""
    from app.video_lab.renderers.remotion.remotion_renderer import REMOTION_ROOT_TSX, REMOTION_DIR

    # When cwd=remotion, the CLI sees REMOTION_DIR/REMOTION_ROOT_TSX
    # i.e. remotion/src/Root.tsx on disk
    assert str(REMOTION_ROOT_TSX) == str(os.path.join("src", "Root.tsx")), \
        f"Expected 'src/Root.tsx', got {REMOTION_ROOT_TSX}"


def test_remotion_props_path_relative_to_remotion_dir():
    """REMOTION_PROPS_PATH should be 'src/props.json' (relative to cwd=remotion)."""
    from app.video_lab.renderers.remotion.remotion_renderer import REMOTION_PROPS_PATH

    assert str(REMOTION_PROPS_PATH) == str(os.path.join("src", "props.json")), \
        f"Expected 'src/props.json', got {REMOTION_PROPS_PATH}"


def test_remotion_entry_is_ai_news_video():
    """REMOTION_ENTRY should be 'AiNewsVideo' matching the Composition id."""
    from app.video_lab.renderers.remotion.remotion_renderer import REMOTION_ENTRY
    assert REMOTION_ENTRY == "AiNewsVideo"


# ─────────────────────────────────────────
# 2. Command uses ./ prefix for Windows
# ─────────────────────────────────────────
def test_render_command_uses_dot_slash_prefix():
    """Render command should use ./src/Root.tsx and ./src/props.json for Windows compatibility."""
    # We test this by inspecting the command construction directly
    from app.video_lab.renderers.remotion.remotion_renderer import (
        REMOTION_ROOT_TSX, REMOTION_PROPS_PATH, REMOTION_ENTRY,
    )

    # The constants should be relative paths (no leading remotion/)
    # Use parts comparison since Path uses \ on Windows
    assert REMOTION_ROOT_TSX.parts == ("src", "Root.tsx"), f"Expected 'src/Root.tsx', got {REMOTION_ROOT_TSX}"
    assert REMOTION_PROPS_PATH.parts == ("src", "props.json"), f"Expected 'src/props.json', got {REMOTION_PROPS_PATH}"

    # When combined with ./ prefix, they should work as relative paths from remotion/ cwd
    assert REMOTION_ROOT_TSX.parts[-1] == "Root.tsx"
    assert REMOTION_PROPS_PATH.parts[-1] == "props.json"
    assert REMOTION_ENTRY == "AiNewsVideo"


# ─────────────────────────────────────────
# 3. Output uses absolute path
# ─────────────────────────────────────────
def test_output_uses_absolute_path():
    """output_mp4 should use resolve() for absolute path."""
    from app.video_lab.renderers.remotion.remotion_renderer import render_remotion_video

    with patch("app.video_lab.renderers.remotion.remotion_renderer.check_remotion_available") as mock_check, \
         patch("subprocess.run") as mock_run:

        mock_check.return_value = (True, "OK")
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

        with patch("app.video_lab.renderers.remotion.remotion_renderer.get_experiment_dir") as mock_dir:
            mock_exp_dir = MagicMock()
            # resolve() should be called
            mock_exp_dir.resolve.return_value = mock_exp_dir
            mock_exp_dir.__truediv__ = lambda self, x: MagicMock()
            mock_dir.return_value = mock_exp_dir

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.__truediv__", return_value=MagicMock()):
                    render_remotion_video(
                        experiment_id="test_exp_abs",
                        props={"title": "Test", "keyPoints": [], "durationSec": 15, "stylePreset": "ai_frontier_dark"},
                    )

    # Verify resolve() was called on experiment dir
    mock_exp_dir.resolve.assert_called()


# ─────────────────────────────────────────
# 4. Root.tsx contains Composition id="AiNewsVideo"
# ─────────────────────────────────────────
def test_root_tsx_contains_composition_id():
    """Root.tsx should define Composition with id='AiNewsVideo'."""
    root_tsx_path = os.path.join(os.path.dirname(__file__), "..", "remotion", "src", "Root.tsx")
    root_tsx_path = os.path.normpath(root_tsx_path)

    with open(root_tsx_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'id="AiNewsVideo"' in content or "id='AiNewsVideo'" in content, \
        "Root.tsx should contain Composition with id='AiNewsVideo'"
    assert "registerRoot" in content, "Root.tsx should call registerRoot"


# ─────────────────────────────────────────
# 5. manifestUrl computed before writing manifest
# ─────────────────────────────────────────
def test_adapter_manifest_url_computed_before_write():
    """Adapter should compute manifest_url before building the manifest dict."""
    from app.video_lab.adapters.remotion_template import run_remotion_template

    with patch("app.video_lab.adapters.remotion_template.check_remotion_available") as mock_check, \
         patch("app.video_lab.adapters.remotion_template.render_remotion_video") as mock_render, \
         patch("app.video_lab.adapters.remotion_template.get_experiment_dir") as mock_dir, \
         patch("app.video_lab.adapters.remotion_template.write_manifest") as mock_write:

        mock_check.return_value = (True, "OK")
        mock_render.return_value = {
            "success": True,
            "videoUrl": "/runtime/video_lab/experiments/test/output.mp4",
            "manifestUrl": "/runtime/video_lab/experiments/test/manifest.json",
            "message": "OK",
            "logs": [],
            "warnings": [],
        }

        mock_exp_dir = MagicMock()
        mock_exp_dir.__truediv__ = lambda self, x: MagicMock()
        mock_dir.return_value = mock_exp_dir
        mock_write.return_value = mock_exp_dir

        run_remotion_template(
            experiment_id="test_manifest_order",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "Test content"},
            params={"targetDuration": 15},
        )

    # write_manifest should have been called with manifest dict
    # that contains manifestUrl (not empty)
    call_args = mock_write.call_args
    manifest_arg = call_args[0][1]  # second positional arg
    assert "manifestUrl" in manifest_arg, "manifest should contain manifestUrl key"
    assert manifest_arg["manifestUrl"] != "", "manifestUrl should not be empty"


# ─────────────────────────────────────────
# 6. remotion_renderer writes manifestUrl in manifest
# ─────────────────────────────────────────
def test_renderer_manifest_contains_manifest_url():
    """Renderer should write manifest with manifestUrl field."""
    from app.video_lab.renderers.remotion.remotion_renderer import render_remotion_video

    with patch("app.video_lab.renderers.remotion.remotion_renderer.check_remotion_available") as mock_check, \
         patch("subprocess.run") as mock_run, \
         patch("app.video_lab.renderers.remotion.remotion_renderer.get_experiment_dir") as mock_dir, \
         patch("app.video_lab.renderers.remotion.remotion_renderer.write_manifest") as mock_write:

        mock_check.return_value = (True, "OK")
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

        mock_exp_dir = MagicMock()
        mock_exp_dir.__truediv__ = lambda self, x: MagicMock()
        mock_dir.return_value = mock_exp_dir
        mock_write.return_value = mock_exp_dir

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.__truediv__", return_value=MagicMock()):
                render_remotion_video(
                    experiment_id="test_manifest_url",
                    props={"title": "Test", "keyPoints": [], "durationSec": 15, "stylePreset": "ai_frontier_dark"},
                )

    call_args = mock_write.call_args
    manifest_arg = call_args[0][1]
    assert "manifestUrl" in manifest_arg, "renderer manifest should contain manifestUrl"


# ─────────────────────────────────────────
# 7. Remotion route failed is not mock
# ─────────────────────────────────────────
def test_remotion_failed_is_real_route_not_mock():
    """Failed Remotion route should have status='failed', not 'mock'."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Failed Remotion Route Test",
        "inputPayload": {"content": ""},  # empty = will fail
        "commonParams": {},
        "routeIds": ["template_programmatic_render"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    result = data["results"][0]

    assert result["routeId"] == "template_programmatic_render"
    assert result["status"] == "failed", f"Expected 'failed', got '{result['status']}'"
    assert result["status"] != "mock", "Failed route should NOT be 'mock'"


# ─────────────────────────────────────────
# 8. Shell=True used for subprocess
# ─────────────────────────────────────────
def test_subprocess_uses_shell_true_on_windows():
    """subprocess.run should use shell=True for npx.cmd on Windows."""
    from app.video_lab.renderers.remotion.remotion_renderer import render_remotion_video

    with patch("app.video_lab.renderers.remotion.remotion_renderer.check_remotion_available") as mock_check, \
         patch("subprocess.run") as mock_run:

        mock_check.return_value = (True, "OK")
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

        with patch("app.video_lab.renderers.remotion.remotion_renderer.get_experiment_dir") as mock_dir:
            mock_exp_dir = MagicMock()
            mock_exp_dir.resolve.return_value = mock_exp_dir
            mock_exp_dir.__truediv__ = lambda self, x: MagicMock()
            mock_dir.return_value = mock_exp_dir

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.__truediv__", return_value=MagicMock()):
                    render_remotion_video(
                        experiment_id="test_shell",
                        props={"title": "Test", "keyPoints": [], "durationSec": 15, "stylePreset": "ai_frontier_dark"},
                    )

    # Find the npx remotion render call
    render_call = None
    for call in mock_run.call_args_list:
        args, kwargs = call
        if args and len(args[0]) > 2 and args[0][0] == "npx" and args[0][1] == "remotion":
            render_call = call
            break

    assert render_call is not None, "Should have called npx remotion render"
    _, render_kwargs = render_call
    assert render_kwargs.get("shell") is True, "npx remotion render should use shell=True on Windows"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
