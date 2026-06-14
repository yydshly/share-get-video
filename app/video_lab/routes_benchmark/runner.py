"""
Routes Benchmark - Runner
V0.3.0: Executes benchmarks across multiple routes
"""

import uuid
from datetime import datetime
from typing import Any

from app.video_lab.routes_benchmark.models import (
    RouteBenchmark,
    RouteResult,
    RouteMetrics,
)
from app.video_lab.routes_benchmark.registry import (
    get_route_by_id,
    get_routes_by_ids,
)
from app.video_lab.adapters.local_frame_compose import run_local_frame_compose
from app.video_lab.adapters.remotion_template import run_remotion_template
from app.video_lab.adapters.hyperframes_html_render import run_hyperframes_html_render
from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
from app.video_lab.adapters.local_media_compose import run_local_media_compose
from app.video_lab.adapters.ai_asset_then_compose import run_ai_asset_then_compose
from app.video_lab.adapters.ai_video_direct import run_ai_video_direct
from app.video_lab.adapters.hybrid_pipeline import run_hybrid_pipeline


# Adapter mapping
_ADAPTERS: dict[str, Any] = {
    "local_frame_compose": run_local_frame_compose,
    "template_programmatic_render": run_remotion_template,
    "hyperframes_html_render": run_hyperframes_html_render,
    "tts_subtitle_compose": run_tts_subtitle_compose,
    "local_media_compose": run_local_media_compose,
    "ai_asset_then_compose": run_ai_asset_then_compose,
    "ai_video_direct": run_ai_video_direct,
    "hybrid_pipeline": run_hybrid_pipeline,
}


class BenchmarkRunner:
    """In-memory benchmark runner."""

    def __init__(self):
        self._benchmarks: dict[str, RouteBenchmark] = {}

    def create_benchmark(
        self,
        test_case_id: str,
        title: str,
        input_payload: dict,
        common_params: dict,
        route_ids: list[str],
    ) -> RouteBenchmark:
        benchmark_id = f"bench_{uuid.uuid4().hex[:12]}"
        benchmark = RouteBenchmark(
            benchmark_id=benchmark_id,
            title=title,
            test_case_id=test_case_id,
            input_payload=input_payload,
            common_params=common_params,
            route_ids=route_ids,
            status="pending",
        )
        self._benchmarks[benchmark_id] = benchmark
        return benchmark

    def get_benchmark(self, benchmark_id: str) -> RouteBenchmark | None:
        return self._benchmarks.get(benchmark_id)

    def run_benchmark(self, benchmark_id: str) -> RouteBenchmark:
        """Execute a benchmark across all specified routes."""
        benchmark = self._benchmarks.get(benchmark_id)
        if not benchmark:
            raise ValueError(f"Benchmark not found: {benchmark_id}")

        benchmark.status = "running"
        start_time = datetime.utcnow()

        routes_to_run = get_routes_by_ids(benchmark.route_ids)

        for route_def in routes_to_run:
            route_result = self._execute_route(
                route_id=route_def.route_id,
                test_case_id=benchmark.test_case_id,
                input_payload=benchmark.input_payload,
                params=benchmark.common_params,
                route_def=route_def,
            )
            benchmark.results.append(route_result)

        # Determine overall status
        # All succeeded => completed
        if all(r.status == "succeeded" for r in benchmark.results):
            benchmark.status = "completed"
        # All mock/reserved/manual => completed
        elif all(r.status in ("mock", "reserved", "manual") for r in benchmark.results):
            benchmark.status = "completed"
        # succeeded + manual (no failed) => completed_with_manual
        elif all(r.status in ("succeeded", "manual") for r in benchmark.results):
            benchmark.status = "completed_with_manual"
        # Some succeeded + some manual + at least one succeeded => completed_with_manual
        elif any(r.status == "succeeded" for r in benchmark.results) and all(r.status in ("succeeded", "manual", "mock", "reserved") for r in benchmark.results):
            benchmark.status = "completed_with_manual"
        # Has failed => partial
        elif any(r.status == "failed" for r in benchmark.results):
            benchmark.status = "partial"
        # All failed => failed
        elif all(r.status == "failed" for r in benchmark.results):
            benchmark.status = "failed"
        else:
            benchmark.status = "partial"

        benchmark.completed_at = datetime.utcnow()
        benchmark.elapsed_ms = int(
            (benchmark.completed_at - start_time).total_seconds() * 1000
        )

        return benchmark

    def _execute_route(
        self,
        route_id: str,
        test_case_id: str,
        input_payload: dict,
        params: dict,
        route_def,  # RouteDefinition
    ) -> RouteResult:
        """Execute a single route."""
        experiment_id = f"bench_{route_id}_{uuid.uuid4().hex[:8]}"
        route_start = datetime.utcnow()

        try:
            if route_def.status == "real" and route_id in _ADAPTERS:
                # Real execution
                adapter = _ADAPTERS[route_id]
                result = adapter(
                    experiment_id=experiment_id,
                    test_case_id=test_case_id,
                    input_payload=input_payload,
                    params=params,
                )

                # Extract video URL and artifacts from result
                video_url = getattr(result, "videoUrl", "") or ""
                cover_url = getattr(result, "coverUrl", "") or ""

                # Find manifest artifact
                manifest_url = ""
                artifacts = []
                for step in getattr(result, "productionSteps", []):
                    for art in getattr(step, "artifacts", []):
                        art_dict = art.to_dict() if hasattr(art, "to_dict") else art
                        artifacts.append(art_dict)
                        if art_dict.get("type") == "manifest":
                            manifest_url = art_dict.get("payload", {}).get("manifestUrl", "")

                route_elapsed_ms = int((datetime.utcnow() - route_start).total_seconds() * 1000)
                return RouteResult(
                    route_id=route_id,
                    status="succeeded" if video_url else "failed",
                    video_url=video_url,
                    cover_url=cover_url,
                    manifest_url=manifest_url,
                    summary=f"Generated video via {route_id}",
                    artifacts=artifacts,
                    metrics=RouteMetrics(
                        generation_time_ms=route_elapsed_ms,
                        estimated_cost="low-medium" if route_id == "local_frame_compose" else ("low-medium" if route_id == "template_programmatic_render" else "unknown"),
                        stability="high" if route_id == "local_frame_compose" else ("medium" if route_id == "template_programmatic_render" else "unknown"),
                        quality_ceiling="high" if route_id == "template_programmatic_render" else "medium",
                    ).__dict__,
                    warnings=_build_warnings(result, video_url),
                    raw_output=getattr(result, "rawOutput", {}) or {},
                )

            elif route_def.status == "manual" and route_id in _ADAPTERS:
                # Manual route - execute adapter, return manual result (no videoUrl expected)
                adapter = _ADAPTERS[route_id]
                result = adapter(
                    experiment_id=experiment_id,
                    test_case_id=test_case_id,
                    input_payload=input_payload,
                    params=params,
                )

                video_url = getattr(result, "videoUrl", "") or ""
                cover_url = getattr(result, "coverUrl", "") or ""

                # Extract manifest artifact for htmlUrl
                manifest_url = ""
                artifacts = []
                for step in getattr(result, "productionSteps", []):
                    for art in getattr(step, "artifacts", []):
                        art_dict = art.to_dict() if hasattr(art, "to_dict") else art
                        artifacts.append(art_dict)
                        if art_dict.get("type") == "manifest":
                            manifest_url = art_dict.get("payload", {}).get("manifestUrl", "")

                route_elapsed_ms = int((datetime.utcnow() - route_start).total_seconds() * 1000)
                # For manual routes, use "manual" status, not succeeded/failed
                return RouteResult(
                    route_id=route_id,
                    status="manual",
                    video_url=video_url,
                    cover_url=cover_url,
                    manifest_url=manifest_url,
                    summary=f"Manual route: {route_def.name} — {route_def.description[:50]}",
                    artifacts=artifacts,
                    metrics=RouteMetrics(
                        generation_time_ms=route_elapsed_ms,
                        estimated_cost="unknown",
                        stability="unknown",
                        quality_ceiling="high",
                    ).__dict__,
                    warnings=_build_warnings(result, video_url),
                    raw_output=getattr(result, "rawOutput", {}) or {},
                )

            elif route_def.status == "mock":
                return self._mock_route(route_id, route_def, experiment_id, params)

            elif route_def.status == "reserved":
                return self._reserved_route(route_id, route_def, experiment_id)

            else:
                route_elapsed_ms = int((datetime.utcnow() - route_start).total_seconds() * 1000)
                return RouteResult(
                    route_id=route_id,
                    status="failed",
                    summary=f"Unknown route status: {route_def.status}",
                )

        except Exception as e:
            route_elapsed_ms = int((datetime.utcnow() - route_start).total_seconds() * 1000)
            return RouteResult(
                route_id=route_id,
                status="failed",
                summary=f"Execution error: {str(e)[:200]}",
                warnings=[str(e)],
            )

    def _mock_route(self, route_id, route_def, experiment_id, params) -> RouteResult:
        """Return mock result for mock routes."""
        return RouteResult(
            route_id=route_id,
            status="mock",
            summary=f"Mock route: {route_def.name} - not yet implemented",
            artifacts=[
                {
                    "type": "route_info",
                    "routeId": route_id,
                    "pipeline": route_def.expected_pipeline,
                    "note": f"{route_def.name} is in mock status. Expected pipeline shown for comparison.",
                }
            ],
            metrics=RouteMetrics(
                estimated_cost="unknown",
                stability="unknown",
                quality_ceiling="unknown",
            ).__dict__,
            warnings=[f"{route_def.name} is mock - no real execution"],
        )

    def _reserved_route(self, route_id, route_def, experiment_id) -> RouteResult:
        """Return reserved result for reserved routes."""
        return RouteResult(
            route_id=route_id,
            status="reserved",
            summary=f"Reserved route: {route_def.name} - {route_def.description}",
            artifacts=[
                {
                    "type": "route_info",
                    "routeId": route_id,
                    "pipeline": route_def.expected_pipeline,
                    "note": f"{route_def.name} is reserved. {route_def.description}",
                }
            ],
            metrics=RouteMetrics(
                estimated_cost="unknown",
                stability="unknown",
                quality_ceiling="unknown",
            ).__dict__,
            warnings=[f"{route_def.name} is reserved - requires future implementation"],
        )


def _build_warnings(result: Any, video_url: str) -> list[str]:
    """
    Build warnings list from a failed route result.

    Preserves FFmpeg/render failure reasons in warnings so the UI can display them.
    Skips generic status warnings for manual routes (manual_completed is expected).
    """
    if video_url:
        return []
    warnings: list[str] = []
    raw = getattr(result, "rawOutput", {}) or {}
    # Skip warnings for manual routes that completed successfully
    if raw.get("status") == "manual_completed":
        return []
    # FFmpeg message
    if raw.get("ffmpegMessage"):
        warnings.append(raw["ffmpegMessage"][:200])
    # Render message
    elif raw.get("renderMessage"):
        warnings.append(raw["renderMessage"][:200])
    # Status (only for genuinely failed routes)
    elif raw.get("status"):
        warnings.append(f"render status: {raw['status']}")
    return warnings


# Singleton instance
_runner: BenchmarkRunner | None = None


def get_runner() -> BenchmarkRunner:
    global _runner
    if _runner is None:
        _runner = BenchmarkRunner()
    return _runner
