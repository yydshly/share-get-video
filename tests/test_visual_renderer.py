"""
Tests for the pluggable VisualRenderer layer.

验证：
- registry 注册了 Pillow / Remotion 两条视觉路线
- resolve_visual_route 的参数解析与回退逻辑
- list_visual_renderers 返回可用性
- tts_subtitle_compose 通过 visualRoute 参数选择渲染器（解耦验证）
"""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.visual import (
    get_visual_renderer,
    list_visual_renderers,
    resolve_visual_route,
    DEFAULT_VISUAL_ROUTE,
    VisualRenderRequest,
    VisualRenderResult,
)


def test_registry_contains_all_routes():
    assert get_visual_renderer("local_frame_compose") is not None
    assert get_visual_renderer("template_programmatic_render") is not None
    assert get_visual_renderer("ai_asset_then_compose") is not None


def test_ai_asset_renderer_metadata():
    r = get_visual_renderer("ai_asset_then_compose")
    assert r.route_id == "ai_asset_then_compose"
    assert r.display_name
    # is_available 返回 (bool, str)，不抛异常
    ok, msg = r.is_available()
    assert isinstance(ok, bool) and isinstance(msg, str)


def test_image_client_not_configured_returns_error():
    from app.video_lab.providers.minimax import MiniMaxImageClient
    client = MiniMaxImageClient(api_key="")
    assert client.is_configured() is False
    res = client.generate("x", "ignored.png")
    assert res["success"] is False
    assert "MINIMAX_API_KEY" in res["providerMessage"]


def test_registry_unknown_route_returns_none():
    assert get_visual_renderer("does_not_exist") is None


def test_default_visual_route_is_pillow():
    assert DEFAULT_VISUAL_ROUTE == "local_frame_compose"


def test_resolve_visual_route_defaults_and_fallbacks():
    assert resolve_visual_route(None) == DEFAULT_VISUAL_ROUTE
    assert resolve_visual_route({}) == DEFAULT_VISUAL_ROUTE
    # unknown route falls back to default
    assert resolve_visual_route({"visualRoute": "bogus"}) == DEFAULT_VISUAL_ROUTE
    # known route is honored
    assert resolve_visual_route({"visualRoute": "template_programmatic_render"}) == "template_programmatic_render"
    # snake_case alias supported
    assert resolve_visual_route({"visual_route": "template_programmatic_render"}) == "template_programmatic_render"


def test_list_visual_renderers_shape():
    items = list_visual_renderers()
    route_ids = {it["routeId"] for it in items}
    assert "local_frame_compose" in route_ids
    assert "template_programmatic_render" in route_ids
    for it in items:
        assert "displayName" in it
        assert "available" in it
        assert "availabilityMessage" in it


def test_renderer_exposes_route_id_and_name():
    r = get_visual_renderer("local_frame_compose")
    assert r.route_id == "local_frame_compose"
    assert r.display_name


def test_tts_subtitle_compose_selects_visual_route():
    """The adapter must route step-7 through the selected VisualRenderer."""
    from app.video_lab.adapters import tts_subtitle_compose as mod

    captured = {}

    class _FakeRenderer:
        def render(self, request: VisualRenderRequest) -> VisualRenderResult:
            captured["route"] = request.params.get("visualRoute")
            return VisualRenderResult(
                success=True,
                route_id="template_programmatic_render",
                silent_video_path="runtime/x/silent.mp4",
                silent_video_url="/runtime/x/silent.mp4",
                frame_count=3,
                total_duration_sec=12.0,
            )

    # Make the adapter resolve to our fake renderer regardless of route
    with patch.object(mod, "resolve_visual_route", return_value="template_programmatic_render"):
        with patch.object(mod, "get_visual_renderer", return_value=_FakeRenderer()):
            with patch.object(mod, "MiniMaxTTSClient") as tts_cls:
                tts = tts_cls.return_value
                tts.is_configured.return_value = True
                tts.generate.return_value = {
                    "success": True,
                    "audioPath": "runtime/x/audio/voiceover.mp3",
                    "durationSec": 12,
                    "providerMessage": "ok",
                }
                # Stop after subtitle/av compose by faking ffmpeg av compose success
                with patch.object(mod, "check_ffmpeg_available", return_value=True):
                    with patch.object(mod, "compose_av_with_subtitles", return_value={"success": True, "subtitle_renderer": "ass", "subtitle_style": {}}):
                        result = mod.run_tts_subtitle_compose(
                            experiment_id="test_vr_select",
                            test_case_id="case_ai_frontier_daily_001",
                            input_payload={"content": "第一条。 依据：A。 第二条。 依据：B。 第三条。 依据：C。"},
                            params={"visualRoute": "template_programmatic_render"},
                        )

    assert captured.get("route") == "template_programmatic_render"
    assert result.rawOutput.get("status") == "succeeded"


# ─────────────────────────────────────────
# V0.3.6-b2: Pillow emphasisTerms rendering
# ─────────────────────────────────────────
def test_pillow_keypoint_template_accepts_emphasis_terms():
    """render_keypoint_template should accept emphasis_terms param without error."""
    import tempfile
    from pathlib import Path
    from app.video_lab.renderers.frame_templates import render_keypoint_template

    with tempfile.TemporaryDirectory() as tmpdir:
        frames_dir = Path(tmpdir)
        result = render_keypoint_template(
            index=1,
            total=3,
            category="",
            title="ProReviewer breakthrough 39%",
            body="Error rate drops from 88.9% to 16%",
            source="",
            frames_dir=frames_dir,
            emphasis_terms=["ProReviewer", "39%", "88.9%", "16%"],
        )
    # Verify result structure (image may not save in all test environments)
    assert "path" in result
    assert "highlights" in result
    assert result["highlights"] == ["ProReviewer", "39%", "88.9%", "16%"]
    assert result["template"] == "keypoint"
    # Verify frame was saved or at least path is valid
    assert str(result["path"]).endswith("frame_001.png")


def test_pillow_keypoint_highlights_priority_over_auto():
    """When emphasisTerms provided, result.highlights should come from them (not auto-extract)."""
    import tempfile
    from pathlib import Path
    from app.video_lab.renderers.frame_templates import render_keypoint_template

    with tempfile.TemporaryDirectory() as tmpdir:
        result = render_keypoint_template(
            index=1,
            total=1,
            category="",
            title="研究突破",
            body="数字在此88.9%",
            source="",
            frames_dir=Path(tmpdir),
            emphasis_terms=["自定义词", "突出显示"],
        )
    # highlights should be the explicit emphasisTerms
    assert result["highlights"] == ["自定义词", "突出显示"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
