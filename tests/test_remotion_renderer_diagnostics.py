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

    def test_windows_shell_true_gets_string(self):
        """On Windows (shell=True), subprocess.run must receive a string command."""
        from app.video_lab.renderers.remotion import remotion_renderer

        original_shell = remotion_renderer.USE_SHELL
        remotion_renderer.USE_SHELL = True

        try:
            with patch.object(remotion_renderer.subprocess, "run") as mock_run:
                mock_run.return_value = MockCompletedProcess(0, "", "")
                remotion_renderer._run_command(
                    ["npx", "--version"], Path("D:/test"), 10
                )

                call_args = mock_run.call_args
                cmd_arg = call_args[0][0] if call_args[0] else call_args[1].get("args")
                assert isinstance(cmd_arg, str), f"Expected str on Windows, got {type(cmd_arg)}"
        finally:
            remotion_renderer.USE_SHELL = original_shell

    def test_non_windows_shell_false_gets_list(self):
        """On non-Windows (shell=False), subprocess.run must receive a list command."""
        from app.video_lab.renderers.remotion import remotion_renderer

        original_shell = remotion_renderer.USE_SHELL
        remotion_renderer.USE_SHELL = False

        try:
            with patch.object(remotion_renderer.subprocess, "run") as mock_run:
                mock_run.return_value = MockCompletedProcess(0, "", "")
                remotion_renderer._run_command(
                    ["npx", "--version"], Path("/tmp/test"), 10
                )

                call_args = mock_run.call_args
                cmd_arg = call_args[0][0] if call_args[0] else call_args[1].get("args")
                assert isinstance(cmd_arg, list), f"Expected list on non-Windows, got {type(cmd_arg)}"
        finally:
            remotion_renderer.USE_SHELL = original_shell
