"""
tests/test_style_gallery_score_history.py
V0.4.4: Style Gallery 评分历史留痕（历史可分析）
"""

import json
from pathlib import Path
from unittest.mock import patch

from app.video_lab.style_gallery import score_history


# ─── 单元：append / read / summarize（tmp 隔离，不污染 runtime）────────────────

class TestScoreHistoryStore:
    def _patch_path(self, monkeypatch, tmp_path):
        p = tmp_path / "score_history.jsonl"
        monkeypatch.setattr(score_history, "_JSONL_PATH", p)
        monkeypatch.setattr(score_history, "_RECORDS_DIR", tmp_path)
        return p

    def test_append_and_read(self, monkeypatch, tmp_path):
        self._patch_path(monkeypatch, tmp_path)
        score_history.append_score({"sampleId": "s1", "route_id": "r1", "route_name": "R1", "score": 80.0})
        score_history.append_score({"sampleId": "s2", "route_id": "r1", "route_name": "R1", "score": 88.0})
        recs = score_history.read_scores()
        assert len(recs) == 2
        assert recs[0]["ts"] <= recs[1]["ts"]
        assert all("isoTime" in r for r in recs)

    def test_read_filters_by_route_and_sample(self, monkeypatch, tmp_path):
        self._patch_path(monkeypatch, tmp_path)
        score_history.append_score({"sampleId": "s1", "route_id": "r1", "score": 70.0})
        score_history.append_score({"sampleId": "s2", "route_id": "r2", "score": 60.0})
        assert len(score_history.read_scores(route_id="r1")) == 1
        assert len(score_history.read_scores(sample_id="s2")) == 1

    def test_summarize_computes_delta(self, monkeypatch, tmp_path):
        self._patch_path(monkeypatch, tmp_path)
        score_history.append_score({"sampleId": "s1", "route_id": "r1", "route_name": "R1", "score": 80.0})
        score_history.append_score({"sampleId": "s1", "route_id": "r1", "route_name": "R1", "score": 88.0})
        summ = score_history.summarize_by_route()
        assert summ["r1"]["latest"] == 88.0
        assert summ["r1"]["previous"] == 80.0
        assert summ["r1"]["delta"] == 8.0
        assert summ["r1"]["count"] == 2
        assert summ["r1"]["average"] == 84.0

    def test_read_empty_when_no_file(self, monkeypatch, tmp_path):
        self._patch_path(monkeypatch, tmp_path)
        assert score_history.read_scores() == []
        assert score_history.summarize_by_route() == {}


# ─── 端点：judge 成功后留痕 + /style-gallery/score-history 返回 ───────────────

class TestScoreHistoryEndpoint:
    def test_judge_appends_history_and_endpoint_returns(self, monkeypatch, tmp_path):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus
        from app.video_lab.style_gallery import store as sg_store

        # 隔离评分历史到 tmp
        monkeypatch.setattr(score_history, "_JSONL_PATH", tmp_path / "score_history.jsonl")
        monkeypatch.setattr(score_history, "_RECORDS_DIR", tmp_path)

        out = StyleSampleOutput(type="mp4", path="", poster="style_gallery/test/sh.jpg")
        sample = StyleSample(
            id="sample_sh1", route_id="local_frame_compose", route_name="本地帧",
            style_name="数据卡", status=SampleStatus.CANDIDATE, params={}, output=out, tags=[],
        )
        sg_store.save_sample(sample)

        runtime = Path(__file__).parent.parent / "runtime" / "style_gallery"
        poster_file = runtime / "style_gallery" / "test" / "sh.jpg"
        poster_file.parent.mkdir(parents=True, exist_ok=True)
        poster_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 100)

        def mock_success(path):
            return {"success": True, "scores": {"layout": 4.0, "readability": 4.2},
                    "overall": 4.0, "suggestions": [], "judge": "test"}

        try:
            with patch("app.video_lab.quality.visual_judge.assess_visual_quality", mock_success):
                client = TestClient(app)
                resp = client.post("/video-lab/style-samples/sample_sh1/judge")
                assert resp.status_code == 200

                # 留痕了一条
                recs = score_history.read_scores(sample_id="sample_sh1")
                assert len(recs) == 1
                assert recs[0]["score"] == 80.0
                assert recs[0]["route_id"] == "local_frame_compose"

                # 历史端点返回
                h = client.get("/video-lab/style-gallery/score-history").json()
                assert "byRoute" in h and "records" in h
                assert h["byRoute"]["local_frame_compose"]["latest"] == 80.0
        finally:
            sg_store.delete_sample("sample_sh1")
            if poster_file.exists():
                poster_file.unlink()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
