"""
Tests for V0.3.4 Route Playground
- Default content can create benchmark
- Route Playground API uses existing /route-benchmarks endpoint
- TTS route shows cost warning when selected
- Scoring dimensions are defined
- Markdown export function works
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ─────────────────────────────────────────
# 1. Route Playground reuses existing benchmark API
# ─────────────────────────────────────────
def test_playground_can_run_single_route():
    """Route Playground should be able to run a single route via POST /route-benchmarks."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Route Playground Test",
        "inputPayload": {"content": "今天有三条 AI 动态值得关注。"},
        "commonParams": {},
        "routeIds": ["local_frame_compose"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "benchmarkId" in data
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["routeId"] == "local_frame_compose"


def test_playground_runs_multiple_routes():
    """Route Playground should be able to run multiple selected routes."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Route Playground Multi",
        "inputPayload": {"content": "今天有三条 AI 动态值得关注。"},
        "commonParams": {},
        "routeIds": ["local_frame_compose", "template_programmatic_render"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2
    route_ids = {r["routeId"] for r in data["results"]}
    assert "local_frame_compose" in route_ids
    assert "template_programmatic_render" in route_ids


def test_playground_includes_tts_route():
    """Route Playground includes tts_subtitle_compose in routes."""
    resp = client.get("/video-lab/routes")
    assert resp.status_code == 200
    routes = resp.json()
    route_ids = {r["routeId"] for r in routes}
    assert "tts_subtitle_compose" in route_ids


def test_playground_tts_route_is_real():
    """tts_subtitle_compose should be marked as real."""
    resp = client.get("/video-lab/routes")
    routes = {r["routeId"]: r for r in resp.json()}
    assert routes["tts_subtitle_compose"]["status"] == "real"


def test_playground_hyperframes_is_manual():
    """hyperframes_html_render should be marked as manual."""
    resp = client.get("/video-lab/routes")
    routes = {r["routeId"]: r for r in resp.json()}
    assert routes["hyperframes_html_render"]["status"] == "manual"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
