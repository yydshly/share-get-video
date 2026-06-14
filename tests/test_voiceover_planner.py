"""
Tests for V0.3.3 Voiceover Planner
- Generates Chinese voiceover text from structured content + key points
- No external dependencies
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.planners.voiceover_planner import generate_voiceover


def test_voiceover_generates_chinese_text():
    """Voiceover should generate Chinese text from key points."""
    structured = {
        "lead": "今天有三个AI信号值得关注。",
        "items": [],
        "totalItems": 1,
    }
    key_points = {
        "keyPoints": [
            {"title": "GPT-5 发布", "body": "性能提升显著", "source": "OpenAI"},
            {"title": "Claude 4 发布", "body": "上下文更长", "source": "Anthropic"},
        ]
    }

    result = generate_voiceover(structured, key_points, target_duration_sec=30)

    assert "voiceoverText" in result
    assert len(result["voiceoverText"]) > 0
    assert isinstance(result["segments"], list)
    assert len(result["segments"]) >= 2
    assert result["estimatedDurationSec"] > 0


def test_voiceover_has_segments_with_timing():
    """Voiceover segments should have index, text, startSec, durationSec."""
    structured = {"lead": "测试 lead", "items": [], "totalItems": 0}
    key_points = {
        "keyPoints": [
            {"title": "Point 1", "body": "Body 1", "source": ""},
            {"title": "Point 2", "body": "Body 2", "source": ""},
        ]
    }

    result = generate_voiceover(structured, key_points, target_duration_sec=20)

    for seg in result["segments"]:
        assert "index" in seg
        assert "text" in seg
        assert "startSec" in seg
        assert "durationSec" in seg
        assert isinstance(seg["text"], str)
        assert seg["durationSec"] > 0


def test_voiceover_fallback_on_empty_keypoints():
    """Should handle empty key points gracefully."""
    structured = {"lead": "只有一个 lead 的内容", "items": [], "totalItems": 0}
    key_points = {"keyPoints": []}

    result = generate_voiceover(structured, key_points, target_duration_sec=10)

    assert result["voiceoverText"] != ""
    assert len(result["segments"]) >= 1


def test_voiceover_segments_are_timed():
    """Segments should have non-overlapping start times."""
    structured = {"lead": "Lead text", "items": [], "totalItems": 0}
    key_points = {
        "keyPoints": [
            {"title": f"Point {i}", "body": "Body", "source": ""}
            for i in range(4)
        ]
    }

    result = generate_voiceover(structured, key_points, target_duration_sec=20)
    segments = result["segments"]

    # Check no overlap
    for i in range(len(segments) - 1):
        curr_end = segments[i]["startSec"] + segments[i]["durationSec"]
        next_start = segments[i + 1]["startSec"]
        assert curr_end <= next_start, f"Overlap detected: {curr_end} > {next_start}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
