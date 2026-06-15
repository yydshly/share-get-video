"""
tests/test_remotion_url_path.py
RemotionVisualRenderer._url_to_path 应基于 config 的 RUNTIME_DIR 还原路径，
而非写死相对 "runtime/"（修复换目录/自定义 RUNTIME_DIR 下算错路径的问题）。
"""

from pathlib import Path

from app.video_lab.renderers.visual.remotion_renderer import RemotionVisualRenderer
from app.video_lab import config


def test_empty_returns_empty():
    assert RemotionVisualRenderer._url_to_path("") == ""
    assert RemotionVisualRenderer._url_to_path(None) == ""  # type: ignore[arg-type]


def test_runtime_url_resolves_under_runtime_dir():
    out = RemotionVisualRenderer._url_to_path("/runtime/video_lab/experiments/e/clip.mp4")
    # 落在 config.RUNTIME_DIR 下，且保留子路径
    assert Path(out) == config.RUNTIME_DIR / "video_lab/experiments/e/clip.mp4"
    assert out.endswith("clip.mp4")


def test_historical_runtime_prefix_still_resolves():
    """委托 path_contract 后，历史 /runtime/ 前缀仍能落到当前 RUNTIME_DIR 下。"""
    out = RemotionVisualRenderer._url_to_path("/runtime/video_lab/y.mp4")
    assert Path(out) == config.RUNTIME_DIR / "video_lab/y.mp4"


def test_bare_relative_resolves_under_runtime_dir():
    """裸相对路径也落到 RUNTIME_DIR 下（path_contract 统一契约）。"""
    out = RemotionVisualRenderer._url_to_path("video_lab/experiments/e/clip.mp4")
    assert Path(out) == config.RUNTIME_DIR / "video_lab/experiments/e/clip.mp4"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
