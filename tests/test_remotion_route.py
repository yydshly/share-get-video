"""
Tests for V0.3.1 Remotion Route
- Real Remotion template_programmatic_render route
- Minimum verification tests
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app.main import app
from app.video_lab.routes_benchmark.registry import get_route_by_id
from app.video_lab.adapters.remotion_template import run_remotion_template


client = TestClient(app)


# ─────────────────────────────────────────
# 1. Registry: template_programmatic_render is real
# ─────────────────────────────────────────
def test_template_programmatic_render_is_real():
    """Registry: template_programmatic_render should have status='real'."""
    route = get_route_by_id("template_programmatic_render")
    assert route is not None, "template_programmatic_render should be registered"
    assert route.status == "real", f"Expected status='real', got '{route.status}'"


def test_template_programmatic_render_has_correct_description():
    """Registry: template_programmatic_render description should mention real rendering."""
    route = get_route_by_id("template_programmatic_render")
    assert route is not None
    assert "Remotion" in route.description or "real" in route.description.lower()


def test_template_programmatic_render_expected_pipeline_has_remotion():
    """Registry: template_programmatic_render expected pipeline should include Remotion steps."""
    route = get_route_by_id("template_programmatic_render")
    assert route is not None
    pipeline = route.expected_pipeline
    assert any("Remotion" in step or "remotion" in step.lower() for step in pipeline), \
        f"Pipeline should mention Remotion steps: {pipeline}"


# ─────────────────────────────────────────
# 2. Props builder tests
# ─────────────────────────────────────────
def test_remotion_props_builder_generates_title():
    """Props builder should generate title from structured content."""
    from app.video_lab.renderers.remotion.props_builder import build_remotion_props

    structured = {
        "lead": "GPT-5 发布，性能大幅提升",
        "totalItems": 1,
    }
    key_points = {
        "keyPoints": [
            {"title": "GPT-5 发布", "body": "性能大幅提升", "source": "OpenAI"}
        ]
    }
    params = {"targetDuration": 30}

    # Mock the file writing part
    with patch("app.video_lab.renderers.remotion.props_builder.get_experiment_dir") as mock_dir:
        mock_dir.return_value = MagicMock()
        mock_path = MagicMock()
        mock_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_path.open = MagicMock()

        with patch("builtins.open", mock_path.open):
            props = build_remotion_props("test_exp", structured, key_points, params)

    assert "title" in props
    assert props["title"] != ""


def test_remotion_props_builder_generates_keypoints():
    """Props builder should generate keyPoints array."""
    from app.video_lab.renderers.remotion.props_builder import build_remotion_props

    structured = {"lead": "测试", "totalItems": 2}
    key_points = {
        "keyPoints": [
            {"title": "Point 1", "body": "Body 1", "source": "Src1"},
            {"title": "Point 2", "body": "Body 2", "source": "Src2"},
        ]
    }
    params = {"targetDuration": 30}

    with patch("app.video_lab.renderers.remotion.props_builder.get_experiment_dir") as mock_dir:
        mock_dir.return_value = MagicMock()
        mock_path = MagicMock()
        mock_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_path.open = MagicMock()

        with patch("builtins.open", mock_path.open):
            props = build_remotion_props("test_exp", structured, key_points, params)

    assert "keyPoints" in props
    assert isinstance(props["keyPoints"], list)
    assert len(props["keyPoints"]) == 2


def test_remotion_props_builder_generates_duration_sec():
    """Props builder should generate durationSec."""
    from app.video_lab.renderers.remotion.props_builder import build_remotion_props

    structured = {"lead": "测试", "totalItems": 3}
    key_points = {"keyPoints": [{"title": f"P{i}", "body": f"B{i}", "source": ""} for i in range(3)]}
    params = {"targetDuration": 45}

    with patch("app.video_lab.renderers.remotion.props_builder.get_experiment_dir") as mock_dir:
        mock_dir.return_value = MagicMock()
        mock_path = MagicMock()
        mock_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_path.open = MagicMock()

        with patch("builtins.open", mock_path.open):
            props = build_remotion_props("test_exp", structured, key_points, params)

    assert "durationSec" in props
    assert isinstance(props["durationSec"], int)
    assert props["durationSec"] > 0


# ─────────────────────────────────────────
# 3. Adapter: missing content returns failed
# ─────────────────────────────────────────
def test_remotion_adapter_empty_content_returns_failed():
    """Adapter should return failed result when content is empty."""
    result = run_remotion_template(
        experiment_id="test_exp_empty",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": ""},
        params={"targetDuration": 30},
    )
    # Should have steps indicating failure
    step_names = [s.name for s in result.productionSteps]
    assert "Structure Content" in step_names
    # The failed step should be there
    statuses = [s.status.value for s in result.productionSteps]
    assert "failed" in statuses
    assert result.videoUrl == ""


# ─────────────────────────────────────────
# 4. Adapter: Remotion environment unavailable returns failed (no exception)
# ─────────────────────────────────────────
def test_remotion_adapter_env_unavailable_returns_failed():
    """Adapter should return failed result when Remotion env is unavailable, without raising."""
    # Patch check_remotion_available to return False
    with patch("app.video_lab.adapters.remotion_template.check_remotion_available") as mock_check:
        mock_check.return_value = (False, "Remotion not installed. Run: cd remotion && npm install.")

        result = run_remotion_template(
            experiment_id="test_exp_no_env",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "GPT-5 发布，性能大幅提升。Claude 4 同时发布。"},
            params={"targetDuration": 30},
        )

    # Should not raise, should return failed
    assert result.videoUrl == ""
    # Should have a warning about environment in the logs
    logs_text = "\n".join(result.logs)
    assert any("Remotion" in log or "npm" in log for log in result.logs), \
        f"Expected Remotion/npm warning in logs, got: {result.logs}"


# ─────────────────────────────────────────
# 5. Route benchmark: template_programmatic_render is not mock
# ─────────────────────────────────────────
def test_benchmark_template_programmatic_render_not_mock():
    """Benchmark for template_programmatic_render should NOT return mock status.

    This test verifies the route is real. It may succeed or fail depending
    on whether Remotion is installed, but it should never return status='mock'.
    """
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Remotion Route Not Mock Test",
        "inputPayload": {"content": "测试内容"},
        "commonParams": {"targetDuration": 15, "keyPointCount": 1},
        "routeIds": ["template_programmatic_render"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data["results"][0]
    assert result["routeId"] == "template_programmatic_render"
    # Must be real - not mock
    assert result["status"] != "mock", \
        "template_programmatic_render should be real, not mock"
    # Should be either succeeded or failed (depending on Remotion env)
    assert result["status"] in ("succeeded", "failed"), \
        f"Expected 'succeeded' or 'failed', got '{result['status']}'"


# ─────────────────────────────────────────
# 6. RouteResult structure
# ─────────────────────────────────────────
def test_route_result_structure_has_required_fields():
    """RouteResult should contain routeId, status, summary, metrics, warnings."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Route Result Structure Test",
        "inputPayload": {"content": "测试"},
        "commonParams": {},
        "routeIds": ["template_programmatic_render"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    result = data["results"][0]
    # Required fields per spec
    assert "routeId" in result, "RouteResult must have routeId"
    assert "status" in result, "RouteResult must have status"
    assert "summary" in result, "RouteResult must have summary"
    assert "metrics" in result, "RouteResult must have metrics"
    assert "warnings" in result, "RouteResult must have warnings"


# ─────────────────────────────────────────
# 7. Real render with mocked subprocess (avoids real Node/Chrome)
# ─────────────────────────────────────────
def test_remotion_adapter_with_mocked_render():
    """Adapter with mocked Remotion render should succeed without real Node/Chrome."""
    # Mock check_remotion_available to say available
    # Mock render_remotion_video to return success
    with patch("app.video_lab.adapters.remotion_template.check_remotion_available") as mock_check:
        mock_check.return_value = (True, "OK")

        with patch("app.video_lab.adapters.remotion_template.render_remotion_video") as mock_render:
            mock_render.return_value = {
                "success": True,
                "videoUrl": "/runtime/video_lab/experiments/test_exp/output.mp4",
                "manifestUrl": "/runtime/video_lab/experiments/test_exp/manifest.json",
                "message": "Success",
                "logs": ["[Remotion] Success"],
                "warnings": [],
            }

            result = run_remotion_template(
                experiment_id="test_exp_mock_render",
                test_case_id="case_ai_frontier_daily_001",
                input_payload={"content": "GPT-5 发布，性能大幅提升。Claude 4 发布，推理能力增强。"},
                params={"targetDuration": 30, "keyPointCount": 2},
            )

    assert result.videoUrl != "", "Should have videoUrl on successful render"
    assert result.adapter == "template_programmatic_render"
    assert result.provider == "Remotion"
    # Check assets
    assert result.assets.get("engine") == "remotion"
    assert result.assets.get("routeReal") is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
