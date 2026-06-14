"""
Tests for V0.2.5 render_params - LocalFrameRenderParams and parse_local_frame_params
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.render_params import (
    parse_local_frame_params,
    LocalFrameRenderParams,
    ParseResult,
    VALID_STYLE_PRESETS,
    VALID_HIGHLIGHT_MODES,
)


# ─────────────────────────────────────────────
# LocalFrameRenderParams Defaults
# ─────────────────────────────────────────
def test_local_frame_render_params_defaults():
    """Default values should be set correctly."""
    params = LocalFrameRenderParams()
    assert params.style_preset == "ai_frontier_dark"
    assert params.target_duration == 45
    assert params.aspect_ratio == "9:16"
    assert params.key_point_count == 6
    assert params.highlight_mode == "auto"
    assert params.transition_enabled is True
    assert params.transition_frames == 4
    assert params.include_overview is True
    assert params.include_summary is True


def test_local_frame_render_params_to_dict():
    """to_dict should convert to camelCase keys."""
    params = LocalFrameRenderParams(
        style_preset="ai_frontier_dark",
        target_duration=45,
        key_point_count=6,
        highlight_mode="auto",
        transition_enabled=True,
        transition_frames=4,
    )
    d = params.to_dict()
    assert d["stylePreset"] == "ai_frontier_dark"
    assert d["targetDuration"] == 45
    assert d["keyPointCount"] == 6
    assert d["highlightMode"] == "auto"
    assert d["transitionEnabled"] is True
    assert d["transitionFrames"] == 4
    assert d["aspectRatio"] == "9:16"
    assert d["includeOverview"] is True
    assert d["includeSummary"] is True


# ─────────────────────────────────────────────
# parse_local_frame_params - Valid params
# ─────────────────────────────────────────
def test_parse_with_valid_params():
    """Valid params should return valid ParseResult."""
    params = {
        "targetDuration": 30,
        "aspectRatio": "9:16",
        "keyPointCount": 4,
        "highlightMode": "auto",
        "transitionEnabled": True,
        "transitionFrames": 2,
        "stylePreset": "ai_frontier_dark",
    }
    result = parse_local_frame_params(params)
    assert result.is_valid is True
    assert result.error is None
    assert result.params is not None
    assert result.params.target_duration == 30
    assert result.params.key_point_count == 4
    assert result.params.highlight_mode == "auto"
    assert result.params.transition_enabled is True
    assert result.params.transition_frames == 2


def test_parse_empty_params_returns_defaults():
    """Empty params should return defaults with warning."""
    result = parse_local_frame_params({})
    assert result.is_valid is True
    assert result.params is not None
    assert result.params.target_duration == 45
    assert len(result.warnings) > 0


def test_parse_none_params_returns_defaults():
    """None params should return defaults with warning."""
    result = parse_local_frame_params(None)
    assert result.is_valid is True
    assert result.params is not None
    assert result.params.target_duration == 45


# ─────────────────────────────────────────────
# targetDuration boundaries
# ─────────────────────────────────────────
def test_parse_target_duration_clamp_low():
    """targetDuration below 15 should clamp to 15."""
    result = parse_local_frame_params({"targetDuration": 5})
    assert result.is_valid is True
    assert result.params.target_duration == 15
    assert any("clamping" in w.lower() for w in result.warnings)


def test_parse_target_duration_clamp_high():
    """targetDuration above 90 should clamp to 90."""
    result = parse_local_frame_params({"targetDuration": 200})
    assert result.is_valid is True
    assert result.params.target_duration == 90
    assert any("clamping" in w.lower() for w in result.warnings)


def test_parse_target_duration_boundary_min():
    """targetDuration at 15 should be valid."""
    result = parse_local_frame_params({"targetDuration": 15})
    assert result.is_valid is True
    assert result.params.target_duration == 15


def test_parse_target_duration_boundary_max():
    """targetDuration at 90 should be valid."""
    result = parse_local_frame_params({"targetDuration": 90})
    assert result.is_valid is True
    assert result.params.target_duration == 90


def test_parse_target_duration_invalid_type():
    """Invalid targetDuration type should fallback to 45."""
    result = parse_local_frame_params({"targetDuration": "invalid"})
    assert result.is_valid is True
    assert result.params.target_duration == 45


# ─────────────────────────────────────────────
# keyPointCount boundaries
# ─────────────────────────────────────────
def test_parse_key_point_count_clamp_low():
    """keyPointCount below 1 should clamp to 1."""
    result = parse_local_frame_params({"keyPointCount": 0})
    assert result.is_valid is True
    assert result.params.key_point_count == 1


def test_parse_key_point_count_clamp_high():
    """keyPointCount above 10 should clamp to 10."""
    result = parse_local_frame_params({"keyPointCount": 20})
    assert result.is_valid is True
    assert result.params.key_point_count == 10


def test_parse_key_point_count_boundary_min():
    """keyPointCount at 1 should be valid."""
    result = parse_local_frame_params({"keyPointCount": 1})
    assert result.is_valid is True
    assert result.params.key_point_count == 1


def test_parse_key_point_count_boundary_max():
    """keyPointCount at 10 should be valid."""
    result = parse_local_frame_params({"keyPointCount": 10})
    assert result.is_valid is True
    assert result.params.key_point_count == 10


def test_parse_key_point_count_invalid_type():
    """Invalid keyPointCount type should fallback to 6."""
    result = parse_local_frame_params({"keyPointCount": "invalid"})
    assert result.is_valid is True
    assert result.params.key_point_count == 6


# ─────────────────────────────────────────────
# transitionFrames boundaries
# ─────────────────────────────────────────
def test_parse_transition_frames_clamp_low():
    """transitionFrames below 0 should clamp to 0."""
    result = parse_local_frame_params({"transitionFrames": -5})
    assert result.is_valid is True
    assert result.params.transition_frames == 0


def test_parse_transition_frames_clamp_high():
    """transitionFrames above 8 should clamp to 8."""
    result = parse_local_frame_params({"transitionFrames": 20})
    assert result.is_valid is True
    assert result.params.transition_frames == 8


def test_parse_transition_frames_boundary_min():
    """transitionFrames at 0 should be valid."""
    result = parse_local_frame_params({"transitionFrames": 0})
    assert result.is_valid is True
    assert result.params.transition_frames == 0


def test_parse_transition_frames_boundary_max():
    """transitionFrames at 8 should be valid."""
    result = parse_local_frame_params({"transitionFrames": 8})
    assert result.is_valid is True
    assert result.params.transition_frames == 8


def test_parse_transition_frames_zero_disables_transitions():
    """transitionFrames=0 should set transitionEnabled=False."""
    result = parse_local_frame_params({"transitionFrames": 0, "transitionEnabled": True})
    assert result.is_valid is True
    assert result.params.transition_frames == 0
    assert result.params.transition_enabled is False


# ─────────────────────────────────────────────
# highlightMode validation
# ─────────────────────────────────────────
def test_parse_highlight_mode_auto():
    """highlightMode=auto should be valid."""
    result = parse_local_frame_params({"highlightMode": "auto"})
    assert result.is_valid is True
    assert result.params.highlight_mode == "auto"


def test_parse_highlight_mode_numbers():
    """highlightMode=numbers should be valid."""
    result = parse_local_frame_params({"highlightMode": "numbers"})
    assert result.is_valid is True
    assert result.params.highlight_mode == "numbers"


def test_parse_highlight_mode_none():
    """highlightMode=none should be valid."""
    result = parse_local_frame_params({"highlightMode": "none"})
    assert result.is_valid is True
    assert result.params.highlight_mode == "none"


def test_parse_highlight_mode_invalid_fallback():
    """Invalid highlightMode should fallback to auto."""
    result = parse_local_frame_params({"highlightMode": "invalid_mode"})
    assert result.is_valid is True
    assert result.params.highlight_mode == "auto"
    assert any("highlightMode" in w for w in result.warnings)


# ─────────────────────────────────────────────
# stylePreset validation
# ─────────────────────────────────────────
def test_parse_style_preset_valid():
    """Valid stylePreset should be accepted."""
    result = parse_local_frame_params({"stylePreset": "ai_frontier_dark"})
    assert result.is_valid is True
    assert result.params.style_preset == "ai_frontier_dark"


def test_parse_style_preset_invalid_fallback():
    """Invalid stylePreset should fallback to default."""
    result = parse_local_frame_params({"stylePreset": "unknown_preset"})
    assert result.is_valid is True
    assert result.params.style_preset == "ai_frontier_dark"
    assert any("stylePreset" in w for w in result.warnings)


# ─────────────────────────────────────────────
# aspectRatio handling
# ─────────────────────────────────────────
def test_parse_aspect_ratio_9_16():
    """aspectRatio=9:16 should be valid."""
    result = parse_local_frame_params({"aspectRatio": "9:16"})
    assert result.is_valid is True
    assert result.params.aspect_ratio == "9:16"


def test_parse_aspect_ratio_16_9():
    """aspectRatio=16:9 should be valid."""
    result = parse_local_frame_params({"aspectRatio": "16:9"})
    assert result.is_valid is True
    assert result.params.aspect_ratio == "16:9"


def test_parse_aspect_ratio_nonstandard_warning():
    """Non-standard aspectRatio should emit warning but use as-is."""
    result = parse_local_frame_params({"aspectRatio": "4:3"})
    assert result.is_valid is True
    assert result.params.aspect_ratio == "4:3"
    assert any("aspectRatio" in w for w in result.warnings)


# ─────────────────────────────────────────────
# transitionEnabled parsing
# ─────────────────────────────────────────
def test_parse_transition_enabled_true():
    """transitionEnabled=true should work."""
    result = parse_local_frame_params({"transitionEnabled": True})
    assert result.is_valid is True
    assert result.params.transition_enabled is True


def test_parse_transition_enabled_false():
    """transitionEnabled=false should work."""
    result = parse_local_frame_params({"transitionEnabled": False})
    assert result.is_valid is True
    assert result.params.transition_enabled is False


def test_parse_transition_enabled_string_true():
    """transitionEnabled="true" string should work."""
    result = parse_local_frame_params({"transitionEnabled": "true"})
    assert result.is_valid is True
    assert result.params.transition_enabled is True


def test_parse_transition_enabled_string_false():
    """transitionEnabled="false" string should work."""
    result = parse_local_frame_params({"transitionEnabled": "false"})
    assert result.is_valid is True
    assert result.params.transition_enabled is False


# ─────────────────────────────────────────────
# includeOverview / includeSummary parsing
# ─────────────────────────────────────────
def test_parse_include_overview():
    """includeOverview should parse correctly."""
    result = parse_local_frame_params({"includeOverview": False})
    assert result.is_valid is True
    assert result.params.include_overview is False


def test_parse_include_summary():
    """includeSummary should parse correctly."""
    result = parse_local_frame_params({"includeSummary": False})
    assert result.is_valid is True
    assert result.params.include_summary is False


# ─────────────────────────────────────────────
# V0.2.5.1: resolve_resolution
# ─────────────────────────────────────────
def test_resolve_resolution_9_16():
    """9:16 should resolve to 1080x1920."""
    from app.video_lab.renderers.render_params import resolve_resolution
    assert resolve_resolution("9:16") == (1080, 1920)


def test_resolve_resolution_16_9():
    """16:9 should resolve to 1920x1080."""
    from app.video_lab.renderers.render_params import resolve_resolution
    assert resolve_resolution("16:9") == (1920, 1080)


def test_resolve_resolution_1_1():
    """1:1 should resolve to 1080x1080."""
    from app.video_lab.renderers.render_params import resolve_resolution
    assert resolve_resolution("1:1") == (1080, 1080)


def test_resolve_resolution_invalid_fallback():
    """Invalid aspect ratio should fallback to 1080x1920."""
    from app.video_lab.renderers.render_params import resolve_resolution
    assert resolve_resolution("invalid") == (1080, 1920)
    assert resolve_resolution("4:3") == (1080, 1920)


# ─────────────────────────────────────────────
# V0.2.5.1: Warning messages show original illegal values
# ─────────────────────────────────────────
def test_warning_highlight_mode_shows_raw_value():
    """Warning for invalid highlightMode should show original illegal value."""
    result = parse_local_frame_params({"highlightMode": "bad_mode"})
    assert result.is_valid is True
    assert result.params.highlight_mode == "auto"
    # Warning should contain the original illegal value, not the fallback
    raw_value_warnings = [w for w in result.warnings if "bad_mode" in w]
    assert len(raw_value_warnings) > 0, f"Expected warning with 'bad_mode', got: {result.warnings}"


def test_warning_style_preset_shows_raw_value():
    """Warning for invalid stylePreset should show original illegal value."""
    result = parse_local_frame_params({"stylePreset": "fake_preset"})
    assert result.is_valid is True
    assert result.params.style_preset == "ai_frontier_dark"
    # Warning should contain the original illegal value, not the fallback
    raw_value_warnings = [w for w in result.warnings if "fake_preset" in w]
    assert len(raw_value_warnings) > 0, f"Expected warning with 'fake_preset', got: {result.warnings}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
