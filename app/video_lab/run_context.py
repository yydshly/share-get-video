"""
run_context.py - Run context for every Video Lab execution.

Every clip-preview, visual-compose, style-sweep, and technique-probe run
gets a stable RunContext with a runId, experimentId, mode, routeId,
logs, warnings, and artifact slots.

This gives every execution a unique identity that flows through all
subsequent manifest and contract structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def new_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def new_experiment_id(prefix: str = "exp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@dataclass
class RunContext:
    """
    Execution context for a single Video Lab run.

    Fields:
        mode: execution mode — "preview" | "compose" | "sweep" | "probe"
        route_id: which visual route — "template_programmatic_render" | "ai_asset_then_compose" | "local_frame_compose"
        experiment_id: stable experiment identity (persists across runs)
        run_id: unique per-execution identity
        status: "running" | "success" | "failed"
        input_snapshot: snapshot of input params
        render_params: merged render parameters
        artifacts: accumulated output artifact URLs
        logs: ordered execution log lines
        warnings: non-fatal warnings
        created_at / updated_at: ISO timestamps
    """

    mode: str
    route_id: str
    experiment_id: str = ""
    run_id: str = ""
    status: str = "running"
    input_snapshot: dict[str, Any] = field(default_factory=dict)
    render_params: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = new_run_id()
        if not self.experiment_id:
            self.experiment_id = new_experiment_id()

    def log(self, line: str) -> None:
        self.logs.append(line)

    def warn(self, line: str) -> None:
        self.warnings.append(line)

    def mark_success(self) -> None:
        self.status = "success"
        self.updated_at = utc_now_iso()

    def mark_failed(self) -> None:
        self.status = "failed"
        self.updated_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": "video-lab-run-context-v1",
            "runId": self.run_id,
            "experimentId": self.experiment_id,
            "mode": self.mode,
            "routeId": self.route_id,
            "status": self.status,
            "inputSnapshot": self.input_snapshot,
            "renderParams": self.render_params,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "warnings": self.warnings,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def to_response_base(self) -> dict[str, Any]:
        """Shared fields used in both success and failure API responses."""
        return {
            "runId": self.run_id,
            "experimentId": self.experiment_id,
            "mode": self.mode,
            "routeId": self.route_id,
            "status": self.status,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "warnings": self.warnings,
        }
