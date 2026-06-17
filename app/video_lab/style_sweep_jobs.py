"""
style_sweep_jobs — async job runner for Style Sweep with progress reporting.

POST /style-sweep-jobs creates a job and returns jobId immediately.
GET /style-sweep-jobs/{job_id} returns current progress.
The actual per-style rendering runs in a background thread.
Job state is persisted to JSON files under runtime/video_lab/style_sweep/jobs/.
"""

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────

_RUNTIME_DIR: Path | None = None


def _get_jobs_dir() -> Path:
    global _RUNTIME_DIR
    if _RUNTIME_DIR is None:
        _RUNTIME_DIR = Path(__file__).parent.parent / "runtime" / "video_lab" / "style_sweep" / "jobs"
    _RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return _RUNTIME_DIR


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class StyleResultEntry:
    styleId: str
    styleName: str
    description: str
    tags: list[str]
    result: dict[str, Any] = field(default_factory=dict)


@dataclass
class SweepJob:
    jobId: str
    status: str  # pending | running | completed | failed | cancelled
    routeId: str
    routeName: str
    total: int
    completed: int = 0
    succeeded: int = 0
    failed: int = 0
    currentStyleId: str = ""
    currentStyleName: str = ""
    results: list[StyleResultEntry] = field(default_factory=list)
    startedAt: str = ""
    updatedAt: str = ""
    finishedAt: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "SweepJob":
        # Reconstitute StyleResultEntry objects from plain dicts
        if "results" in d and d["results"]:
            d["results"] = [
                StyleResultEntry(**r) if isinstance(r, dict) else r
                for r in d["results"]
            ]
        return SweepJob(**d)


# ─── Job persistence ─────────────────────────────────────────────────────────

def _job_path(job_id: str) -> Path:
    return _get_jobs_dir() / f"{job_id}.json"


def _save_job(job: SweepJob) -> None:
    path = _job_path(job.jobId)
    path.write_text(json.dumps(job.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def _load_job(job_id: str) -> SweepJob | None:
    path = _job_path(job_id)
    if not path.exists():
        return None
    try:
        return SweepJob.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


# ─── Public API ────────────────────────────────────────────────────────────────

def create_sweep_job(
    content: str,
    route_id: str,
    route_name: str,
    total: int,
    render_fn: Callable[[str, str, dict], dict[str, Any]],
    styles: list[dict[str, Any]],
) -> SweepJob:
    """Create a new sweep job, persist it, and start background execution."""
    job_id = f"sweep_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    job = SweepJob(
        jobId=job_id,
        status="pending",
        routeId=route_id,
        routeName=route_name,
        total=total,
        startedAt=now,
        updatedAt=now,
    )
    _save_job(job)

    # Start background execution — does NOT block the caller
    thread = threading.Thread(
        target=_run_job_background,
        args=(job_id, content, route_id, render_fn, styles),
        daemon=True,
    )
    thread.start()

    return job


def get_sweep_job(job_id: str) -> SweepJob | None:
    """Load job state from disk. Returns None if not found."""
    return _load_job(job_id)


# ─── Background worker ───────────────────────────────────────────────────────

def _run_job_background(
    job_id: str,
    content: str,
    route_id: str,
    render_fn: Callable[[str, str, dict], dict[str, Any]],
    styles: list[dict[str, Any]],
) -> None:
    """Run each style sequentially, updating job state after each completion."""
    job = _load_job(job_id)
    if job is None:
        logger.error("[style_sweep_jobs] Job %s not found", job_id)
        return

    job.status = "running"
    job.updatedAt = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _save_job(job)

    for idx, st in enumerate(styles):
        # Reload latest job state (in case of concurrent reads)
        job = _load_job(job_id) or job
        style_id = st.get("style_id", "")
        style_name = st.get("style_name", "")
        merged = {**({"content": content} if "content" not in route_id else {}), **st.get("params", {})}
        # For remotion route, content is a separate field; for others it's part of params
        if "content" in st.get("params", {}):
            merged = {**merged, "content": content}
        elif "content" not in merged:
            merged["content"] = content

        # Update current style tracking
        job.currentStyleId = style_id
        job.currentStyleName = style_name
        job.updatedAt = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _save_job(job)

        # Render this single style
        try:
            result = render_fn(content, route_id, merged)
        except Exception as e:
            result = {
                "status": "failed",
                "failedReason": f"render error: {e}",
                "finalVideoUrl": "",
                "coverUrl": "",
                "audioUrl": "",
                "srtUrl": "",
                "manifestUrl": "",
                "warnings": [],
                "steps": [],
                "params": merged,
            }

        entry = StyleResultEntry(
            styleId=style_id,
            styleName=style_name,
            description=st.get("description", ""),
            tags=st.get("tags", []),
            result=result,
        )

        # Reload and update
        job = _load_job(job_id) or job
        job.results.append(entry)
        job.completed = idx + 1
        if result.get("status") == "succeeded":
            job.succeeded += 1
        else:
            job.failed += 1
        job.updatedAt = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _save_job(job)

    # Finalize
    job = _load_job(job_id) or job
    job.status = "completed"
    job.currentStyleId = ""
    job.currentStyleName = ""
    job.finishedAt = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    job.updatedAt = job.finishedAt
    _save_job(job)
    logger.info("[style_sweep_jobs] Job %s completed: %d/%d succeeded", job_id, job.succeeded, job.total)
