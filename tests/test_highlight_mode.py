"""
Tests for V0.2.5 highlightMode support in text_layout
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.text_layout import extract_highlights, extract_highlights_by_mode


# ─────────────────────────────────────────────
# extract_highlights (backward compat + delegates to auto)
# ─────────────────────────────────────────
def test_extract_highlights_basic():
    """extract_highlights should find percentages and multipliers."""
    text = "错误拒绝率从88.9%降至16%，成本高出10倍"
    result = extract_highlights(text)
    assert "88.9%" in result
    assert "16%" in result
    assert "10倍" in result


def test_extract_highlights_large_numbers():
    """extract_highlights should find large Chinese numbers."""
    text = "BBVA部署至10万名员工，OpenMedQ参数量达5620亿"
    result = extract_highlights(text)
    assert "10万" in result
    assert "5620亿" in result


# ─────────────────────────────────────────────
# extract_highlights_by_mode - auto mode
# ─────────────────────────────────────────
def test_extract_highlights_by_mode_auto():
    """Mode auto should extract all highlight types."""
    text = "错误拒绝率从88.9%降至16%，成本高出10倍，BBVA部署至10万名员工"
    result = extract_highlights_by_mode(text, "auto")
    assert "88.9%" in result
    assert "16%" in result
    assert "10倍" in result
    assert "10万" in result


def test_extract_highlights_by_mode_auto_deduplicates():
    """Mode auto should deduplicate results."""
    text = "88.9% 16% 88.9% 16%"
    result = extract_highlights_by_mode(text, "auto")
    assert result.count("88.9%") == 1
    assert result.count("16%") == 1


# ─────────────────────────────────────────────
# extract_highlights_by_mode - numbers mode
# ─────────────────────────────────────────
def test_extract_highlights_by_mode_numbers():
    """Mode numbers should only extract numeric patterns."""
    text = "错误拒绝率从88.9%降至16%，成本高出10倍，BBVA部署至10万名员工"
    result = extract_highlights_by_mode(text, "numbers")
    assert "88.9%" in result
    assert "16%" in result
    assert "10倍" in result
    # numbers mode should NOT include Chinese number phrases
    assert "10万" not in result
    assert "5620亿" not in result


def test_extract_highlights_by_mode_numbers_percentages():
    """Mode numbers should find percentages."""
    text = "准确率 88.9% 错误率 16%"
    result = extract_highlights_by_mode(text, "numbers")
    assert "88.9%" in result
    assert "16%" in result


def test_extract_highlights_by_mode_numbers_multipliers():
    """Mode numbers should find multipliers like 10x and 10倍."""
    text = "性能提升5x，成本降低3倍"
    result = extract_highlights_by_mode(text, "numbers")
    assert "5x" in result or "5X" in result
    assert "3倍" in result


# ─────────────────────────────────────────────
# extract_highlights_by_mode - none mode
# ─────────────────────────────────────────
def test_extract_highlights_by_mode_none():
    """Mode none should return empty list."""
    text = "错误拒绝率从88.9%降至16%，成本高出10倍，BBVA部署至10万名员工"
    result = extract_highlights_by_mode(text, "none")
    assert result == []


def test_extract_highlights_by_mode_none_empty_text():
    """Mode none with empty text should return empty list."""
    result = extract_highlights_by_mode("", "none")
    assert result == []


# ─────────────────────────────────────────────
# extract_highlights_by_mode - edge cases
# ─────────────────────────────────────────
def test_extract_highlights_by_mode_invalid_mode():
    """Invalid mode should behave like auto."""
    text = "88.9% 10倍"
    result = extract_highlights_by_mode(text, "invalid_mode")
    assert "88.9%" in result
    assert "10倍" in result


def test_extract_highlights_by_mode_empty_text():
    """Empty text should return empty list."""
    result = extract_highlights_by_mode("", "auto")
    assert result == []


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
