"""
tests/test_route_recommendation.py
数据驱动的最佳路线推荐：从真实累计评分算出，而非写死；无数据时如实说明。
"""

from app.video_lab.route_recommendation import recommend_route_from_summary


def _kind(latest, count):
    return {"latest": latest, "count": count}


def test_empty_summary_is_honest_not_fabricated():
    out = recommend_route_from_summary({})
    assert out["dataDriven"] is False
    assert out["recommendedRoute"] is None
    assert out["ranking"] == []
    assert "暂无评分数据" in out["reason"]


def test_recommends_highest_combined_score():
    summary = {
        "local_frame_compose": {"structural": _kind(5.0, 5), "perceptual": _kind(3.0, 5)},   # (100+60)/2=80
        "template_programmatic_render": {"structural": _kind(4.8, 5), "perceptual": _kind(4.8, 5)},  # (96+96)/2=96
    }
    out = recommend_route_from_summary(summary)
    assert out["dataDriven"] is True
    assert out["recommendedRoute"] == "template_programmatic_render"
    assert out["ranking"][0]["score"] == 96.0
    assert out["confident"] is True
    assert "基于真实评分" in out["reason"]


def test_single_kind_still_ranks():
    """只有结构分也能排（视觉分缺失不致命）。"""
    summary = {"ai_asset_then_compose": {"structural": _kind(4.0, 4)}}
    out = recommend_route_from_summary(summary)
    assert out["recommendedRoute"] == "ai_asset_then_compose"
    assert out["ranking"][0]["score"] == 80.0


def test_low_samples_marked_not_confident():
    summary = {"local_frame_compose": {"structural": _kind(5.0, 1)}}
    out = recommend_route_from_summary(summary)
    assert out["dataDriven"] is True
    assert out["confident"] is False
    assert "待更多数据" in out["reason"]


def test_route_with_no_scores_skipped():
    summary = {
        "a": {"structural": {"latest": None, "count": 2}},   # 无有效分 → 跳过
        "b": {"structural": _kind(4.0, 3)},
    }
    out = recommend_route_from_summary(summary)
    assert [r["route"] for r in out["ranking"]] == ["b"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
