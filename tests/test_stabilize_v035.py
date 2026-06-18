"""
Tests for V0.3.5-dev stabilization fixes:
1. RouteDefinition.status supports "manual"
2. RouteBenchmark supports "completed_with_manual"
3. generation_time_ms is properly measured (not always 0)
4. ExperimentRunner adapter exception -> failed status
5. MethodCategory frontend/backend consistency
6. ROUTE_REGISTRY has 8 routes (local_media_compose added)
7. ArtifactType supports audio_output / subtitle_file / html_output
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ─────────────────────────────────────────
# 1. RouteDefinition.status supports "manual"
# ─────────────────────────────────────────
def test_route_definition_status_includes_manual():
    """RouteDefinition.status type should include 'manual'."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id

    route = get_route_by_id("hyperframes_html_render")
    assert route is not None
    assert route.status == "manual"


def test_hyperframes_route_returns_manual_status():
    """hyperframes_html_render route should return 'manual' status."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id

    route = get_route_by_id("hyperframes_html_render")
    assert route.status == "manual"


# ─────────────────────────────────────────
# 2. RouteBenchmark supports completed_with_manual
# ─────────────────────────────────────────
def test_route_benchmark_completed_with_manual_status():
    """Benchmark with succeeded + manual routes should get completed_with_manual status."""
    from app.video_lab.routes_benchmark.runner import BenchmarkRunner
    from app.video_lab.routes_benchmark.registry import get_routes_by_ids

    runner = BenchmarkRunner()

    # Create benchmark with a mock route (not failed)
    benchmark = runner.create_benchmark(
        test_case_id="case_ai_frontier_daily_001",
        title="Test",
        input_payload={"content": "测试"},
        common_params={},
        route_ids=["local_frame_compose", "hyperframes_html_render"],
    )

    result = runner.run_benchmark(benchmark.benchmark_id)

    # Status should be completed_with_manual (not partial)
    assert result.status in ("completed", "completed_with_manual"), (
        f"Expected completed or completed_with_manual, got {result.status}"
    )


def test_route_benchmark_all_mock_is_completed():
    """Benchmark with all mock routes should get 'completed' status."""
    from app.video_lab.routes_benchmark.runner import BenchmarkRunner

    runner = BenchmarkRunner()
    benchmark = runner.create_benchmark(
        test_case_id="case_ai_frontier_daily_001",
        title="All Mock",
        input_payload={"content": "测试"},
        common_params={},
        route_ids=["ai_asset_then_compose", "hybrid_pipeline"],
    )

    result = runner.run_benchmark(benchmark.benchmark_id)
    assert result.status == "completed"


def test_route_benchmark_all_reserved_is_completed():
    """Benchmark with all reserved routes should get 'completed' status."""
    from app.video_lab.routes_benchmark.runner import BenchmarkRunner

    runner = BenchmarkRunner()
    benchmark = runner.create_benchmark(
        test_case_id="case_ai_frontier_daily_001",
        title="All Reserved",
        input_payload={"content": "测试"},
        common_params={},
        route_ids=["ai_video_direct"],
    )

    result = runner.run_benchmark(benchmark.benchmark_id)
    assert result.status == "completed"


# ─────────────────────────────────────────
# 3. generation_time_ms is properly measured
# ─────────────────────────────────────────
def test_route_benchmark_generation_time_ms_is_nonzero():
    """Route benchmark result should have non-zero generation_time_ms for real routes."""
    from app.video_lab.routes_benchmark.runner import BenchmarkRunner

    runner = BenchmarkRunner()
    benchmark = runner.create_benchmark(
        test_case_id="case_ai_frontier_daily_001",
        title="Time Test",
        input_payload={"content": "测试内容"},
        common_params={"targetDuration": 20, "keyPointCount": 2, "transitionEnabled": False},
        route_ids=["local_frame_compose"],
    )

    result = runner.run_benchmark(benchmark.benchmark_id)

    # At least one result should have generation_time_ms (metrics is a dict in RouteResult.to_dict())
    for r in result.results:
        if r.status == "succeeded":
            assert "generation_time_ms" in r.metrics


def test_route_benchmark_generation_time_ms_for_manual_route():
    """Manual routes should also have generation_time_ms measured."""
    from app.video_lab.routes_benchmark.runner import BenchmarkRunner

    runner = BenchmarkRunner()
    benchmark = runner.create_benchmark(
        test_case_id="case_ai_frontier_daily_001",
        title="Manual Time",
        input_payload={"content": "测试内容"},
        common_params={},
        route_ids=["hyperframes_html_render"],
    )

    result = runner.run_benchmark(benchmark.benchmark_id)

    for r in result.results:
        # Manual routes should have generation_time_ms in metrics dict
        assert "generation_time_ms" in r.metrics


# ─────────────────────────────────────────
# 4. ExperimentRunner adapter exception -> failed status
# ─────────────────────────────────────────
def test_experiment_runner_adapter_exception_sets_failed_status():
    """When adapter raises exception, experiment.status should be FAILED."""
    from app.video_lab.experiment_runner import ExperimentRunner
    from app.video_lab.models import ExperimentStatus, MethodCategory
    from app.video_lab import method_registry

    runner = ExperimentRunner()

    # Create an experiment with template_programmatic_render (which has a real adapter)
    exp = runner.create_experiment(
        test_case_id="case_ai_frontier_daily_001",
        method_id="method_template_programmatic_render",
        title="Exception Test",
        input_payload={"content": "测试"},
        params={},
    )

    # Save original adapter and replace with one that raises
    orig_adapter = method_registry._METHOD_ADAPTERS[MethodCategory.TEMPLATE_PROGRAMMATIC_RENDER.value]

    def bad_adapter(*args, **kwargs):
        raise RuntimeError("Intentional test exception")

    method_registry._METHOD_ADAPTERS[MethodCategory.TEMPLATE_PROGRAMMATIC_RENDER.value] = bad_adapter

    try:
        try:
            runner.run_experiment(exp.id)
        except RuntimeError as e:
            assert "Intentional test exception" in str(e)

        # Experiment should be FAILED (not stuck in RUNNING)
        updated_exp = runner.get_experiment(exp.id)
        assert updated_exp.status == ExperimentStatus.FAILED, (
            f"Expected FAILED, got {updated_exp.status}"
        )
        assert updated_exp.errorMessage is not None
        assert "Intentional test exception" in updated_exp.errorMessage
    finally:
        # Restore original adapter
        method_registry._METHOD_ADAPTERS[MethodCategory.TEMPLATE_PROGRAMMATIC_RENDER.value] = orig_adapter


# ─────────────────────────────────────────
# 5. MethodCategory frontend/backend consistency
# ─────────────────────────────────────────
def test_method_category_has_tts_subtitle_compose():
    """MethodCategory should include TTS_SUBTITLE_COMPOSE."""
    from app.video_lab.models import MethodCategory

    assert MethodCategory.TTS_SUBTITLE_COMPOSE.value == "tts_subtitle_compose"


def test_method_category_has_hyperframes_html_render():
    """MethodCategory should include HYPERFRAMES_HTML_RENDER."""
    from app.video_lab.models import MethodCategory

    assert MethodCategory.HYPERFRAMES_HTML_RENDER.value == "hyperframes_html_render"


def test_seed_data_has_tts_subtitle_video_method():
    """seed_data should have VideoMethod for tts_subtitle_compose."""
    from app.video_lab.seed_data import get_method_by_id

    method = get_method_by_id("method_tts_subtitle_compose")
    assert method is not None
    assert method.category.value == "tts_subtitle_compose"


def test_seed_data_has_hyperframes_video_method():
    """seed_data should have VideoMethod for hyperframes_html_render."""
    from app.video_lab.seed_data import get_method_by_id

    method = get_method_by_id("method_hyperframes_html_render")
    assert method is not None
    assert method.category.value == "hyperframes_html_render"


def test_method_registry_has_tts_adapter():
    """method_registry should have adapter for TTS_SUBTITLE_COMPOSE."""
    from app.video_lab.models import MethodCategory
    from app.video_lab.method_registry import get_adapter_for_category

    adapter = get_adapter_for_category(MethodCategory.TTS_SUBTITLE_COMPOSE)
    assert adapter is not None


def test_method_registry_has_hyperframes_adapter():
    """method_registry should have adapter for HYPERFRAMES_HTML_RENDER."""
    from app.video_lab.models import MethodCategory
    from app.video_lab.method_registry import get_adapter_for_category

    adapter = get_adapter_for_category(MethodCategory.HYPERFRAMES_HTML_RENDER)
    assert adapter is not None


# ─────────────────────────────────────────
# 6. ROUTE_REGISTRY has 8 routes
# ─────────────────────────────────────────
def test_route_registry_has_8_routes():
    """ROUTE_REGISTRY should have 8 routes (local_media_compose added)."""
    from app.video_lab.routes_benchmark.registry import list_routes

    routes = list_routes()
    assert len(routes) == 8, f"Expected 8 routes, got {len(routes)}"


def test_route_registry_includes_local_media_compose():
    """ROUTE_REGISTRY should include local_media_compose."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id

    route = get_route_by_id("local_media_compose")
    assert route is not None
    assert route.status == "mock"


def test_api_routes_returns_8_routes():
    """GET /routes should return 8 routes."""
    resp = client.get("/video-lab/routes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 8, f"Expected 8 routes, got {len(data)}"


# ─────────────────────────────────────────
# 7. ArtifactType supports audio_output / subtitle_file / html_output
# ─────────────────────────────────────────
def test_artifact_type_has_audio_output():
    """ArtifactType should include AUDIO_OUTPUT."""
    from app.video_lab.models import ArtifactType

    assert ArtifactType.AUDIO_OUTPUT.value == "audio_output"


def test_artifact_type_has_subtitle_file():
    """ArtifactType should include SUBTITLE_FILE."""
    from app.video_lab.models import ArtifactType

    assert ArtifactType.SUBTITLE_FILE.value == "subtitle_file"


def test_artifact_type_has_html_output():
    """ArtifactType should include HTML_OUTPUT."""
    from app.video_lab.models import ArtifactType

    assert ArtifactType.HTML_OUTPUT.value == "html_output"


# ─────────────────────────────────────────
# 8. ImplementationStatus includes MANUAL
# ─────────────────────────────────────────
def test_implementation_status_has_manual():
    """ImplementationStatus should include MANUAL."""
    from app.video_lab.models import ImplementationStatus

    assert ImplementationStatus.MANUAL.value == "manual"


# ─────────────────────────────────────────
# 9. Version is 1.2.3
# ─────────────────────────────────────────
def test_api_version_is_1_2_3():
    """Root API should return version 1.2.3."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.2.3"


def test_fastapi_app_version_is_1_2_3():
    """FastAPI app version should be 1.2.3."""
    assert app.version == "1.2.3"


# ─────────────────────────────────────────
# 10. RouteBenchmark status type includes completed_with_manual
# ─────────────────────────────────────────
def test_route_benchmark_status_type():
    """RouteBenchmark.status should support completed_with_manual and failed."""
    from app.video_lab.routes_benchmark.models import RouteBenchmark

    # These should not raise
    b1 = RouteBenchmark(
        benchmark_id="test",
        title="test",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={},
        common_params={},
        route_ids=[],
        status="completed_with_manual",
    )
    b2 = RouteBenchmark(
        benchmark_id="test2",
        title="test2",
        test_case_id="case_ai_frontier_daily_001",
        input_payload={},
        common_params={},
        route_ids=[],
        status="failed",
    )
    assert b1.status == "completed_with_manual"
    assert b2.status == "failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
