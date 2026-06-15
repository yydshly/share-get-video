"""
Tests for the deterministic video quality assessor.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.quality import assess_quality


def _good_inputs():
    structured = {"lead": "总起", "totalItems": 2, "items": []}
    key_points = {"keyPoints": [
        {"title": "A 模型提升39%", "source": "依据：A"},
        {"title": "B 通过率0.84", "source": "依据：B"},
    ]}
    voiceover = {
        "voiceoverText": "开场。 A 模型提升39%。 B 通过率0.84。 结尾。",
        "segments": [
            {"index": 1, "text": "s1", "startSec": 0, "durationSec": 6},
            {"index": 2, "text": "s2", "startSec": 6, "durationSec": 6},
        ],
    }
    return structured, key_points, voiceover


def test_high_quality_passes():
    structured, key_points, voiceover = _good_inputs()
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=12.0, subtitle_count=2, subtitle_burned=True,
        visual_duration_sec=12.0, has_cover=True, frame_count=4, warnings=[],
    )
    d = report.to_dict()
    assert d["overallScore"] >= 4.5
    assert d["counts"]["fail"] == 0
    # 关键数字 39% / 0.84 应被判定为保留
    knum = next(c for c in d["checks"] if c["checkId"] == "key_numbers_preserved")
    assert knum["status"] == "pass"


def test_missing_key_number_flagged():
    structured, key_points, voiceover = _good_inputs()
    # 旁白丢掉 0.84
    voiceover["voiceoverText"] = "开场。 A 模型提升39%。 结尾。"
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=12.0, subtitle_count=2, subtitle_burned=True,
        visual_duration_sec=12.0, has_cover=True, frame_count=4, warnings=[],
    )
    knum = next(c for c in report.to_dict()["checks"] if c["checkId"] == "key_numbers_preserved")
    assert knum["status"] in ("warn", "fail")
    assert "0.84" in knum["value"]


def test_duplicate_keypoints_fail():
    structured = {"lead": "总起", "totalItems": 2, "items": []}
    key_points = {"keyPoints": [
        {"title": "重复", "source": "依据：A"},
        {"title": "重复", "source": "依据：B"},
    ]}
    voiceover = {"voiceoverText": "重复 重复", "segments": [
        {"index": 1, "text": "s", "startSec": 0, "durationSec": 5},
        {"index": 2, "text": "s", "startSec": 5, "durationSec": 5},
    ]}
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=10.0, subtitle_count=2, subtitle_burned=True,
        visual_duration_sec=10.0, has_cover=True, frame_count=3, warnings=[],
    )
    dup = next(c for c in report.to_dict()["checks"] if c["checkId"] == "no_duplication")
    assert dup["status"] == "fail"


def test_subtitle_audio_drift_detected():
    structured, key_points, voiceover = _good_inputs()
    # 字幕轴 12s，但实际音频 30s → 漂移大
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=30.0, subtitle_count=2, subtitle_burned=True,
        visual_duration_sec=12.0, has_cover=True, frame_count=4, warnings=[],
    )
    drift = next(c for c in report.to_dict()["checks"] if c["checkId"] == "subtitle_audio_drift")
    assert drift["status"] in ("warn", "fail")


def test_missing_subtitle_and_cover_warn():
    structured, key_points, voiceover = _good_inputs()
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=12.0, subtitle_count=0, subtitle_burned=False,
        visual_duration_sec=12.0, has_cover=False, frame_count=4, warnings=[],
    )
    checks = {c["checkId"]: c for c in report.to_dict()["checks"]}
    assert checks["subtitle_present"]["status"] == "warn"
    assert checks["has_cover"]["status"] == "warn"


def test_needs_human_dimensions_present():
    structured, key_points, voiceover = _good_inputs()
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=12.0, subtitle_count=2, subtitle_burned=True,
        visual_duration_sec=12.0, has_cover=True, frame_count=4, warnings=[],
    )
    assert "visual_aesthetics" in report.to_dict()["needsHuman"]


# ─── V0.3.6-b2: title_length threshold fix ─────────────────────────────────

def test_title_length_allows_6_char_titles():
    """6-char titles should NOT trigger title_length short warning."""
    structured = {"lead": "总起", "totalItems": 2, "items": []}
    # Two 6-char titles — these are within the 6-14 char valid range
    key_points = {"keyPoints": [
        {"title": "模型A突破", "source": "依据：1"},
        {"title": "模型B发布", "source": "依据：2"},
    ]}
    voiceover = {
        "voiceoverText": "开场。 模型A突破。 模型B发布。 结尾。",
        "segments": [
            {"index": 1, "text": "s1", "startSec": 0, "durationSec": 6},
            {"index": 2, "text": "s2", "startSec": 6, "durationSec": 6},
        ],
    }
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=12.0, subtitle_count=2, subtitle_burned=True,
        visual_duration_sec=12.0, has_cover=True, frame_count=4, warnings=[],
    )
    checks = {c["checkId"]: c for c in report.to_dict()["checks"]}
    # title_length should PASS (not warn) for 6-char titles
    assert checks["title_length"]["status"] == "pass", \
        f"6-char titles should pass, got: {checks['title_length']}"


def test_title_length_catches_truly_short_titles():
    """Titles < 5 chars should still trigger title_length warning."""
    structured = {"lead": "总起", "totalItems": 1, "items": []}
    key_points = {"keyPoints": [
        {"title": "突破", "source": "依据：1"},  # 2 chars — truly short
    ]}
    voiceover = {
        "voiceoverText": "开场。 突破。 结尾。",
        "segments": [{"index": 1, "text": "s1", "startSec": 0, "durationSec": 6}],
    }
    report = assess_quality(
        source_content="x", structured=structured, key_points=key_points, voiceover=voiceover,
        audio_duration_sec=6.0, subtitle_count=1, subtitle_burned=True,
        visual_duration_sec=6.0, has_cover=True, frame_count=2, warnings=[],
    )
    checks = {c["checkId"]: c for c in report.to_dict()["checks"]}
    # title_length should WARN for truly short titles (<5 chars)
    assert checks["title_length"]["status"] in ("warn", "fail"), \
        f"2-char title should warn, got: {checks['title_length']}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
