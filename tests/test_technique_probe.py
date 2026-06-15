"""
tests/test_technique_probe.py
Loop2: 最佳技术探测编排 —— 多路线各出片→按质量分排名→推荐。
用桩 compose_fn，不触发任何真实渲染。
"""

from app.video_lab.technique_probe import (
    rank_probe_results,
    run_technique_probe,
    DEFAULT_PROBE_ROUTES,
)


def _r(route, status="succeeded", score=None, **extra):
    d = {"visualRoute": route, "status": status, "quality": {}}
    if score is not None:
        d["quality"] = {"overallScore": score}
    d.update(extra)
    return d


def test_rank_orders_by_score_desc():
    results = [
        _r("a", score=70),
        _r("b", score=90),
        _r("c", score=80),
    ]
    ranking = rank_probe_results(results)
    assert [x["visualRoute"] for x in ranking] == ["b", "c", "a"]
    assert [x["rank"] for x in ranking] == [1, 2, 3]
    assert ranking[0]["score"] == 90


def test_failed_routes_sink_to_bottom_with_null_score():
    results = [
        _r("ok", score=60),
        _r("bad", status="failed", failedReason="boom"),
    ]
    ranking = rank_probe_results(results)
    assert ranking[0]["visualRoute"] == "ok"
    assert ranking[1]["visualRoute"] == "bad"
    assert ranking[1]["score"] is None
    assert ranking[1]["failedReason"] == "boom"


def test_run_probe_aggregates_and_recommends_top():
    canned = {
        "local_frame_compose": _r("local_frame_compose", score=75, finalVideoUrl="/u/a.mp4"),
        "template_programmatic_render": _r("template_programmatic_render", score=88, finalVideoUrl="/u/b.mp4"),
        "ai_asset_then_compose": _r("ai_asset_then_compose", status="failed", failedReason="no key"),
    }

    def fake_compose(content, route, params):
        return canned[route]

    out = run_technique_probe("内容", None, {}, fake_compose)
    assert out["routesRun"] == DEFAULT_PROBE_ROUTES
    assert out["recommendedRoute"] == "template_programmatic_render"
    assert out["recommendedDisplayName"]  # 有中文展示名
    assert out["succeededCount"] == 2
    assert out["totalCount"] == 3
    assert out["ranking"][0]["rank"] == 1


def test_run_probe_isolates_per_route_exception():
    """单条路线抛异常不应中断整体探测，其它路线照常排名。"""
    def flaky_compose(content, route, params):
        if route == "template_programmatic_render":
            raise RuntimeError("render crashed")
        return _r(route, score=50)

    out = run_technique_probe("内容", None, {}, flaky_compose)
    assert out["totalCount"] == 3
    crashed = [r for r in out["results"] if r["visualRoute"] == "template_programmatic_render"][0]
    assert crashed["status"] == "failed"
    assert "render crashed" in crashed["failedReason"]
    # 另两条成功的仍参与排名并产生推荐
    assert out["recommendedRoute"] in ("local_frame_compose", "ai_asset_then_compose")


def test_visual_score_breaks_structural_tie():
    """结构分几乎打平时，视觉分(0-5)应拉开差距并可改变名次。"""
    results = [
        {"visualRoute": "a", "status": "succeeded", "quality": {"overallScore": 5.0}, "visualScore": 3.0},
        {"visualRoute": "b", "status": "succeeded", "quality": {"overallScore": 4.8}, "visualScore": 4.8},
    ]
    ranking = rank_probe_results(results)
    # a: 0.5*100+0.5*60=80 ; b: 0.5*96+0.5*96=96 → b 胜出（视觉翻盘）
    assert ranking[0]["visualRoute"] == "b"
    assert ranking[0]["combinedScore"] == 96.0
    assert ranking[0]["visualScore"] == 4.8
    # 结构分(0-5)仍保留给 UI
    assert ranking[1]["score"] == 5.0


def test_combined_falls_back_to_structural_without_visual():
    """没有视觉分时综合分=结构分×20，仍可排名。"""
    results = [{"visualRoute": "a", "status": "succeeded", "quality": {"overallScore": 4.0}}]
    ranking = rank_probe_results(results)
    assert ranking[0]["combinedScore"] == 80.0
    assert ranking[0]["visualScore"] is None


def test_judge_fn_attaches_visual_score_and_affects_recommendation():
    base = {
        "local_frame_compose": {"visualRoute": "local_frame_compose", "status": "succeeded", "quality": {"overallScore": 5.0}},
        "template_programmatic_render": {"visualRoute": "template_programmatic_render", "status": "succeeded", "quality": {"overallScore": 4.8}},
        "ai_asset_then_compose": {"visualRoute": "ai_asset_then_compose", "status": "succeeded", "quality": {"overallScore": 5.0}},
    }

    def fake_compose(content, route, params):
        return dict(base[route])

    # 让 Remotion 视觉分(0-5)最高 → 应被推荐，尽管结构分略低
    visual_by_route = {
        "local_frame_compose": 2.5,
        "template_programmatic_render": 4.9,
        "ai_asset_then_compose": 2.8,
    }

    def fake_judge(result):
        return {"visualScore": visual_by_route[result["visualRoute"]], "visualDimensions": {}}

    out = run_technique_probe("内容", None, {}, fake_compose, judge_fn=fake_judge)
    assert out["recommendedRoute"] == "template_programmatic_render"
    assert out["ranking"][0]["visualScore"] == 4.9


def test_run_probe_respects_explicit_routes():
    def fake_compose(content, route, params):
        return _r(route, score=10)

    out = run_technique_probe("内容", ["local_frame_compose"], {}, fake_compose)
    assert out["routesRun"] == ["local_frame_compose"]
    assert out["totalCount"] == 1


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
