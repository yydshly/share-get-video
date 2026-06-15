"""
tests/test_style_sweep.py
样式对比编排 —— 同一路线每个预置样式各出一片。用桩 render_fn，不触发真实渲染。
"""

from app.video_lab.style_sweep import styles_for_route, run_style_sweep

FAKE_STYLES = [
    {"route_id": "r1", "route_name": "路线一", "style_id": "s1", "style_name": "样式甲",
     "description": "d1", "tags": ["a"], "params": {"foo": 1}},
    {"route_id": "r1", "route_name": "路线一", "style_id": "s2", "style_name": "样式乙",
     "description": "d2", "tags": ["b"], "params": {"foo": 2}},
    {"route_id": "r2", "route_name": "路线二", "style_id": "s3", "style_name": "样式丙",
     "params": {"foo": 3}},
]


def test_styles_for_route_filters_by_route():
    out = styles_for_route("r1", FAKE_STYLES)
    assert [s["style_id"] for s in out] == ["s1", "s2"]


def test_sweep_renders_each_style_with_merged_params():
    seen = []

    def fake_render(content, route, params):
        seen.append((route, params.get("foo"), params.get("targetDuration")))
        return {"visualRoute": route, "status": "succeeded", "finalVideoUrl": f"/u/{params.get('foo')}.mp4", "quality": {"overallScore": 5}}

    out = run_style_sweep("内容", "r1", {"targetDuration": 45}, fake_render, styles=FAKE_STYLES)
    assert out["routeId"] == "r1"
    assert out["routeName"] == "路线一"
    assert out["styleCount"] == 2
    assert out["succeededCount"] == 2
    # 样式参数覆盖在传入参数之上，且基础参数保留
    assert (("r1", 1, 45) in seen) and (("r1", 2, 45) in seen)
    # 每个样式条目带 styleId/styleName + 渲染结果
    ids = {r["styleId"] for r in out["results"]}
    assert ids == {"s1", "s2"}
    assert out["results"][0]["result"]["finalVideoUrl"].endswith(".mp4")


def test_sweep_isolates_per_style_exception():
    def flaky_render(content, route, params):
        if params.get("foo") == 2:
            raise RuntimeError("render crashed")
        return {"visualRoute": route, "status": "succeeded", "quality": {}}

    out = run_style_sweep("内容", "r1", {}, flaky_render, styles=FAKE_STYLES)
    assert out["styleCount"] == 2
    assert out["succeededCount"] == 1
    bad = [r for r in out["results"] if r["styleId"] == "s2"][0]
    assert bad["result"]["status"] == "failed"
    assert "render crashed" in bad["result"]["failedReason"]


def test_sweep_unknown_route_returns_empty():
    def fake_render(content, route, params):
        return {"status": "succeeded"}

    out = run_style_sweep("内容", "nope", {}, fake_render, styles=FAKE_STYLES)
    assert out["styleCount"] == 0
    assert out["results"] == []
    assert out["routeName"] == "nope"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
