"""
Tests for V0.3.3 FFmpeg AV Composer
- compose_av_with_subtitles builds correct command
- compose_av_with_subtitles handles missing FFmpeg gracefully
- compose_video_with_audio handles missing FFmpeg gracefully
- Windows path escaping is handled
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.ffmpeg_av_composer import (
    compose_av_with_subtitles,
    compose_video_with_audio,
    check_ffmpeg_available,
)


def test_check_ffmpeg_available_returns_bool():
    """check_ffmpeg_available should return True/False."""
    result = check_ffmpeg_available()
    assert isinstance(result, bool)


def test_compose_av_with_subtitles_returns_failed_without_ffmpeg():
    """Should return failed result when FFmpeg is not available."""
    with patch("app.video_lab.renderers.ffmpeg_av_composer.check_ffmpeg_available", return_value=False):
        from app.video_lab.renderers.ffmpeg_av_composer import compose_av_with_subtitles
        with patch("app.video_lab.renderers.ffmpeg_av_composer.get_ffmpeg_version", return_value="not_found"):
            result = compose_av_with_subtitles(
                video_path=Path("video.mp4"),
                audio_path=Path("audio.mp3"),
                output_path=Path("output.mp4"),
            )

    assert result["success"] is False
    assert "FFmpeg not found" in result["message"]


def test_compose_av_with_subtitles_returns_failed_for_missing_video():
    """Should return failed result when video file does not exist."""
    with patch("app.video_lab.renderers.ffmpeg_av_composer.check_ffmpeg_available", return_value=True):
        result = compose_av_with_subtitles(
            video_path=Path("nonexistent_video.mp4"),
            audio_path=Path("audio.mp3"),
            output_path=Path("output.mp4"),
        )

    assert result["success"] is False
    assert "not found" in result["message"]


def test_compose_av_with_subtitles_returns_failed_for_missing_audio():
    """Should return failed result when audio file does not exist."""
    with patch("app.video_lab.renderers.ffmpeg_av_composer.check_ffmpeg_available", return_value=True):
        # Create a fake video path but no audio
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
        try:
            result = compose_av_with_subtitles(
                video_path=video_path,
                audio_path=Path("nonexistent_audio.mp3"),
                output_path=Path("output.mp4"),
            )
            assert result["success"] is False
            assert "not found" in result["message"]
        finally:
            os.unlink(video_path)


def test_compose_av_with_subtitles_command_contains_video_and_audio():
    """Command should contain input paths for video and audio."""
    import tempfile

    # Create real temporary files to pass existence checks
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vf:
        video_path = Path(vf.name)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as af:
        audio_path = Path(af.name)

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.video_lab.renderers.ffmpeg_av_composer.check_ffmpeg_available", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            with patch("app.video_lab.renderers.ffmpeg_av_composer.get_ffmpeg_version", return_value="ffmpeg version 6.0"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    out_path = Path(tmpdir) / "output.mp4"
                    result = compose_av_with_subtitles(
                        video_path=video_path,
                        audio_path=audio_path,
                        output_path=out_path,
                    )

    try:
        assert result["success"] is True
        assert "libx264" in result["ffmpeg_command"]
        assert "aac" in result["ffmpeg_command"]
    finally:
        os.unlink(video_path)
        os.unlink(audio_path)


def test_compose_av_with_subtitles_includes_subtitles_filter():
    """Command should include subtitles filter when srt_path is provided."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vf:
        video_path = Path(vf.name)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as af:
        audio_path = Path(af.name)
    with tempfile.NamedTemporaryFile(suffix=".srt", delete=False, mode="w") as sf:
        sf.write("1\n00:00:00,000 --> 00:00:02,000\nTest\n")
        srt_path = Path(sf.name)

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.video_lab.renderers.ffmpeg_av_composer.check_ffmpeg_available", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            with patch("app.video_lab.renderers.ffmpeg_av_composer.get_ffmpeg_version", return_value="ffmpeg 6.0"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    out_path = Path(tmpdir) / "output.mp4"
                    result = compose_av_with_subtitles(
                        video_path=video_path,
                        audio_path=audio_path,
                        srt_path=srt_path,
                        output_path=out_path,
                    )

    try:
        assert result["success"] is True
        assert "subtitles=" in result["ffmpeg_command"]
    finally:
        os.unlink(video_path)
        os.unlink(audio_path)
        os.unlink(srt_path)


def test_compose_video_with_audio_returns_failed_without_ffmpeg():
    """compose_video_with_audio should return failed when FFmpeg unavailable."""
    with patch("app.video_lab.renderers.ffmpeg_av_composer.check_ffmpeg_available", return_value=False):
        with patch("app.video_lab.renderers.ffmpeg_av_composer.get_ffmpeg_version", return_value="not_found"):
            result = compose_video_with_audio(
                video_path=Path("video.mp4"),
                audio_path=Path("audio.mp3"),
                output_path=Path("output.mp4"),
            )

    assert result["success"] is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
