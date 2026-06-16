"""
JobRun v1 contract — sync task status abstraction for Video Lab.

V1.0.4: Lightweight status tracking for synchronous long-running tasks
(visual-compose, style-sweep, technique-probe). NOT a real async queue.

Fields:
  - jobId / runId / experimentId / mode / routeId
  - status: pending | running | succeeded | failed | canceled
  - stage: created | planning | tts | subtitle | visual_render | compose | manifest | completed | failed
  - progress: 0-100
  - stageLabel: human-readable stage description
  - logs / artifacts / error
  - createdAt / updatedAt (ISO 8601 UTC)

Design constraints:
  - No FastAPI dependency
  - No database dependency
  - No filesystem write
  - Pure Python, fully unit-testable
  - All state transitions are explicit (mark_running / advance / mark_succeeded / mark_failed)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ─── Status enums ──────────────────────────────────────────────────────────
JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELED = "canceled"

JOB_STATUSES = {
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    JOB_STATUS_FAILED,
    JOB_STATUS_CANCELED,
}

# ─── Stage enums ──────────────────────────────────────────────────────────
JOB_STAGE_CREATED = "created"
JOB_STAGE_PLANNING = "planning"
JOB_STAGE_TTS = "tts"
JOB_STAGE_SUBTITLE = "subtitle"
JOB_STAGE_VISUAL_RENDER = "visual_render"
JOB_STAGE_COMPOSE = "compose"
JOB_STAGE_MANIFEST = "manifest"
JOB_STAGE_COMPLETED = "completed"
JOB_STAGE_FAILED = "failed"

JOB_STAGES = {
    JOB_STAGE_CREATED,
    JOB_STAGE_PLANNING,
    JOB_STAGE_TTS,
    JOB_STAGE_SUBTITLE,
    JOB_STAGE_VISUAL_RENDER,
    JOB_STAGE_COMPOSE,
    JOB_STAGE_MANIFEST,
    JOB_STAGE_COMPLETED,
    JOB_STAGE_FAILED,
}

# ─── Human-readable stage labels ──────────────────────────────────────────
STAGE_LABELS: dict[str, str] = {
    JOB_STAGE_CREATED: "已创建",
    JOB_STAGE_PLANNING: "规划生成方案",
    JOB_STAGE_TTS: "合成语音",
    JOB_STAGE_SUBTITLE: "生成字幕",
    JOB_STAGE_VISUAL_RENDER: "渲染画面",
    JOB_STAGE_COMPOSE: "合成视频",
    JOB_STAGE_MANIFEST: "写入清单",
    JOB_STAGE_COMPLETED: "已完成",
    JOB_STAGE_FAILED: "失败",
}

STATUS_LABELS: dict[str, str] = {
    JOB_STATUS_PENDING: "等待中",
    JOB_STATUS_RUNNING: "进行中",
    JOB_STATUS_SUCCEEDED: "成功",
    JOB_STATUS_FAILED: "失败",
    JOB_STATUS_CANCELED: "已取消",
}


def new_job_id() -> str:
    """Generate a new job ID."""
    return f"job_{uuid.uuid4().hex[:12]}"


def _utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class JobRun:
    """
    V1.0.4 JobRun status contract.

    Tracks the lifecycle of a synchronous long-running Video Lab task.
    Each service creates a JobRun at start, advances stages, and
    includes it in the final response (response.jobRun).
    """

    job_id: str
    run_id: str
    experiment_id: str
    mode: str
    route_id: str
    status: str = JOB_STATUS_PENDING
    stage: str = JOB_STAGE_CREATED
    progress: int = 0
    stage_label: str = field(default_factory=lambda: STAGE_LABELS[JOB_STAGE_CREATED])
    logs: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)

    def _touch(self) -> None:
        """Update updated_at timestamp."""
        self.updated_at = _utc_now_iso()

    def mark_running(self, stage: str = JOB_STAGE_PLANNING, progress: int = 10) -> None:
        """Transition to running state at the given stage."""
        if stage not in JOB_STAGES:
            raise ValueError(f"unknown stage: {stage}")
        self.status = JOB_STATUS_RUNNING
        self.stage = stage
        self.progress = max(0, min(100, progress))
        self.stage_label = STAGE_LABELS.get(stage, stage)
        self._touch()

    def advance(self, stage: str, progress: int) -> None:
        """Advance to the next stage without changing status (must be running)."""
        if stage not in JOB_STAGES:
            raise ValueError(f"unknown stage: {stage}")
        if self.status not in (JOB_STATUS_PENDING, JOB_STATUS_RUNNING):
            raise ValueError(
                f"cannot advance from terminal status: {self.status}"
            )
        self.stage = stage
        self.progress = max(0, min(100, progress))
        self.stage_label = STAGE_LABELS.get(stage, stage)
        if self.status == JOB_STATUS_PENDING:
            self.status = JOB_STATUS_RUNNING
        self._touch()

    def mark_succeeded(self, stage: str = JOB_STAGE_COMPLETED, progress: int = 100) -> None:
        """Mark the job as succeeded."""
        if stage not in JOB_STAGES:
            raise ValueError(f"unknown stage: {stage}")
        self.status = JOB_STATUS_SUCCEEDED
        self.stage = stage
        self.progress = max(0, min(100, progress))
        self.stage_label = STAGE_LABELS.get(stage, stage)
        self._touch()

    def mark_failed(
        self,
        error: dict[str, Any] | None = None,
        stage: str = JOB_STAGE_FAILED,
        progress: int = 100,
    ) -> None:
        """Mark the job as failed."""
        if stage not in JOB_STAGES:
            raise ValueError(f"unknown stage: {stage}")
        self.status = JOB_STATUS_FAILED
        self.stage = stage
        self.progress = max(0, min(100, progress))
        self.stage_label = STAGE_LABELS.get(stage, stage)
        self.error = error
        self._touch()

    def log(self, line: str) -> None:
        """Append a log line to the job run."""
        if line:
            self.logs.append(line)
            self._touch()

    def set_artifact(self, key: str, value: Any) -> None:
        """Set an artifact entry (e.g. 'finalVideoUrl', 'manifestUrl')."""
        self.artifacts[key] = value
        self._touch()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for response inclusion."""
        return {
            "jobId": self.job_id,
            "runId": self.run_id,
            "experimentId": self.experiment_id,
            "mode": self.mode,
            "routeId": self.route_id,
            "status": self.status,
            "stage": self.stage,
            "progress": self.progress,
            "stageLabel": self.stage_label,
            "logs": list(self.logs),
            "artifacts": dict(self.artifacts),
            "error": self.error,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }
