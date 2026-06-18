"""
Tests for Remotion style resolution in props_builder.

Covers:
- build_remotion_props does not raise UnboundLocalError for 'style'
- remotionFamily=data_news, card_stack, timeline_news all build valid props
- stylePreset missing does not raise
- stylePreset unknown does not raise, falls back gracefully
- remotionFamily missing falls back to data_news
- contentDebug.style is always defined (no UnboundLocalError)
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.remotion.props_builder import build_remotion_props


def _build_props(structured, key_points, params):
    """Helper: build props with mocked experiment dir."""
    with patch("app.video_lab.renderers.remotion.props_builder.get_experiment_dir") as mock_dir:
        mock_dir.return_value = MagicMock()
        mock_path = MagicMock()
        mock_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_path.open = MagicMock()
        with patch("builtins.open", mock_path.open):
            return build_remotion_props("test_exp", structured, key_points, params)


class TestStyleResolution:
    """Tests for style variable binding and remotionFamily fallback."""

    def test_no_unbound_local_error_style(self):
        """build_remotion_props must not raise UnboundLocalError for 'style'."""
        structured = {"lead": "测试新闻", "subtitle": "AI 前沿"}
        key_points = {
            "keyPoints": [
                {"title": "标题1", "body": "内容1", "source": "源1"}
            ]
        }
        params = {}
        # Must not raise
        props = _build_props(structured, key_points, params)
        assert "style" not in props or isinstance(props.get("style"), dict)

    def test_remotion_family_data_news(self):
        """remotionFamily=data_news builds valid props."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "data_news"}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") == "data_news"
        assert "contentDebug" in props
        assert "style" in props["contentDebug"]

    def test_remotion_family_card_stack(self):
        """remotionFamily=card_stack builds valid props."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "card_stack"}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") == "card_stack"
        assert "contentDebug" in props

    def test_remotion_family_timeline_news(self):
        """remotionFamily=timeline_news is preserved in props (V0.8.9)."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "timeline_news"}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") == "timeline_news"
        assert "contentDebug" in props
        assert props["contentDebug"].get("remotionFamily") == "timeline_news"

    def test_remotion_family_dashboard_brief(self):
        """remotionFamily=dashboard_brief is preserved in props."""
        structured = {"lead": "娴嬭瘯", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "dashboard_brief"}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") == "dashboard_brief"
        assert props["contentDebug"].get("remotionFamily") == "dashboard_brief"

    def test_remotion_family_caption_story(self):
        """remotionFamily=caption_story is preserved in props."""
        structured = {"lead": "娴嬭瘯", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "caption_story"}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") == "caption_story"
        assert props["contentDebug"].get("remotionFamily") == "caption_story"

    def test_family_variant_is_applied_to_style(self):
        """familyVariant should be passed through to Remotion style props."""
        structured = {"lead": "娴嬭瘯", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "dashboard_brief", "familyVariant": "chart_story"}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") == "dashboard_brief"
        assert props["style"].get("familyVariant") == "chart_story"
        assert props["contentDebug"]["style"].get("familyVariant") == "chart_story"

    def test_unknown_remotion_family_fallback_no_error(self):
        """Unknown remotionFamily is silently ignored (no exception)."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "unknown_family"}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") is None
        assert "contentDebug" in props
        assert props["contentDebug"].get("remotionFamily") == "data_news"

    def test_remotion_family_missing_fallback(self):
        """remotionFamily missing defaults to data_news in contentDebug."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {}
        props = _build_props(structured, key_points, params)
        assert props.get("remotionFamily") is None  # not set unless explicitly valid
        # contentDebug should have a fallback
        cd = props.get("contentDebug", {})
        assert cd.get("remotionFamily") == "data_news"

    def test_style_preset_missing_no_error(self):
        """stylePreset missing does not raise."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {}
        props = _build_props(structured, key_points, params)
        assert "style" not in props or isinstance(props.get("style"), dict)

    def test_style_preset_unknown_no_error(self):
        """stylePreset unknown does not raise, falls back gracefully."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"stylePreset": "nonexistent_preset_xyz"}
        # Must not raise
        props = _build_props(structured, key_points, params)
        # stylePreset is informational, unknown values are ignored
        assert "stylePreset" in props

    def test_remotion_style_dict_applied(self):
        """remotionStyle dict in params is applied to props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "accentColor": "#FF0000",
                "highlightColor": "#00FF00",
                "fontScale": 1.2,
            }
        }
        props = _build_props(structured, key_points, params)
        assert "style" in props
        assert props["style"].get("accentColor") == "#FF0000"
        assert props["style"].get("highlightColor") == "#00FF00"
        assert props["style"].get("fontScale") == 1.2

    def test_extended_transition_styles_are_applied(self):
        """V1.2.4: rich transition styles should pass through to Remotion style props."""
        structured = {"lead": "娴嬭瘯", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        for transition in ("push", "wipe", "zoom_blur", "flip", "glitch"):
            props = _build_props(structured, key_points, {"transitionStyle": transition})
            assert props["style"].get("transitionStyle") == transition

    def test_content_debug_has_style_dict(self):
        """contentDebug.style must always be a dict (not raise UnboundLocalError)."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {}
        props = _build_props(structured, key_points, params)
        cd = props.get("contentDebug", {})
        assert isinstance(cd.get("style"), dict), f"contentDebug.style should be dict, got {type(cd.get('style'))}"


class TestBackgroundPresetAndCardStackPeekFrames:
    """V1.2.1.4: Tests for backgroundPreset and cardStackPeekFrames in build_remotion_props."""

    def test_background_preset_glass_dashboard(self):
        """glass_dashboard preset is passed through to props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionFamily": "data_news",
            "remotionStyle": {
                "backgroundPreset": "glass_dashboard",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["backgroundPreset"] == "glass_dashboard"
        assert props["contentDebug"]["style"]["backgroundPreset"] == "glass_dashboard"

    def test_background_preset_aurora_blue(self):
        """aurora_blue preset is passed through to props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionFamily": "card_stack",
            "remotionStyle": {
                "backgroundPreset": "aurora_blue",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["backgroundPreset"] == "aurora_blue"

    def test_background_preset_warm_cinematic(self):
        """warm_cinematic preset is passed through to props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "backgroundPreset": "warm_cinematic",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["backgroundPreset"] == "warm_cinematic"

    def test_rich_background_presets_are_applied(self):
        """V1.2.4: richer background presets are passed through to Remotion."""
        structured = {"lead": "test", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        for background in ("neon_circuit", "deep_space"):
            props = _build_props(structured, key_points, {"backgroundPreset": background})
            assert props["style"]["backgroundPreset"] == background

    def test_background_preset_invalid_value_not_passed(self):
        """Invalid backgroundPreset values are silently ignored."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "backgroundPreset": "bad_invalid_value",
            },
        }
        props = _build_props(structured, key_points, params)
        assert "backgroundPreset" not in props.get("style", {})

    def test_background_preset_from_top_level_params(self):
        """backgroundPreset from top-level params (not remotionStyle dict) is also accepted."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "backgroundPreset": "glass_dashboard",
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["backgroundPreset"] == "glass_dashboard"

    def test_card_stack_peek_frames_valid(self):
        """cardStackPeekFrames is passed through to props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionFamily": "card_stack",
            "remotionStyle": {
                "cardStackPeekFrames": 18,
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["cardStackPeekFrames"] == 18

    def test_card_stack_peek_frames_clamped_to_45(self):
        """cardStackPeekFrames values > 45 are clamped to 45."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "cardStackPeekFrames": 999,
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["cardStackPeekFrames"] == 45

    def test_card_stack_peek_frames_clamped_negative_to_zero(self):
        """cardStackPeekFrames negative values are clamped to 0."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "cardStackPeekFrames": -5,
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["cardStackPeekFrames"] == 0

    def test_card_stack_peek_frames_from_top_level_params(self):
        """cardStackPeekFrames from top-level params is also accepted."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "cardStackPeekFrames": 22,
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["cardStackPeekFrames"] == 22

    def test_background_preset_and_card_stack_peek_frames_together(self):
        """backgroundPreset and cardStackPeekFrames can be set simultaneously."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionFamily": "card_stack",
            "remotionStyle": {
                "backgroundPreset": "aurora_blue",
                "cardStackPeekFrames": 18,
                "accentColor": "#8b5cf6",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["backgroundPreset"] == "aurora_blue"
        assert props["style"]["cardStackPeekFrames"] == 18
        assert props["style"]["accentColor"] == "#8b5cf6"
        assert props["remotionFamily"] == "card_stack"


class TestVisualStylePresetInProps:
    """V1.2.3: Tests that visualStylePreset is correctly passed through build_remotion_props."""

    def test_visual_style_preset_light_editorial_from_remotion_style(self):
        """visualStylePreset=light_editorial from remotionStyle dict ends up in props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "visualStylePreset": "light_editorial",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["visualStylePreset"] == "light_editorial"
        assert props["contentDebug"]["style"]["visualStylePreset"] == "light_editorial"

    def test_visual_style_preset_warm_paper_from_remotion_style(self):
        """visualStylePreset=warm_paper from remotionStyle dict ends up in props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "visualStylePreset": "warm_paper",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["visualStylePreset"] == "warm_paper"

    def test_visual_style_preset_bold_magazine_from_remotion_style(self):
        """visualStylePreset=bold_magazine from remotionStyle dict ends up in props.style."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "visualStylePreset": "bold_magazine",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["visualStylePreset"] == "bold_magazine"

    def test_visual_style_preset_from_top_level_params(self):
        """visualStylePreset from top-level params (not remotionStyle dict) is also accepted."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "visualStylePreset": "light_editorial",
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["visualStylePreset"] == "light_editorial"

    def test_visual_style_preset_unknown_value_ignored(self):
        """Unknown visualStylePreset values are silently ignored (not written to style)."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "visualStylePreset": "not_a_real_preset",
            },
        }
        props = _build_props(structured, key_points, params)
        assert "visualStylePreset" not in props.get("style", {})

    def test_visual_style_preset_and_background_preset_together(self):
        """visualStylePreset and backgroundPreset can be set simultaneously."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {
            "remotionStyle": {
                "visualStylePreset": "bold_magazine",
                "backgroundPreset": "glass_dashboard",
            },
        }
        props = _build_props(structured, key_points, params)
        assert props["style"]["visualStylePreset"] == "bold_magazine"
        assert props["style"]["backgroundPreset"] == "glass_dashboard"
