"""
tests/test_overview_background.py
概览页(overview)支持 AI 背景：AI 素材路线下概览页应与封面观感一致（用 AI 背景而非渐变）。
"""

from unittest.mock import patch

from PIL import Image

from app.video_lab.renderers import frame_templates as ft


def _blank(w=1080, h=1920):
    return Image.new("RGB", (w, h), (10, 14, 26))


def _items():
    return [{"index": "1", "title": "要点一"}, {"index": "2", "title": "要点二"}]


def test_overview_uses_ai_background_when_provided(tmp_path):
    with patch.object(ft, "load_background_image", return_value=_blank()) as m_bg, \
         patch.object(ft, "render_gradient_background", return_value=_blank()) as m_grad:
        r = ft.render_overview_template(_items(), tmp_path, background_path="x/bg.png")
    assert r.get("path")
    m_bg.assert_called_once()           # 用了 AI 背景
    m_grad.assert_not_called()          # 没回退渐变


def test_overview_falls_back_to_gradient_without_background(tmp_path):
    with patch.object(ft, "load_background_image", return_value=_blank()) as m_bg, \
         patch.object(ft, "render_gradient_background", return_value=_blank()) as m_grad:
        r = ft.render_overview_template(_items(), tmp_path)
    assert r.get("path")
    m_grad.assert_called_once()         # 无背景 → 渐变
    m_bg.assert_not_called()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
