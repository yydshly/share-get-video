"""
tests/test_style_gallery_presets.py
V0.4.6: 每条路线多个预置风格（覆盖参数空间 / 能力边界）
"""

from collections import Counter

from app.video_lab.style_gallery.presets import list_preset_styles

REQUIRED_FIELDS = {"route_id", "route_name", "style_id", "style_name", "description", "capabilities", "tags", "params"}
KNOWN_ROUTES = {"local_frame_compose", "template_programmatic_render", "ai_asset_then_compose"}


def test_each_route_has_at_least_three_presets():
    presets = list_preset_styles()
    by_route = Counter(p["route_id"] for p in presets)
    for route in KNOWN_ROUTES:
        assert by_route[route] >= 3, f"{route} 仅 {by_route[route]} 个预置，应 >= 3"


def test_all_required_fields_present():
    for p in list_preset_styles():
        missing = REQUIRED_FIELDS - set(p.keys())
        assert not missing, f"{p.get('style_id')} 缺字段: {missing}"
        assert isinstance(p["params"], dict) and p["params"], f"{p['style_id']} params 不应为空"


def test_style_ids_unique():
    ids = [p["style_id"] for p in list_preset_styles()]
    dupes = [i for i, c in Counter(ids).items() if c > 1]
    assert not dupes, f"重复 style_id: {dupes}"


def test_routes_are_known():
    for p in list_preset_styles():
        assert p["route_id"] in KNOWN_ROUTES, f"未知 route_id: {p['route_id']}"


def test_remotion_family_values_are_supported():
    """remotionFamily 只能用真实支持的值（props_builder + AiNewsVideo.tsx 都已实现）。"""
    supported = {"data_news", "card_stack", "timeline_news", "dashboard_brief", "caption_story"}
    for p in list_preset_styles():
        fam = p["params"].get("remotionFamily")
        if fam is not None:
            assert fam in supported, f"{p['style_id']} 用了未实现的 remotionFamily: {fam}"


def test_card_stack_paradigm_is_offered():
    """应有至少一个 Remotion 样式用 card_stack 范式（与默认 data_news 形成版式差异）。"""
    fams = {p["params"].get("remotionFamily") for p in list_preset_styles()}
    assert "card_stack" in fams


def test_all_style_family_paradigms_are_offered():
    """Remotion family research page should map to real preset values."""
    fams = {p["params"].get("remotionFamily") for p in list_preset_styles()}
    assert {"card_stack", "timeline_news", "dashboard_brief", "caption_story"}.issubset(fams)


def test_remotion_style_family_variants_are_offered():
    """Landable style-family variants should have real Style Gallery presets."""
    ids = {p["style_id"] for p in list_preset_styles()}
    assert {
        "remotion_chart_story",
        "remotion_ranking_strip",
        "remotion_timeline_route_map",
        "remotion_caption_intro",
        "remotion_cta_overlay",
    }.issubset(ids)


def test_expanded_style_coverage():
    """扩充后各路线样式数（覆盖更大风格跨度）。"""
    by_route = Counter(p["route_id"] for p in list_preset_styles())
    assert by_route["local_frame_compose"] >= 5
    assert by_route["template_programmatic_render"] >= 14
    assert by_route["ai_asset_then_compose"] >= 5


def test_endpoint_returns_presets():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.get("/video-lab/style-gallery/preset-styles")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == len(list_preset_styles())
    assert len(data) >= 14


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
