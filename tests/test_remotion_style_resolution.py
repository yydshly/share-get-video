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
        """remotionFamily=timeline_news builds valid props (V0.8.9)."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {"remotionFamily": "timeline_news"}
        props = _build_props(structured, key_points, params)
        # timeline_news is not in the allowlist so remotionFamily key should not be set
        assert "remotionFamily" not in props or props.get("remotionFamily") in (
            "data_news",
            "card_stack",
        )
        assert "contentDebug" in props

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

    def test_content_debug_has_style_dict(self):
        """contentDebug.style must always be a dict (not raise UnboundLocalError)."""
        structured = {"lead": "测试", "subtitle": "AI"}
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        params = {}
        props = _build_props(structured, key_points, params)
        cd = props.get("contentDebug", {})
        assert isinstance(cd.get("style"), dict), f"contentDebug.style should be dict, got {type(cd.get('style'))}"
