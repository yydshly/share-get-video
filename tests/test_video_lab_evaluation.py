"""
Tests for evaluation API endpoints
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def _create_experiment():
    """Helper: create a mock experiment via the runner."""
    from app.video_lab.experiment_runner import get_runner
    runner = get_runner()
    exp = runner.create_experiment(
        test_case_id="case_ai_frontier_daily_001",
        method_id="method_template_programmatic_render",
        title="Evaluation Test Experiment",
        input_payload={"content": "Test content"},
        params={},
    )
    runner.run_experiment(exp.id)
    return exp.id


def test_save_evaluation_success():
    """POST /experiments/{id}/evaluation should save a valid evaluation."""
    exp_id = _create_experiment()
    payload = {
        "informationAccuracy": 4,
        "readability": 5,
        "visualQuality": 4,
        "pacing": 3,
        "shareability": 4,
        "stability": 5,
        "productizationValue": 4,
        "notes": "Test notes",
    }
    resp = client.post(f"/video-lab/experiments/{exp_id}/evaluation", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["experimentId"] == exp_id
    assert data["informationAccuracy"] == 4
    assert data["readability"] == 5
    assert data["notes"] == "Test notes"
    assert data["averageScore"] is not None


def test_get_evaluation_success():
    """GET /experiments/{id}/evaluation should return saved evaluation."""
    exp_id = _create_experiment()
    payload = {
        "informationAccuracy": 4,
        "readability": 3,
        "visualQuality": 4,
        "pacing": 3,
        "shareability": 2,
        "stability": 4,
        "productizationValue": 3,
        "notes": "",
    }
    client.post(f"/video-lab/experiments/{exp_id}/evaluation", json=payload)
    resp = client.get(f"/video-lab/experiments/{exp_id}/evaluation")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["experimentId"] == exp_id
    assert data["informationAccuracy"] == 4


def test_get_evaluation_not_found():
    """GET /experiments/{id}/evaluation should return 404 when no evaluation exists."""
    # Use a real-looking experiment ID that won't exist in the runner
    resp = client.get("/video-lab/experiments/nonexistent_exp_id/evaluation")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


def test_save_evaluation_experiment_not_found():
    """POST /experiments/{id}/evaluation should return 404 for unknown experiment."""
    payload = {
        "informationAccuracy": 4,
        "readability": 3,
        "visualQuality": 4,
        "pacing": 3,
        "shareability": 2,
        "stability": 4,
        "productizationValue": 3,
        "notes": "",
    }
    resp = client.post("/video-lab/experiments/nonexistent_exp_id/evaluation", json=payload)
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


def test_save_evaluation_missing_field_returns_422():
    """Missing a required field should return HTTP 422."""
    exp_id = _create_experiment()
    payload = {
        "informationAccuracy": 4,
        # missing: readability, visualQuality, pacing, ...
    }
    resp = client.post(f"/video-lab/experiments/{exp_id}/evaluation", json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_save_evaluation_out_of_range_returns_422():
    """Score < 1 or > 5 should return HTTP 422."""
    exp_id = _create_experiment()
    # Score too high
    payload = {
        "informationAccuracy": 4,
        "readability": 3,
        "visualQuality": 6,  # out of range
        "pacing": 3,
        "shareability": 2,
        "stability": 4,
        "productizationValue": 3,
        "notes": "",
    }
    resp = client.post(f"/video-lab/experiments/{exp_id}/evaluation", json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_experiment_detail_returns_result():
    """GET /experiments/{id} should return experiment with result."""
    exp_id = _create_experiment()
    resp = client.get(f"/video-lab/experiments/{exp_id}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "experiment" in data
    assert data["experiment"]["id"] == exp_id
    assert "result" in data
    assert data["result"] is not None


def test_experiment_detail_not_found():
    """GET /experiments/{id} should return 404 for unknown experiment."""
    resp = client.get("/video-lab/experiments/nonexistent_exp_id")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
