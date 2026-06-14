"""
Tests for V0.3.0: local_frame_renderer keyPoints fallback
Ensures renderer works when only keyPoints (not key_points) is provided.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.local_frame_renderer import generate_frames


def test_generate_frames_with_keyPoints_only():
    """generate_frames should work when key_points contains only keyPoints (not key_points)."""
    # Simulate adapter providing only keyPoints
    key_points = {
        "keyPoints": [
            {"title": "第一点", "source": "依据1"},
            {"title": "第二点", "source": "依据2"},
            {"title": "第三点", "source": "依据3"},
        ],
        "totalPoints": 3,
        "requestedKeyPointCount": 3,
        "actualKeyPointCount": 3,
    }

    structured = {
        "lead": "测试总起",
        "items": [],
        "totalItems": 0,
    }

    result = generate_frames(
        experiment_id="test_keypoints_fallback",
        structured=structured,
        key_points=key_points,
        target_duration_sec=15,
        resolution=(1080, 1920),
        enable_transitions=False,
        transition_frames=0,
        highlight_mode="auto",
        include_overview=False,
        include_summary=False,
    )

    # Should produce frames
    assert result["total_frames"] > 0
    # Should have keypoint frames
    keypoint_frames = [f for f in result["frames"] if f["type"] == "keypoint"]
    assert len(keypoint_frames) == 3, f"Expected 3 keypoint frames, got {len(keypoint_frames)}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
