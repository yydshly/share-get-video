"""
tests/test_style_gallery_route_fit.py
V0.4.9: 每条路线"最适合风格"判定（宏观目标①）
"""

from datetime import datetime

from app.video_lab.style_gallery import store as sg_store
from app.video_lab.style_gallery.models import (
    StyleSample, StyleSampleOutput, SampleStatus, VisualJudgement,
)


def _sample(sid: str, route_id: str, style_name: str, score: float | None) -> StyleSample:
    vj = None
    if score is not None:
        vj = VisualJudgement(
            score=score, grade="good" if score >= 70 else "ok",
            summary="", judged_at="2026-06-15T10:00:00", dimensions={"layout": 4.0},
        )
    return StyleSample(
        id=sid, route_id=route_id, route_name="测试路线", style_name=style_name,
        status=SampleStatus.CANDIDATE, params={}, output=StyleSampleOutput(type="mp4", path="x.mp4"),
        tags=[], visual_judgement=vj, created_at=datetime.utcnow(),
    )


def test_route_fit_picks_highest_score():
    """同一路线下，best 应是最高分样片；avgScore 为已评分样片均值。"""
    from fastapi.testclient import TestClient
    from app.main import app

    route = "test_route_fit_xyz"  # 独立 route_id，避免与真实数据冲突
    sg_store.save_sample(_sample("rf_low", route, "低分风格", 60.0))
    sg_store.save_sample(_sample("rf_high", route, "高分风格", 85.0))
    sg_store.save_sample(_sample("rf_unscored", route, "未评分风格", None))
    try:
        client = TestClient(app)
        resp = client.get("/video-lab/style-gallery/route-fit")
        assert resp.status_code == 200
        data = resp.json()
        assert route in data
        r = data[route]
        assert r["sampleCount"] == 3
        assert r["scoredCount"] == 2
        assert r["avgScore"] == 72.5  # (60 + 85) / 2
        assert r["best"]["sampleId"] == "rf_high"
        assert r["best"]["styleName"] == "高分风格"
        assert r["best"]["score"] == 85.0
    finally:
        for sid in ("rf_low", "rf_high", "rf_unscored"):
            sg_store.delete_sample(sid)


def test_route_fit_best_none_when_unscored():
    """全部未评分时 best 为 None。"""
    from fastapi.testclient import TestClient
    from app.main import app

    route = "test_route_fit_unscored_only"
    sg_store.save_sample(_sample("rfu_1", route, "风格1", None))
    try:
        client = TestClient(app)
        data = client.get("/video-lab/style-gallery/route-fit").json()
        assert data[route]["best"] is None
        assert data[route]["scoredCount"] == 0
        assert data[route]["avgScore"] is None
    finally:
        sg_store.delete_sample("rfu_1")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
