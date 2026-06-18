"""
Tests for Remotion renderer subprocess diagnostics and robustness.

Covers:
- stdout/stderr=None does not raise TypeError
- stderr empty → fallback to stdout in message
- returncode always logged
- Windows shell=True gets string command, non-Windows gets list
- failure message contains stderr or stdout tail
"""

import sys
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class MockCompletedProcess:
    """Minimal CompletedProcess stand-in."""

    def __init__(self, returncode: int, stdout=None, stderr=None):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestRemotionRendererDiagnostics:
    """Tests for render_remotion_video diagnostics robustness."""

    def test_default_timeout_scales_with_duration(self):
        """Long videos should not inherit the fixed 300s render budget."""
        from app.video_lab.renderers.remotion import remotion_renderer

        assert remotion_renderer.default_remotion_timeout({"durationSec": 15}) == 300
        assert remotion_renderer.default_remotion_timeout({"durationSec": 105.31}) == 751
        assert remotion_renderer.default_remotion_timeout({"durationSec": 160.74}) > 900
        assert remotion_renderer.default_remotion_timeout({"durationSec": 9999}) == 1200

    def test_long_portrait_render_uses_bounded_concurrency(self):
        from app.video_lab.renderers.remotion import remotion_renderer

        assert remotion_renderer.default_remotion_concurrency({"durationSec": 20}) == "75%"
        assert remotion_renderer.default_remotion_concurrency({"durationSec": 60}) == "12"
        assert remotion_renderer.default_remotion_concurrency({"durationSec": 105.31}) == "8"

    def test_render_command_uses_fast_server_render_flags(self, tmp_path):
        """Remotion command should use bounded quality and concurrency flags."""
        from app.video_lab.renderers.remotion import remotion_renderer

        captured = {}

        def fake_run(cmd, cwd, timeout):
            captured["cmd"] = cmd
            captured["timeout"] = timeout
            return MockCompletedProcess(returncode=1, stdout="", stderr="boom")

        with patch.object(remotion_renderer, "_run_command", side_effect=fake_run):
            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir", return_value=tmp_path):
                    result = remotion_renderer.render_remotion_video(
                        "test_exp",
                        {"title": "Test", "durationSec": 160.74},
                    )

        assert result["success"] is False
        cmd = captured["cmd"]
        assert "--x264-preset" in cmd
        assert "veryfast" in cmd
        assert "--crf" in cmd
        assert "26" in cmd
        assert "--concurrency" in cmd
        assert "8" in cmd
        assert captured["timeout"] > 300

    def test_timeout_message_includes_last_render_progress(self, tmp_path):
        from app.video_lab.renderers.remotion import remotion_renderer

        timeout_error = subprocess.TimeoutExpired(
            "remotion",
            5,
            output="Rendered 120/300\nRendered 121/300, time remaining: 20s\n",
        )
        with patch.object(remotion_renderer, "_run_command", side_effect=timeout_error):
            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir", return_value=tmp_path):
                    result = remotion_renderer.render_remotion_video(
                        "test_exp",
                        {"title": "Test", "durationSec": 12.0},
                        timeout=5,
                    )

        assert result["success"] is False
        assert "Rendered 121/300" in result["message"]
        assert "timeout output tail" in "\n".join(result["logs"])

    def test_timeout_recovers_valid_completed_mp4(self, tmp_path):
        """If Remotion finishes an MP4 at the timeout boundary, return success."""
        from app.video_lab.renderers.remotion import remotion_renderer

        output = tmp_path / "output.mp4"
        output.write_bytes(b"fake but probed")

        with patch.object(remotion_renderer, "_run_command", side_effect=subprocess.TimeoutExpired("remotion", 5)):
            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir", return_value=tmp_path):
                    with patch.object(remotion_renderer, "_probe_mp4_duration", return_value=12.0):
                        with patch.object(remotion_renderer, "write_manifest") as mock_write:
                            result = remotion_renderer.render_remotion_video(
                                "test_exp",
                                {"title": "Test", "durationSec": 12.0},
                                timeout=5,
                            )

        assert result["success"] is True
        assert "timed out" in " ".join(result["warnings"]).lower()
        manifest = mock_write.call_args[0][1]
        assert manifest["recoveredAfterTimeout"] is True
        assert manifest["recoveredDurationSec"] == 12.0

    def test_stdout_stderr_none_no_type_error(self):
        """render_remotion_video must not raise TypeError when stdout/stderr are None."""
        from app.video_lab.renderers.remotion import remotion_renderer

        # Mock subprocess.run to return None for stdout/stderr
        with patch.object(remotion_renderer.subprocess, "run") as mock_run:
            mock_run.return_value = MockCompletedProcess(returncode=1, stdout=None, stderr=None)

            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir") as mock_dir:
                    mock_exp_dir = MagicMock()
                    mock_exp_dir.resolve.return_value = Path("D:/test/exp")
                    mock_dir.return_value = mock_exp_dir

                    # Must not raise TypeError or any other exception
                    result = remotion_renderer.render_remotion_video("test_exp", {"title": "Test"}, timeout=5)

                    assert result["success"] is False
                    assert "code 1" in result["message"]

    def test_stderr_with_value_in_message(self):
        """Failure message must contain stderr when stderr is non-empty."""
        from app.video_lab.renderers.remotion import remotion_renderer

        with patch.object(remotion_renderer.subprocess, "run") as mock_run:
            mock_run.return_value = MockCompletedProcess(
                returncode=1, stdout="", stderr="Chrome failed to launch"
            )

            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir") as mock_dir:
                    mock_exp_dir = MagicMock()
                    mock_exp_dir.resolve.return_value = Path("D:/test/exp")
                    mock_dir.return_value = mock_exp_dir

                    result = remotion_renderer.render_remotion_video("test_exp", {"title": "Test"}, timeout=5)

                    assert "Chrome failed to launch" in result["message"]

    def test_stderr_empty_fallback_to_stdout(self):
        """When stderr is empty but stdout has content, message must include stdout."""
        from app.video_lab.renderers.remotion import remotion_renderer

        with patch.object(remotion_renderer.subprocess, "run") as mock_run:
            mock_run.return_value = MockCompletedProcess(
                returncode=1, stdout="Composition not found", stderr=""
            )

            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir") as mock_dir:
                    mock_exp_dir = MagicMock()
                    mock_exp_dir.resolve.return_value = Path("D:/test/exp")
                    mock_dir.return_value = mock_exp_dir

                    result = remotion_renderer.render_remotion_video("test_exp", {"title": "Test"}, timeout=5)

                    assert "Composition not found" in result["message"]

    def test_logs_contain_returncode(self):
        """Logs must contain returncode even on success-like paths."""
        from app.video_lab.renderers.remotion import remotion_renderer

        with patch.object(remotion_renderer.subprocess, "run") as mock_run:
            mock_run.return_value = MockCompletedProcess(
                returncode=1, stdout="", stderr="error"
            )

            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir") as mock_dir:
                    mock_exp_dir = MagicMock()
                    mock_exp_dir.resolve.return_value = Path("D:/test/exp")
                    mock_dir.return_value = mock_exp_dir

                    result = remotion_renderer.render_remotion_video("test_exp", {"title": "Test"}, timeout=5)

                    logs_text = " ".join(result["logs"])
                    assert "returncode" in logs_text

    def test_logs_contain_stdout_stderr(self):
        """Logs must contain stdout and stderr (or <empty>) entries."""
        from app.video_lab.renderers.remotion import remotion_renderer

        with patch.object(remotion_renderer.subprocess, "run") as mock_run:
            mock_run.return_value = MockCompletedProcess(
                returncode=1, stdout="out text", stderr="err text"
            )

            with patch.object(remotion_renderer, "check_remotion_available", return_value=(True, "ok")):
                with patch.object(remotion_renderer, "get_experiment_dir") as mock_dir:
                    mock_exp_dir = MagicMock()
                    mock_exp_dir.resolve.return_value = Path("D:/test/exp")
                    mock_dir.return_value = mock_exp_dir

                    result = remotion_renderer.render_remotion_video("test_exp", {"title": "Test"}, timeout=5)

                    logs_text = " ".join(result["logs"])
                    assert "stdout" in logs_text
                    assert "stderr" in logs_text


class TestRunCommandPlatform:
    """Tests for _run_command cross-platform behavior."""

    def test_command_always_runs_without_shell_wrapper(self):
        """Renderer commands should not wait on a lingering Windows cmd.exe."""
        from app.video_lab.renderers.remotion import remotion_renderer

        with patch.object(remotion_renderer.subprocess, "run") as mock_run:
            mock_run.return_value = MockCompletedProcess(0, "", "")
            remotion_renderer._run_command(
                ["node", "remotion-cli.js", "--version"], Path("D:/test"), 10
            )

            call_args = mock_run.call_args
            cmd_arg = call_args[0][0] if call_args[0] else call_args[1].get("args")
            assert isinstance(cmd_arg, list)
            assert call_args[1]["shell"] is False
