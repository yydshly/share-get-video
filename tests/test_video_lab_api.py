"""
Tests for Video Lab API endpoints
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ─────────────────────────────────────────────
# POST /video-lab/experiments
# ─────────────────────────────────────────────
def test_create_experiment_accepts_json_body():
    """POST /experiments should accept a JSON body and return experiment+result."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_template_programmatic_render",
        "title": "API JSON body test",
        "inputPayload": {"content": "今日 AI 前沿测试内容"},
        "params": {"targetDuration": 45, "aspectRatio": "9:16"},
    }

    resp = client.post("/video-lab/experiments", json=payload)

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "experiment" in data, f"Response should have 'experiment' key: {data}"
    assert data["experiment"]["testCaseId"] == payload["testCaseId"]
    assert data["experiment"]["methodId"] == payload["methodId"]
    assert data["experiment"]["title"] == payload["title"]
    assert "result" in data


def test_create_experiment_missing_required_field_returns_422():
    """Missing required field (title) should return HTTP 422."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_template_programmatic_render",
        # missing: "title"
    }

    resp = client.post("/video-lab/experiments", json=payload)

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_create_experiment_empty_title_returns_422():
    """Empty string for required field should return HTTP 422."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_template_programmatic_render",
        "title": "",
    }

    resp = client.post("/video-lab/experiments", json=payload)

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_create_experiment_unknown_test_case_returns_400():
    """Unknown testCaseId should return HTTP 400."""
    payload = {
        "testCaseId": "nonexistent_case",
        "methodId": "method_template_programmatic_render",
        "title": "Should fail",
        "inputPayload": {},
        "params": {},
    }

    resp = client.post("/video-lab/experiments", json=payload)

    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "Unknown test case" in data["detail"]


def test_create_experiment_unknown_method_returns_400():
    """Unknown methodId should return HTTP 400."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "nonexistent_method",
        "title": "Should fail",
        "inputPayload": {},
        "params": {},
    }

    resp = client.post("/video-lab/experiments", json=payload)

    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "Unknown method" in data["detail"]


def test_create_experiment_local_frame_compose_ffmpeg_failure_returns_200_with_failed_status(monkeypatch):
    """
    When local_frame_compose runs but FFmpeg is unavailable,
    the API should return HTTP 200 with experiment.status='failed'.
    The business failure is distinguished from HTTP errors.
    """
    # Patch check_ffmpeg_available at BOTH locations (ffmpeg_composer and local_frame_compose import)
    def fake_check(*args, **kwargs):
        return False

    monkeypatch.setattr(
        "app.video_lab.renderers.ffmpeg_composer.check_ffmpeg_available",
        fake_check,
    )
    monkeypatch.setattr(
        "app.video_lab.adapters.local_frame_compose.check_ffmpeg_available",
        fake_check,
    )

    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "FFmpeg failure test via API",
        "inputPayload": {"content": "Test content"},
        "params": {"targetDuration": 10},
    }

    resp = client.post("/video-lab/experiments", json=payload)

    # API should be 200 — the experiment ran but the adapter reported failure
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["experiment"]["status"] == "failed", (
        f"experiment.status should be 'failed', got: {data['experiment']['status']}"
    )
    assert "result" in data
    assert data["result"]["rawOutput"]["ffmpegSuccess"] is False


# ─────────────────────────────────────────────
# GET endpoints
# ─────────────────────────────────────────────
def test_list_test_cases_returns_200():
    resp = client.get("/video-lab/test-cases")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_test_case_returns_404_for_unknown():
    resp = client.get("/video-lab/test-cases/nonexistent_case")
    assert resp.status_code == 404


def test_list_methods_returns_200():
    resp = client.get("/video-lab/methods")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_method_returns_404_for_unknown():
    resp = client.get("/video-lab/methods/nonexistent_method")
    assert resp.status_code == 404


def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
