"""
tests/test_style_gallery_templates.py
V0.4.2: Style Sample promotion to template tests
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus, VisualJudgement
from app.video_lab.style_gallery import templates as sg_templates


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_templates_dir(monkeypatch, tmp_path):
    """Redirect templates JSONL path to a temp directory."""
    runtime = tmp_path / "runtime" / "style_gallery"
    records_dir = runtime / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = records_dir / "style_templates.jsonl"

    monkeypatch.setattr(sg_templates, "_RUNTIME", runtime)
    monkeypatch.setattr(sg_templates, "_RECORDS_DIR", records_dir)
    monkeypatch.setattr(sg_templates, "_JSONL_PATH", jsonl_path)
    return records_dir


def make_sample_with_judgement(
    sample_id: str,
    route_id: str = "local_frame_compose",
    score: float = 82.0,
) -> StyleSample:
    out = StyleSampleOutput(type="mp4", path="test.mp4")
    judgement = VisualJudgement(
        score=score,
        grade="good",
        summary="整体清晰，数字突出。",
        strengths=["数据突出", "排版稳定"],
        weaknesses=["文字略密"],
        suggestions=["减少副标题长度"],
        judged_at="2026-06-15T10:00:00",
        dimensions={"layout": 4.0, "readability": 4.2},
    )
    return StyleSample(
        id=sample_id,
        route_id=route_id,
        route_name="Test Route",
        style_name="Test Style",
        description="Test description",
        status=SampleStatus.CANDIDATE,
        params={"showDataViz": True, "highlightMode": "auto"},
        output=out,
        tags=["测试"],
        visual_judgement=judgement,
        created_at=datetime.utcnow(),
    )


def make_sample_without_judgement(sample_id: str) -> StyleSample:
    out = StyleSampleOutput(type="mp4", path="test.mp4")
    return StyleSample(
        id=sample_id,
        route_id="local_frame_compose",
        route_name="Test Route",
        style_name="Test Style",
        status=SampleStatus.CANDIDATE,
        params={},
        output=out,
        tags=[],
        created_at=datetime.utcnow(),
    )


# ─── Template Model Tests ─────────────────────────────────────────────────────

class TestStyleTemplateModel:
    """Test StyleTemplate model."""

    def test_template_to_dict(self):
        """StyleTemplate.to_dict() should serialize all fields."""
        template = sg_templates.StyleTemplate(
            id="template_abc123",
            name="测试模板",
            route_id="local_frame_compose",
            route_name="Pillow 信息卡路线",
            style_name="测试风格",
            description="测试描述",
            params={"showDataViz": True},
            source_sample_id="sample_xyz",
            source_sample_score=82.0,
            visual_judgement={"score": 82, "grade": "good"},
            tags=["测试"],
            created_at=datetime.fromisoformat("2026-06-15T10:00:00"),
        )
        d = template.to_dict()
        assert d["id"] == "template_abc123"
        assert d["name"] == "测试模板"
        assert d["source_sample_score"] == 82.0
        assert d["visual_judgement"]["score"] == 82
        assert "created_at" in d

    def test_template_from_dict(self):
        """StyleTemplate.from_dict() should deserialize correctly."""
        data = {
            "id": "template_xyz",
            "name": "另一个模板",
            "route_id": "template_programmatic_render",
            "route_name": "Remotion 路线",
            "style_name": "动态栏目",
            "description": "",
            "params": {"motionIntensity": "high"},
            "source_sample_id": "sample_123",
            "source_sample_score": 88.0,
            "visual_judgement": None,
            "tags": ["动态"],
            "created_at": "2026-06-15T10:00:00",
        }
        template = sg_templates.StyleTemplate.from_dict(data)
        assert template.id == "template_xyz"
        assert template.route_id == "template_programmatic_render"
        assert template.source_sample_score == 88.0


# ─── Template CRUD Tests ─────────────────────────────────────────────────────

class TestTemplateCrud:
    """Test templates store CRUD operations."""

    def test_save_and_list_template(self, temp_templates_dir):
        """save_template and list_templates should work together."""
        template = sg_templates.StyleTemplate(
            id="template_save1",
            name="测试模板1",
            route_id="local_frame_compose",
            route_name="Test",
            style_name="Style",
            params={},
            source_sample_id="sample_1",
        )
        sg_templates.save_template(template)

        templates = sg_templates.list_templates()
        assert len(templates) == 1
        assert templates[0].id == "template_save1"

    def test_get_template(self, temp_templates_dir):
        """get_template should return correct template."""
        template = sg_templates.StyleTemplate(
            id="template_get1",
            name="获取测试",
            route_id="local_frame_compose",
            route_name="Test",
            style_name="Style",
            params={},
            source_sample_id="sample_1",
        )
        sg_templates.save_template(template)

        found = sg_templates.get_template("template_get1")
        assert found is not None
        assert found.name == "获取测试"

    def test_get_nonexistent_returns_none(self, temp_templates_dir):
        """get_template should return None for missing id."""
        found = sg_templates.get_template("nonexistent")
        assert found is None

    def test_delete_template(self, temp_templates_dir):
        """delete_template should remove record."""
        template = sg_templates.StyleTemplate(
            id="template_del1",
            name="删除测试",
            route_id="local_frame_compose",
            route_name="Test",
            style_name="Style",
            params={},
            source_sample_id="sample_1",
        )
        sg_templates.save_template(template)
        assert len(sg_templates.list_templates()) == 1

        deleted = sg_templates.delete_template("template_del1")
        assert deleted is True
        assert len(sg_templates.list_templates()) == 0

    def test_delete_nonexistent_returns_false(self, temp_templates_dir):
        """delete_template should return False for missing id."""
        deleted = sg_templates.delete_template("nonexistent")
        assert deleted is False

    def test_list_templates_filter_by_route(self, temp_templates_dir):
        """list_templates should filter by route_id."""
        t1 = sg_templates.StyleTemplate(
            id="template_r1",
            name="Pillow模板",
            route_id="local_frame_compose",
            route_name="Pillow",
            style_name="Style",
            params={},
            source_sample_id="s1",
        )
        t2 = sg_templates.StyleTemplate(
            id="template_r2",
            name="Remotion模板",
            route_id="template_programmatic_render",
            route_name="Remotion",
            style_name="Style",
            params={},
            source_sample_id="s2",
        )
        sg_templates.save_template(t1)
        sg_templates.save_template(t2)

        all_templates = sg_templates.list_templates()
        assert len(all_templates) == 2

        pillow_templates = sg_templates.list_templates(route_id="local_frame_compose")
        assert len(pillow_templates) == 1
        assert pillow_templates[0].route_id == "local_frame_compose"


# ─── Router Promote Endpoint Tests ──────────────────────────────────────────

class TestPromoteEndpoint:
    """Test POST /style-samples/{id}/promote-template endpoint."""

    def test_promote_returns_404_for_missing_sample(self):
        """Promote endpoint should return 404 when sample not found."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/video-lab/style-samples/nonexistent_id/promote-template", json={})
        assert resp.status_code == 404

    def test_promote_sample_with_judgement(self, temp_templates_dir):
        """Promote should create template from sample with visual_judgement."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery import store as sg_store

        sample = make_sample_with_judgement("sample_promote1", score=82.0)
        sg_store.save_sample(sample)

        try:
            client = TestClient(app)
            resp = client.post("/video-lab/style-samples/sample_promote1/promote-template", json={"name": "我的高分模板"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "我的高分模板"
            assert data["source_sample_id"] == "sample_promote1"
            assert data["source_sample_score"] == 82.0
            assert "id" in data
            assert data["id"].startswith("template_")
        finally:
            sg_store.delete_sample("sample_promote1")

    def test_promote_sample_without_judgement_returns_warning(self, temp_templates_dir):
        """Promote should succeed but return warning when no visual_judgement."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery import store as sg_store

        sample = make_sample_without_judgement("sample_no_judge")
        sg_store.save_sample(sample)

        try:
            client = TestClient(app)
            resp = client.post("/video-lab/style-samples/sample_no_judge/promote-template", json={})
            assert resp.status_code == 200
            data = resp.json()
            assert "warnings" in data
            assert any("尚未进行视觉评分" in w for w in data["warnings"])
        finally:
            sg_store.delete_sample("sample_no_judge")

    def test_promote_low_score_returns_warning(self, temp_templates_dir):
        """Promote should return warning for low visual score."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery import store as sg_store

        sample = make_sample_with_judgement("sample_low_score", score=45.0)
        sg_store.save_sample(sample)

        try:
            client = TestClient(app)
            resp = client.post("/video-lab/style-samples/sample_low_score/promote-template", json={})
            assert resp.status_code == 200
            data = resp.json()
            assert "warnings" in data
            assert any("低于55分" in w for w in data["warnings"])
        finally:
            sg_store.delete_sample("sample_low_score")

    def test_promote_dedup_no_duplicate(self, temp_templates_dir):
        """V0.4.7: 同一样片重复升级默认不重复创建；force=true 可强制再建。"""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery import store as sg_store, templates as sg_templates

        sample = make_sample_with_judgement("sample_dedup1", score=80.0)
        sg_store.save_sample(sample)
        try:
            client = TestClient(app)
            r1 = client.post("/video-lab/style-samples/sample_dedup1/promote-template", json={})
            assert r1.status_code == 200
            assert not r1.json().get("deduped")

            r2 = client.post("/video-lab/style-samples/sample_dedup1/promote-template", json={})
            assert r2.status_code == 200
            assert r2.json().get("deduped") is True
            assert len(sg_templates.list_templates()) == 1, "重复升级不应新建模板"

            r3 = client.post("/video-lab/style-samples/sample_dedup1/promote-template", json={"force": True})
            assert r3.status_code == 200
            assert not r3.json().get("deduped")
            assert len(sg_templates.list_templates()) == 2, "force 应强制再建一份"
        finally:
            sg_store.delete_sample("sample_dedup1")


class TestTemplateEndpoints:
    """Test template list/get/delete endpoints."""

    def test_list_templates_empty(self):
        """GET /style-templates should return empty list initially."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.get("/video-lab/style-templates")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_delete_template_endpoint(self, temp_templates_dir):
        """DELETE /style-templates/{id} should delete template."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.video_lab.style_gallery import store as sg_store

        # First create a sample and promote it
        sample = make_sample_with_judgement("sample_del_test")
        sg_store.save_sample(sample)

        try:
            client = TestClient(app)
            # Promote
            resp = client.post("/video-lab/style-samples/sample_del_test/promote-template", json={})
            assert resp.status_code == 200
            template_data = resp.json()
            template_id = template_data["id"]

            # Delete via endpoint
            resp = client.delete(f"/video-lab/style-templates/{template_id}")
            assert resp.status_code == 200

            # Verify deleted
            resp = client.get(f"/video-lab/style-templates/{template_id}")
            assert resp.status_code == 404
        finally:
            sg_store.delete_sample("sample_del_test")

    def test_delete_nonexistent_template_returns_404(self):
        """DELETE should return 404 for missing template."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.delete("/video-lab/style-templates/nonexistent_template")
        assert resp.status_code == 404
