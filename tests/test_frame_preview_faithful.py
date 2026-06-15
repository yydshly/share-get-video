"""
tests/test_frame_preview_faithful.py
V0.5.0: 快速预览忠实还原真实出片（应用 themeAdaptive 的 tone 配色/图标 + showDataViz 的数据图）
"""

from unittest.mock import patch

from app.video_lab.renderers import frame_preview


def _capture_kwargs(shot, params):
    """渲染单帧并捕获传给 render_keypoint_template 的关键 kwargs。"""
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        return {"path": "runtime/style_gallery/test/_f.png", "frame_name": "_f.png", "warnings": []}

    with patch.object(frame_preview, "render_keypoint_template", side_effect=fake_render):
        frame_preview.render_single_frame("local_frame_compose", "keypoint", shot, "", params)
    return captured


def test_preview_applies_metrics_when_show_data_viz():
    shot = {"headline": "购物AI落后", "display": "主流模型通过率仅57-77%，暴露短板。", "emphasisTerms": ["57-77%"]}
    kw = _capture_kwargs(shot, {"showDataViz": True, "themeAdaptive": True})
    assert kw.get("metrics"), "showDataViz 时应提取并传入 metrics"
    # 区间 57-77% 应被解析
    vals = {m.get("unit") for m in kw["metrics"]}
    assert "%" in vals


def test_preview_no_metrics_when_disabled():
    shot = {"headline": "购物AI落后", "display": "通过率仅57-77%。", "emphasisTerms": []}
    kw = _capture_kwargs(shot, {"showDataViz": False, "themeAdaptive": True})
    assert kw.get("metrics") is None


def test_preview_applies_tone_icon_and_highlight():
    """负面语义 → tone 自动给环形图标 + 琥珀高亮（与真实出片一致）。"""
    shot = {"headline": "购物AI落后短板", "display": "通过率低，暴露推理短板。", "emphasisTerms": []}
    kw = _capture_kwargs(shot, {"themeAdaptive": True})
    assert kw.get("icon") == "ring", f"negative tone 应为 ring，得到 {kw.get('icon')}"
    assert kw.get("highlight_color") is not None


def test_preview_explicit_style_overrides_tone():
    """显式 icon/highlightColor 优先于 tone。"""
    shot = {"headline": "购物AI落后", "display": "短板。", "emphasisTerms": []}
    kw = _capture_kwargs(shot, {"themeAdaptive": True, "icon": "bars", "highlightColor": "#123456"})
    assert kw.get("icon") == "bars"
    assert kw.get("highlight_color") == (0x12, 0x34, 0x56)


def test_preview_theme_adaptive_off_no_auto_icon():
    shot = {"headline": "购物AI落后", "display": "短板。", "emphasisTerms": []}
    kw = _capture_kwargs(shot, {"themeAdaptive": False})
    assert not kw.get("icon")


def test_summary_frame_preview_renders():
    """V0.5.3: 总结页预览可渲染（含 conclusions + cta）。"""
    r = frame_preview.render_single_frame(
        "local_frame_compose", "summary", {"headline": "今日回顾"}, "",
        {"conclusions": ["要点一39%", "要点二57-77%", "要点三"], "cta": "分享模板"},
    )
    assert r.get("success") is True
    assert r.get("imageUrl", "").endswith("summary.png")


def test_summary_accepts_newline_string_conclusions():
    r = frame_preview.render_single_frame(
        "local_frame_compose", "summary", {"headline": "回顾"}, "",
        {"conclusions": "第一条\n第二条\n第三条"},
    )
    assert r.get("success") is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
