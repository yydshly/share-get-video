"""
Tests for V0.3.3 Subtitle Planner (SRT generation)
- Generates SRT files from voiceover segments
- No external dependencies
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.planners.subtitle_planner import generate_srt_from_segments, _format_srt_time, _split_subtitle_text


def test_format_srt_time():
    """SRT time format should be HH:MM:SS,mmm."""
    assert _format_srt_time(0.0) == "00:00:00,000"
    assert _format_srt_time(1.5) == "00:00:01,500"
    assert _format_srt_time(65.3) == "00:01:05,300"
    assert _format_srt_time(3661.123) == "01:01:01,123"


def test_split_subtitle_text():
    """Subtitle text should be split into reasonable-length lines."""
    text = "今天有三个AI信号值得关注，分别是GPT-5发布、Claude 4发布和Gemini Ultra更新。"
    lines = _split_subtitle_text(text, max_chars=15)
    assert len(lines) > 1
    for line in lines:
        assert len(line) <= 15


def test_srt_generation_from_segments():
    """SRT generation should produce valid SRT content."""
    segments = [
        {"text": "今天为大家带来AI前沿资讯。", "startSec": 0.0, "durationSec": 3.5},
        {"text": "第一条：GPT-5 发布，性能大幅提升。", "startSec": 3.5, "durationSec": 5.0},
    ]

    result = generate_srt_from_segments(segments)

    assert result["format"] == "srt"
    assert len(result["subtitles"]) == 2
    assert result["subtitles"][0]["text"] == "今天为大家带来AI前沿资讯。"
    assert result["subtitles"][0]["startSec"] == 0.0
    assert result["subtitles"][0]["endSec"] == 3.5


def test_srt_file_written():
    """SRT file should be written to output_path."""
    segments = [
        {"text": "测试字幕", "startSec": 0.0, "durationSec": 2.0},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        srt_path = Path(tmpdir) / "test.srt"
        result = generate_srt_from_segments(segments, output_path=srt_path)

        assert srt_path.exists(), "SRT file should be created"
        content = srt_path.read_text(encoding="utf-8")
        assert "测试字幕" in content
        assert "00:00:00,000 --> 00:00:02,000" in content
        assert result["srtPath"] != ""
        assert result["srtUrl"] != ""


def test_srt_content_format():
    """SRT content should follow standard format: index, time, text, blank line."""
    segments = [
        {"text": "第一行字幕", "startSec": 0.0, "durationSec": 2.0},
        {"text": "第二行字幕", "startSec": 2.0, "durationSec": 3.0},
    ]

    from app.video_lab.planners.subtitle_planner import _build_srt_content
    subtitles = [{"startSec": 0.0, "endSec": 2.0, "text": "第一行字幕"},
                {"startSec": 2.0, "endSec": 5.0, "text": "第二行字幕"}]
    content = _build_srt_content(subtitles)

    lines = content.split("\n")
    assert "1" in lines
    assert "2" in lines
    assert "第一行字幕" in content
    assert "第二行字幕" in content


def test_empty_segments_handled():
    """Empty segment list should produce empty SRT."""
    result = generate_srt_from_segments([])
    assert result["subtitles"] == []
    assert result["format"] == "srt"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
