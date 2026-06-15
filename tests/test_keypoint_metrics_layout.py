"""
tests/test_keypoint_metrics_layout.py
V0.5.1: 数据图作为整体块的一部分紧跟正文，不再钉死在卡片底部（消除中间大空隙）
"""

from app.video_lab.renderers import frame_templates as ft


def _capture_metrics_y(tmp_path, monkeypatch, content_align="top"):
    captured = {}

    def spy(draw, metrics, x, y, w, scale, **kw):
        captured["y"] = y

    monkeypatch.setattr(ft, "_draw_metrics_card", spy)
    ft.render_keypoint_template(
        index=1, total=6, category="", title="短标题", body="一句简短的正文内容。",
        source="", frames_dir=tmp_path, resolution=(1080, 1920),
        metrics=[{"label": "提升", "value": 39, "unit": "%"}],
        content_align=content_align,
    )
    return captured["y"]


def test_metrics_follows_text_not_pinned_to_bottom(tmp_path, monkeypatch):
    """top 对齐 + 短文：数据图应紧跟正文（靠上），而非钉在卡片底部。"""
    y = _capture_metrics_y(tmp_path, monkeypatch, content_align="top")
    # 旧行为：钉底 metrics_card_y = content_bottom(1710) - reserve(230) = 1480
    assert y < 1480, f"数据图应紧跟正文，不应钉底，得到 y={y}"


def test_metrics_block_centered_when_center(tmp_path, monkeypatch):
    """center 对齐：整块（标题+正文+数据图）居中，数据图位置比 top 时更靠下。"""
    y_top = _capture_metrics_y(tmp_path, monkeypatch, content_align="top")
    y_center = _capture_metrics_y(tmp_path, monkeypatch, content_align="center")
    assert y_center > y_top, "居中时数据图应整体下移（块居中）"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
