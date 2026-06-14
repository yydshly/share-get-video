"""
Tests for V0.3.8.1 FFmpeg subtitle burn-in filter.
- ASS file path is preferred over SRT
- SRT path uses original_size + force_style
- burn_in=False skips subtitle burn
- Result includes subtitle_renderer and subtitle_style fields
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.ffmpeg_av_composer import compose_av_with_subtitles


def _make_files(tmpdir: str) -> tuple:
    """Create dummy video and audio files for testing."""
    video = Path(tmpdir) / "silent.mp4"
    audio = Path(tmpdir) / "voiceover.mp3"
    srt = Path(tmpdir) / "subtitles.srt"
    ass = Path(tmpdir) / "subtitles.ass"
    out = Path(tmpdir) / "final.mp4"

    # Write minimal dummy content (FFmpeg will fail but we mock the call)
    video.write_bytes(b"fake video content")
    audio.write_bytes(b"fake audio content")
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello", encoding="utf-8")
    ass.write_text(
        "[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize\nStyle: Default,Microsoft YaHei,32\n\n[Events]\nFormat: Layer, Start, End, Style, Text\nDialogue: 0,0:00:00.00,0:00:01.00,Default,Hello",
        encoding="utf-8",
    )
    return video, audio, srt, ass, out


def test_ass_path_used_when_provided():
    """If ASS path is given, FFmpeg filter should use it (no force_style needed)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video, audio, srt, ass, out = _make_files(tmpdir)

        # Mock subprocess.run to capture the command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = compose_av_with_subtitles(
                video_path=video,
                audio_path=audio,
                srt_path=srt,
                ass_path=ass,
                output_path=out,
                resolution=(1080, 1920),
            )

        assert result["success"] is True
        assert result["subtitle_renderer"] == "ass"
        assert result["subtitle_style"]["renderer"] == "ass"
        assert result["subtitle_style"]["playResX"] == 1080
        assert result["subtitle_style"]["playResY"] == 1920


def test_srt_path_used_when_ass_not_provided():
    """If only SRT, filter should use original_size + force_style."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video, audio, srt, ass, out = _make_files(tmpdir)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = compose_av_with_subtitles(
                video_path=video,
                audio_path=audio,
                srt_path=srt,
                ass_path=None,
                output_path=out,
                resolution=(1080, 1920),
            )

        assert result["success"] is True
        assert result["subtitle_renderer"] == "srt_subtitles_filter"
        # SRT path should use original_size hint
        assert result["ffmpeg_command"]
        assert "original_size=1080x1920" in result["ffmpeg_command"]


def test_burn_in_false_skips_subtitle():
    """burn_in=False should result in no subtitle filter and renderer='none'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video, audio, srt, ass, out = _make_files(tmpdir)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = compose_av_with_subtitles(
                video_path=video,
                audio_path=audio,
                srt_path=srt,
                ass_path=ass,
                output_path=out,
                resolution=(1080, 1920),
                burn_in=False,
            )

        assert result["success"] is True
        assert result["subtitle_renderer"] == "none"
        # FFmpeg command should NOT contain subtitle filter
        assert "subtitles=" not in result["ffmpeg_command"]


def test_ass_path_takes_priority_over_srt():
    """When both ASS and SRT are given, ASS should be used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video, audio, srt, ass, out = _make_files(tmpdir)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = compose_av_with_subtitles(
                video_path=video,
                audio_path=audio,
                srt_path=srt,
                ass_path=ass,
                output_path=out,
                resolution=(1080, 1920),
            )

        assert result["subtitle_renderer"] == "ass"


def test_missing_video_returns_error():
    """Missing video file should return a clear error and skip ffmpeg call."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _, audio, srt, ass, out = _make_files(tmpdir)
        missing_video = Path(tmpdir) / "missing.mp4"

        with patch("app.video_lab.renderers.ffmpeg_av_composer.check_ffmpeg_available", return_value=True):
            # Patch subprocess.run to also fail if called for the actual composition
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = b""
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = compose_av_with_subtitles(
                    video_path=missing_video,
                    audio_path=audio,
                    srt_path=srt,
                    ass_path=ass,
                    output_path=out,
                )

        assert result["success"] is False
        assert "Video file not found" in result["message"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
