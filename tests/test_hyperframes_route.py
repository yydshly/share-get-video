"""
Tests for V0.3.2 HyperFrames HTML Render Route
- HTML builder generates self-contained HTML
- HTML contains title and key points
- HTML has no external network dependencies
- Adapter returns HTML artifact with htmlUrl/htmlPath
- Route Benchmark can run hyperframes route without exceptions
- Registry contains hyperframes_html_render as manual route
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ─────────────────────────────────────────
# 1. Registry contains hyperframes_html_render as manual
# ─────────────────────────────────────────
def test_registry_has_hyperframes_route():
    """Registry should contain hyperframes_html_render with status='manual'."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id

    route = get_route_by_id("hyperframes_html_render")
    assert route is not None, "hyperframes_html_render should be in registry"
    assert route.status == "manual", f"Expected status='manual', got '{route.status}'"
    assert route.adapter_category == "hyperframes_html_render"
    assert "HyperFrames" in route.description or "HTML" in route.description


def test_registry_hyperframes_pipeline_has_html_step():
    """hyperframes_html_render pipeline should include HTML generation step."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id

    route = get_route_by_id("hyperframes_html_render")
    assert route is not None
    pipeline = route.expected_pipeline
    assert any("HTML" in step or "html" in step.lower() for step in pipeline), \
        f"Pipeline should mention HTML: {pipeline}"


# ─────────────────────────────────────────
# 2. HTML builder generates self-contained HTML
# ─────────────────────────────────────────
def test_html_builder_generates_self_contained_html():
    """HTML builder should generate HTML with no external network deps."""
    from app.video_lab.renderers.hyperframes.html_builder import build_html

    structured = {"lead": "GPT-5 发布", "items": [], "totalItems": 1}
    key_points = {"keyPoints": [{"title": "Point 1", "body": "Body 1", "source": ""}]}
    params = {"targetDuration": 30}

    result = build_html("test_exp_html", structured, key_points, params)

    assert result["success"] is True
    assert "htmlUrl" in result
    assert "htmlPath" in result
    assert result["htmlUrl"] != ""
    assert result["htmlPath"] != ""

    # Check file was actually written
    html_path = result["htmlPath"]
    assert os.path.exists(html_path), f"HTML file should exist: {html_path}"

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check key content is present
    assert "GPT-5" in content
    assert "Point 1" in content
    # No external dependencies
    assert "cdn." not in content.lower()
    assert "http://" not in content
    assert "script src=" not in content
    assert 'href="http' not in content


# ─────────────────────────────────────────
# 3. HTML builder contains input title and key points
# ─────────────────────────────────────────
def test_html_builder_contains_title_and_keypoints():
    """Generated HTML should contain the input title and key points."""
    from app.video_lab.renderers.hyperframes.html_builder import build_html

    structured = {"lead": "Test AI News Title", "items": [], "totalItems": 1}
    key_points = {
        "keyPoints": [
            {"title": "AI Breakthrough 1", "body": "Description 1", "source": "Source1"},
            {"title": "AI Breakthrough 2", "body": "Description 2", "source": "Source2"},
        ]
    }
    params = {}

    result = build_html("test_titles", structured, key_points, params)
    html_path = result["htmlPath"]

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Test AI News Title" in content or "AI 前沿动态" in content
    assert "AI Breakthrough 1" in content
    assert "AI Breakthrough 2" in content


# ─────────────────────────────────────────
# 4. HTML is portrait 9:16 ratio
# ─────────────────────────────────────────
def test_html_is_portrait_format():
    """Generated HTML should be portrait 9:16 CSS."""
    from app.video_lab.renderers.hyperframes.html_builder import build_html

    structured = {"lead": "Test", "items": [], "totalItems": 0}
    key_points = {"keyPoints": []}
    result = build_html("test_portrait", structured, key_points, {})

    with open(result["htmlPath"], "r", encoding="utf-8") as f:
        content = f.read()

    # Should be viewport meta tag
    assert 'viewport' in content
    # Width 100vw is portrait-style
    assert "100vw" in content


# ─────────────────────────────────────────
# 5. HTML builder has dark AI theme colors
# ─────────────────────────────────────────
def test_html_has_dark_theme():
    """HTML should use dark background colors."""
    from app.video_lab.renderers.hyperframes.html_builder import build_html

    structured = {"lead": "Test", "items": [], "totalItems": 0}
    key_points = {"keyPoints": []}
    result = build_html("test_theme", structured, key_points, {})

    with open(result["htmlPath"], "r", encoding="utf-8") as f:
        content = f.read()

    # Dark background color
    assert "#0a0e1a" in content or "#111827" in content
    # Accent color
    assert "#3b82f6" in content


# ─────────────────────────────────────────
# 6. Route Benchmark can run hyperframes route
# ─────────────────────────────────────────
def test_route_benchmark_runs_hyperframes_route():
    """Benchmark should be able to run hyperframes_html_render without exceptions."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "HyperFrames HTML Route Test",
        "inputPayload": {"content": "测试内容"},
        "commonParams": {},
        "routeIds": ["hyperframes_html_render"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "benchmarkId" in data
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["routeId"] == "hyperframes_html_render"
    assert result["status"] == "manual", f"Expected 'manual', got '{result['status']}'"
    # Should have HTML artifact URL
    has_html = any(
        a.get("type") == "manifest" and a.get("payload", {}).get("htmlUrl")
        for a in result.get("artifacts", [])
    )
    assert has_html, "Should have HTML artifact with htmlUrl"


# ─────────────────────────────────────────
# 7. Adapter returns manual result with htmlUrl/htmlPath
# ─────────────────────────────────────────
def test_adapter_returns_html_artifact():
    """Adapter should return HTML URL/path in artifacts."""
    from app.video_lab.adapters.hyperframes_html_render import run_hyperframes_html_render

    result = run_hyperframes_html_render(
        experiment_id="test_adapter_html",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": "测试内容"},
        params={"targetDuration": 30},
    )

    # Find manifest artifact with htmlUrl
    html_urls = []
    for step in result.productionSteps:
        for art in step.artifacts:
            d = art.to_dict() if hasattr(art, "to_dict") else art
            if d.get("type") == "manifest":
                payload = d.get("payload", {})
                if payload.get("htmlUrl"):
                    html_urls.append(payload["htmlUrl"])

    assert len(html_urls) >= 1, f"Should have HTML URL in artifacts, got: {[a.to_dict() if hasattr(a, 'to_dict') else a for step in result.productionSteps for a in step.artifacts]}"


# ─────────────────────────────────────────
# 8. HTML has CSS animations
# ─────────────────────────────────────────
def test_html_has_animations():
    """HTML should contain CSS animations."""
    from app.video_lab.renderers.hyperframes.html_builder import build_html

    structured = {"lead": "Test", "items": [], "totalItems": 0}
    key_points = {"keyPoints": []}
    result = build_html("test_anim", structured, key_points, {})

    with open(result["htmlPath"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "@keyframes" in content, "HTML should contain CSS keyframe animations"
    assert "animation" in content, "HTML should use CSS animation properties"


# ─────────────────────────────────────────
# 9. HTML no external resources
# ─────────────────────────────────────────
def test_html_no_external_resources():
    """Generated HTML should not reference external URLs/scripts."""
    from app.video_lab.renderers.hyperframes.html_builder import build_html

    structured = {"lead": "Test", "items": [], "totalItems": 0}
    key_points = {"keyPoints": []}
    result = build_html("test_ext", structured, key_points, {})

    with open(result["htmlPath"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "src=" not in content or 'src="data:' in content, "Should have no external scripts"
    assert "href=" not in content or "href=#" in content, "Should have no external links"
    assert "fonts.googleapis" not in content.lower(), "Should not use Google Fonts CDN"
    assert "cdn." not in content.lower(), "Should not use CDN resources"


# ─────────────────────────────────────────
# 10. RouteBenchmark overall status with manual route
# ─────────────────────────────────────────
def test_benchmark_status_with_manual_route():
    """Benchmark with manual route should complete (not stay running)."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Manual Route Status Test",
        "inputPayload": {"content": "测试"},
        "commonParams": {},
        "routeIds": ["hyperframes_html_render"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Status should be "completed" (manual is treated as non-running terminal state)
    assert data["status"] in ("completed", "partial"), \
        f"Expected completed/partial, got '{data['status']}'"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
