"""
Tests for V0.3.0 Route Benchmark module
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ─────────────────────────────────────────
# GET /routes
# ─────────────────────────────────────────
def test_list_routes_returns_200():
    """GET /routes should return 200 with a list."""
    resp = client.get("/video-lab/routes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 6


def test_list_routes_contains_all_route_ids():
    """Routes should include all 6 registered route IDs."""
    resp = client.get("/video-lab/routes")
    assert resp.status_code == 200
    data = resp.json()
    route_ids = [r["routeId"] for r in data]
    expected = [
        "local_frame_compose",
        "template_programmatic_render",
        "tts_subtitle_compose",
        "ai_asset_then_compose",
        "ai_video_direct",
        "hybrid_pipeline",
    ]
    for rid in expected:
        assert rid in route_ids, f"Missing route: {rid}"


def test_list_routes_includes_status():
    """Each route should include status (real/mock/reserved)."""
    resp = client.get("/video-lab/routes")
    assert resp.status_code == 200
    data = resp.json()
    for route in data:
        assert "status" in route
        assert route["status"] in ("real", "mock", "reserved")
        assert "routeId" in route
        assert "name" in route
        assert "expectedPipeline" in route


# ─────────────────────────────────────────
# POST /route-benchmarks
# ─────────────────────────────────────────
def test_create_benchmark_with_local_frame_compose():
    """POST /route-benchmarks should run local_frame_compose route."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Benchmark Test",
        "inputPayload": {"content": "测试内容"},
        "commonParams": {
            "targetDuration": 20,
            "keyPointCount": 2,
            "transitionEnabled": False,
            "transitionFrames": 0,
        },
        "routeIds": ["local_frame_compose"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert "benchmarkId" in data
    assert data["title"] == "Benchmark Test"
    assert data["testCaseId"] == "case_ai_frontier_daily_001"
    assert len(data["results"]) == 1

    result = data["results"][0]
    assert result["routeId"] == "local_frame_compose"
    # local_frame_compose is real - may succeed or fail depending on FFmpeg
    assert result["status"] in ("succeeded", "failed")


def test_create_benchmark_with_mock_route():
    """Benchmark with mock route should return mock result."""
    # Note: template_programmatic_render is now real (V0.3.1)
    # Use tts_subtitle_compose which is still mock
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Mock Benchmark",
        "inputPayload": {"content": "测试"},
        "commonParams": {},
        "routeIds": ["tts_subtitle_compose"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data["results"][0]
    assert result["routeId"] == "tts_subtitle_compose"
    assert result["status"] == "mock"


def test_create_benchmark_with_reserved_route():
    """Benchmark with reserved route should return reserved result."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Reserved Benchmark",
        "inputPayload": {"content": "测试"},
        "commonParams": {},
        "routeIds": ["ai_video_direct"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data["results"][0]
    assert result["routeId"] == "ai_video_direct"
    assert result["status"] == "reserved"


def test_create_benchmark_with_multiple_routes():
    """Benchmark with multiple routes should return results for each."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Multi Route",
        "inputPayload": {"content": "测试"},
        "commonParams": {},
        "routeIds": ["local_frame_compose", "template_programmatic_render", "ai_video_direct"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert len(data["results"]) == 3
    route_ids = [r["routeId"] for r in data["results"]]
    assert "local_frame_compose" in route_ids
    assert "template_programmatic_render" in route_ids
    assert "ai_video_direct" in route_ids


def test_create_benchmark_unknown_route_id_returns_400():
    """Unknown route ID should return 400."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Bad Route",
        "inputPayload": {"content": "测试"},
        "commonParams": {},
        "routeIds": ["nonexistent_route"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "Unknown route IDs" in data["detail"]


# ─────────────────────────────────────────
# GET /route-benchmarks/{id}
# ─────────────────────────────────────────
def test_get_benchmark_returns_result():
    """GET /route-benchmarks/{id} should return the benchmark."""
    # First create
    create_payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Get Test",
        "inputPayload": {"content": "测试"},
        "commonParams": {},
        "routeIds": ["local_frame_compose"],
    }
    create_resp = client.post("/video-lab/route-benchmarks", json=create_payload)
    assert create_resp.status_code == 200
    benchmark_id = create_resp.json()["benchmarkId"]

    # Then get
    get_resp = client.get(f"/video-lab/route-benchmarks/{benchmark_id}")
    assert get_resp.status_code == 200, f"Expected 200, got {get_resp.status_code}: {get_resp.text}"
    data = get_resp.json()
    assert data["benchmarkId"] == benchmark_id


def test_get_benchmark_not_found_returns_404():
    """GET /route-benchmarks/unknown_id should return 404."""
    resp = client.get("/video-lab/route-benchmarks/nonexistent_bench_id")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


# ─────────────────────────────────────────
# local_frame_compose result structure
# ─────────────────────────────────────────
def test_local_frame_compose_result_has_video_url_on_success():
    """Successful local_frame_compose result should include videoUrl."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Video URL Test",
        "inputPayload": {"content": "测试内容"},
        "commonParams": {
            "targetDuration": 15,
            "keyPointCount": 1,
            "transitionEnabled": False,
            "transitionFrames": 0,
        },
        "routeIds": ["local_frame_compose"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    result = data["results"][0]
    # If succeeded, should have videoUrl
    if result["status"] == "succeeded":
        assert result["videoUrl"] != ""
        assert "metrics" in result


# ─────────────────────────────────────────
# Registry functions
# ─────────────────────────────────────────
def test_registry_list_routes():
    """Registry should list 6 routes."""
    from app.video_lab.routes_benchmark.registry import list_routes
    routes = list_routes()
    assert len(routes) == 6


def test_registry_get_route_by_id():
    """Registry should get route by ID."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id
    route = get_route_by_id("local_frame_compose")
    assert route is not None
    assert route.route_id == "local_frame_compose"
    assert route.status == "real"

    route = get_route_by_id("nonexistent")
    assert route is None


def test_registry_get_routes_by_ids():
    """Registry should get multiple routes by IDs."""
    from app.video_lab.routes_benchmark.registry import get_routes_by_ids
    routes = get_routes_by_ids(["local_frame_compose", "ai_video_direct"])
    assert len(routes) == 2
    ids = [r.route_id for r in routes]
    assert "local_frame_compose" in ids
    assert "ai_video_direct" in ids


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
