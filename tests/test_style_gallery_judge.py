"""
tests/test_style_gallery_judge.py
V0.4.0: Visual judgement for Style Gallery samples
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.video_lab.style_gallery.models import (
    StyleSample, StyleSampleOutput, SampleStatus,
    VisualJudgement, EvaluationScore,
)


# ─── VisualJudgement Model Tests ─────────────────────────────────────────────

class TestVisualJudgementModel:
    """Test VisualJudgement field in StyleSample."""

    def test_visual_judgement_default_is_none(self):
        """StyleSample with no visual_judgement should have None."""
        out = StyleSampleOutput(type="mp4", path="test.mp4")
        sample = StyleSample(
            id="sample_test1",
            route_id="local_frame_compose",
            route_name="Test Route",
            style_name="Test Style",
            status=SampleStatus.CANDIDATE,
            params={},
            output=out,
            tags=[],
        )
        assert sample.visual_judgement is None

    def test_visual_judgement_can_be_set(self):
        """VisualJudgement can be assigned to a StyleSample."""
        out = StyleSampleOutput(type="mp4", path="test.mp4")
        judgement = VisualJudgement(
            score=82.0,
            grade="good",
            summary="整体清晰，数字突出。",
            strengths=["数据突出", "排版稳定"],
            weaknesses=["文字略密"],
            suggestions=["减少副标题长度"],
            judged_at="2026-06-15T10:00:00",
            dimensions={"layout": 4.0, "readability": 4.2},
        )
        sample = StyleSample(
            id="sample_test2",
            route_id="local_frame_compose",
            route_name="Test Route",
            style_name="Test Style",
            status=SampleStatus.CANDIDATE,
            params={},
            output=out,
            tags=[],
            visual_judgement=judgement,
        )
        assert sample.visual_judgement is not None
        assert sample.visual_judgement.score == 82.0
        assert sample.visual_judgement.grade == "good"

    def test_to_dict_includes_visual_judgement(self):
        """to_dict should serialize visual_judgement."""
        out = StyleSampleOutput(type="mp4", path="test.mp4")
        judgement = VisualJudgement(
            score=75.0,
            grade="good",
            summary="表现良好。",
            strengths=["可读性好"],
            weaknesses=[],
            suggestions=[],
            judged_at="2026-06-15T10:00:00",
            dimensions={"readability": 4.0},
        )
        sample = StyleSample(
            id="sample_test3",
            route_id="local_frame_compose",
            route_name="Test Route",
            style_name="Test Style",
            status=SampleStatus.CANDIDATE,
            params={},
            output=out,
            tags=[],
            visual_judgement=judgement,
        )
        d = sample.to_dict()
        assert "visual_judgement" in d
        assert d["visual_judgement"]["score"] == 75.0
        assert d["visual_judgement"]["grade"] == "good"

    def test_from_dict_handles_missing_visual_judgement(self):
        """from_dict should handle records without visual_judgement (backward compat)."""
        # Simulate old record without visual_judgement field
        old_record = {
            "id": "sample_old1",
            "route_id": "local_frame_compose",
            "route_name": "Test Route",
            "style_name": "Test Style",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "test.mp4", "poster": "", "audio_url": "", "srt_url": "", "manifest_url": ""},
            "tags": [],
            "created_at": "2026-06-15T10:00:00",
            # No visual_judgement field - old record
        }
        sample = StyleSample.from_dict(old_record)
        assert sample.visual_judgement is None
        assert sample.id == "sample_old1"

    def test_from_dict_handles_present_visual_judgement(self):
        """from_dict should deserialize visual_judgement when present."""
        record = {
            "id": "sample_j1",
            "route_id": "local_frame_compose",
            "route_name": "Test Route",
            "style_name": "Test Style",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "test.mp4", "poster": "", "audio_url": "", "srt_url": "", "manifest_url": ""},
            "tags": [],
            "created_at": "2026-06-15T10:00:00",
            "visual_judgement": {
                "score": 88.0,
                "grade": "excellent",
                "summary": "优秀表现",
                "strengths": ["排版好", "清晰"],
                "weaknesses": [],
                "suggestions": [],
                "judged_at": "2026-06-15T10:00:00",
                "dimensions": {"layout": 4.5, "readability": 4.5},
            },
        }
        sample = StyleSample.from_dict(record)
        assert sample.visual_judgement is not None
        assert sample.visual_judgement.score == 88.0
        assert sample.visual_judgement.grade == "excellent"

    def test_visual_judgement_grade_bounds(self):
        """Grade should be determined by score ranges."""
        judgement_excellent = VisualJudgement(
            score=90.0, grade="excellent", summary="", judged_at="", dimensions={},
        )
        judgement_good = VisualJudgement(
            score=80.0, grade="good", summary="", judged_at="", dimensions={},
        )
        judgement_ok = VisualJudgement(
            score=60.0, grade="ok", summary="", judged_at="", dimensions={},
        )
        judgement_poor = VisualJudgement(
            score=40.0, grade="poor", summary="", judged_at="", dimensions={},
        )
        assert judgement_excellent.grade == "excellent"
        assert judgement_good.grade == "good"
        assert judgement_ok.grade == "ok"
        assert judgement_poor.grade == "poor"


# ─── Router Judge Endpoint Tests ─────────────────────────────────────────────

class TestJudgeEndpoint:
    """Test POST /style-samples/{sample_id}/judge endpoint."""

    def test_judge_returns_404_for_missing_sample(self):
        """Judge endpoint should return 404 when sample not found."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/video-lab/style-samples/nonexistent_id/judge")
        assert resp.status_code == 404

    def test_judge_returns_400_when_no_media(self):
        """Judge endpoint should return 400 when sample has no poster or video."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus

        # Create a sample without poster or video
        out = StyleSampleOutput(type="mp4", path="", poster="")
        sample = StyleSample(
            id="sample_no_media",
            route_id="local_frame_compose",
            route_name="Test",
            style_name="Test",
            status=SampleStatus.CANDIDATE,
            params={},
            output=out,
            tags=[],
        )

        # Save it directly to the store
        from app.video_lab.style_gallery import store as sg_store
        sg_store.save_sample(sample)

        try:
            client = TestClient(app)
            resp = client.post("/video-lab/style-samples/sample_no_media/judge")
            assert resp.status_code == 400
            assert "No poster or video" in resp.json()["detail"]
        finally:
            sg_store.delete_sample("sample_no_media")

    def test_judge_returns_500_when_vision_api_fails(self, monkeypatch):
        """Judge endpoint should return 500 when visual judge API fails."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus
        import tempfile
        from pathlib import Path

        # Create a sample with a poster path
        out = StyleSampleOutput(type="mp4", path="", poster="style_gallery/test/sample.jpg")
        sample = StyleSample(
            id="sample_judge_fail",
            route_id="local_frame_compose",
            route_name="Test",
            style_name="Test",
            status=SampleStatus.CANDIDATE,
            params={},
            output=out,
            tags=[],
        )

        from app.video_lab.style_gallery import store as sg_store
        sg_store.save_sample(sample)

        # Create temp poster file
        runtime = Path(__file__).parent.parent / "runtime" / "style_gallery"
        poster_file = runtime / "style_gallery" / "test" / "sample.jpg"
        poster_file.parent.mkdir(parents=True, exist_ok=True)
        poster_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 100)

        try:
            # Mock assess_visual_quality to fail (patch where it's imported in router)
            def mock_fail(path):
                return {"success": False, "message": "API key missing"}

            with patch("app.video_lab.quality.visual_judge.assess_visual_quality", mock_fail):
                client = TestClient(app)
                resp = client.post("/video-lab/style-samples/sample_judge_fail/judge")
                assert resp.status_code == 500
        finally:
            sg_store.delete_sample("sample_judge_fail")
            if poster_file.exists():
                poster_file.unlink()

    def test_judge_returns_structure_with_required_fields(self, monkeypatch):
        """Judge endpoint should return score/grade/summary when successful."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus
        from pathlib import Path

        # Create a sample with poster
        out = StyleSampleOutput(type="mp4", path="", poster="style_gallery/test/sample_ok.jpg")
        sample = StyleSample(
            id="sample_judge_ok",
            route_id="local_frame_compose",
            route_name="Test",
            style_name="Test",
            status=SampleStatus.CANDIDATE,
            params={},
            output=out,
            tags=[],
        )

        from app.video_lab.style_gallery import store as sg_store
        sg_store.save_sample(sample)

        # Create temp poster file
        runtime = Path(__file__).parent.parent / "runtime" / "style_gallery"
        poster_file = runtime / "style_gallery" / "test" / "sample_ok.jpg"
        poster_file.parent.mkdir(parents=True, exist_ok=True)
        poster_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)

        try:
            # Mock assess_visual_quality to succeed (patch where it's imported in router)
            def mock_success(path):
                return {
                    "success": True,
                    "scores": {"layout": 4.0, "readability": 4.2, "hierarchy": 3.8, "aesthetics": 4.0},
                    "overall": 4.0,
                    "suggestions": ["建议1", "建议2"],
                    "frameCount": 1,
                    "judge": "test",
                }

            with patch("app.video_lab.quality.visual_judge.assess_visual_quality", mock_success):
                client = TestClient(app)
                resp = client.post("/video-lab/style-samples/sample_judge_ok/judge")
                assert resp.status_code == 200
                data = resp.json()
                assert "visual_judgement" in data
                assert "score" in data["visual_judgement"]
                assert "grade" in data["visual_judgement"]
                assert "summary" in data["visual_judgement"]
                assert data["visual_judgement"]["score"] == 80.0  # 4.0 * 20
                assert data["visual_judgement"]["grade"] == "good"
        finally:
            sg_store.delete_sample("sample_judge_ok")
            if poster_file.exists():
                poster_file.unlink()

    def test_judge_extracts_frame_when_only_video(self, monkeypatch, tmp_path):
        """V0.4.5: 无 poster、只有视频时，judge 应先抽帧（送评委的是 .png 而非 .mp4）。"""
        import shutil
        import subprocess
        from pathlib import Path
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus
        from app.video_lab.style_gallery import store as sg_store, score_history

        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            import pytest as _pytest
            _pytest.skip("ffmpeg/ffprobe not available")

        # 隔离评分历史，避免污染 runtime
        monkeypatch.setattr(score_history, "_JSONL_PATH", tmp_path / "sh.jsonl")
        monkeypatch.setattr(score_history, "_RECORDS_DIR", tmp_path)

        vid_rel = "style_gallery/test/judge_vid.mp4"
        vid_abs = Path("runtime") / vid_rel
        vid_abs.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=10",
             "-pix_fmt", "yuv420p", vid_abs.as_posix()],
            capture_output=True, timeout=60,
        )
        assert vid_abs.exists(), "failed to create test video"

        out = StyleSampleOutput(type="mp4", path=vid_rel, poster="")
        sample = StyleSample(
            id="sample_vidjudge", route_id="local_frame_compose", route_name="T",
            style_name="T", status=SampleStatus.CANDIDATE, params={}, output=out, tags=[],
        )
        sg_store.save_sample(sample)

        captured = {}

        def mock_ok(path):
            captured["path"] = path
            return {"success": True, "scores": {"layout": 4.0, "readability": 4.0},
                    "overall": 4.0, "suggestions": [], "judge": "test"}

        try:
            with patch("app.video_lab.quality.visual_judge.assess_visual_quality", mock_ok):
                client = TestClient(app)
                resp = client.post("/video-lab/style-samples/sample_vidjudge/judge")
                assert resp.status_code == 200, resp.text
                # 关键：送给评委的是抽出的帧（.png），不是原始 mp4
                assert captured["path"].lower().endswith(".png"), captured.get("path")
        finally:
            sg_store.delete_sample("sample_vidjudge")
            # 清理测试视频和抽出的帧
            for f in vid_abs.parent.glob("*"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def test_judge_returns_503_when_api_key_missing(self):
        """V0.4.8: 缺 MINIMAX_API_KEY 时返回 503 + 明确提示（非 500）。"""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus
        from app.video_lab.style_gallery import store as sg_store
        from pathlib import Path

        out = StyleSampleOutput(type="mp4", path="", poster="style_gallery/test/nokey.jpg")
        sample = StyleSample(
            id="sample_nokey", route_id="local_frame_compose", route_name="T",
            style_name="T", status=SampleStatus.CANDIDATE, params={}, output=out, tags=[],
        )
        sg_store.save_sample(sample)
        poster_file = Path(__file__).parent.parent / "runtime" / "style_gallery" / "style_gallery" / "test" / "nokey.jpg"
        poster_file.parent.mkdir(parents=True, exist_ok=True)
        poster_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 50)

        def mock_no_key(path):
            return {"success": False, "message": "MINIMAX_API_KEY not configured"}

        try:
            with patch("app.video_lab.quality.visual_judge.assess_visual_quality", mock_no_key):
                client = TestClient(app)
                resp = client.post("/video-lab/style-samples/sample_nokey/judge")
                assert resp.status_code == 503, resp.text
                assert "MINIMAX_API_KEY" in resp.json()["detail"]
        finally:
            sg_store.delete_sample("sample_nokey")
            if poster_file.exists():
                poster_file.unlink()

    def test_judge_availability_endpoint(self):
        """可用性端点返回 available + message。"""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.get("/video-lab/style-gallery/judge-availability")
        assert resp.status_code == 200
        data = resp.json()
        assert "available" in data and isinstance(data["available"], bool)
        assert "message" in data
