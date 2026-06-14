"""
Routes Benchmark - Data models for multi-route benchmarking
V0.3.0: Multi-route horizontal verification framework
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RouteMetrics:
    """Metrics for a single route result."""
    generation_time_ms: int = 0
    estimated_cost: str = "unknown"
    stability: str = "unknown"
    quality_ceiling: str = "unknown"


@dataclass
class RouteResult:
    """Result from a single route execution."""
    route_id: str
    status: str  # "succeeded" | "failed" | "mock" | "reserved"
    video_url: str = ""
    cover_url: str = ""
    manifest_url: str = ""
    summary: str = ""
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteBenchmarkRequest:
    """Request to run a benchmark across multiple routes."""
    test_case_id: str
    title: str
    input_payload: dict[str, Any]
    common_params: dict[str, Any] = field(default_factory=dict)
    route_ids: list[str] = field(default_factory=list)


@dataclass
class RouteBenchmark:
    """A benchmark run across multiple routes."""
    benchmark_id: str
    title: str
    test_case_id: str
    input_payload: dict[str, Any]
    common_params: dict[str, Any]
    route_ids: list[str]
    status: str = "pending"  # "pending" | "running" | "completed" | "partial"
    results: list[RouteResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    elapsed_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmarkId": self.benchmark_id,
            "title": self.title,
            "testCaseId": self.test_case_id,
            "inputPayload": self.input_payload,
            "commonParams": self.common_params,
            "routeIds": self.route_ids,
            "status": self.status,
            "results": [
                {
                    "routeId": r.route_id,
                    "status": r.status,
                    "videoUrl": r.video_url,
                    "coverUrl": r.cover_url,
                    "manifestUrl": r.manifest_url,
                    "summary": r.summary,
                    "artifacts": r.artifacts,
                    "metrics": r.metrics,
                    "warnings": r.warnings,
                }
                for r in self.results
            ],
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "elapsedMs": self.elapsed_ms,
        }
