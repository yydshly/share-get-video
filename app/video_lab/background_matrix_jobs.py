"""Background jobs for the long-running Remotion background matrix."""

import threading
import time
import uuid
from copy import deepcopy
from types import SimpleNamespace
from typing import Any

from app.video_lab.services.style_family_service import (
    MAX_MATRIX_ITEMS,
    VALID_BACKGROUND_PRESETS,
    VALID_MATRIX_FAMILIES,
    run_background_variant_matrix,
)


_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _snapshot(job_id: str) -> dict[str, Any] | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return deepcopy(job) if job is not None else None


def create_background_matrix_job(request: Any) -> dict[str, Any]:
    """Start a matrix render in a daemon thread and return immediately."""
    matrix = dict(request.matrix or {})
    families = [
        family
        for family in matrix.get("families", VALID_MATRIX_FAMILIES)
        if family in VALID_MATRIX_FAMILIES
    ]
    backgrounds = [
        background
        for background in matrix.get("backgroundPresets", VALID_BACKGROUND_PRESETS)
        if background in VALID_BACKGROUND_PRESETS
    ]
    if not families:
        raise ValueError(f"families filter resulted in empty set. Allowed values: {VALID_MATRIX_FAMILIES}")
    if not backgrounds:
        raise ValueError(
            "backgroundPresets filter resulted in empty set. "
            f"Allowed values: {VALID_BACKGROUND_PRESETS}"
        )

    work_items = [(family, background) for family in families for background in backgrounds]
    if len(work_items) > MAX_MATRIX_ITEMS:
        raise ValueError(
            f"background matrix is limited to {MAX_MATRIX_ITEMS} clips per request, "
            f"but {len(work_items)} requested."
        )
    job_id = f"background_matrix_{uuid.uuid4().hex[:12]}"
    job = {
        "jobId": job_id,
        "status": "pending",
        "total": len(work_items),
        "completed": 0,
        "items": [],
        "totalElapsedMs": 0,
        "error": "",
    }
    with _jobs_lock:
        _jobs[job_id] = job

    threading.Thread(
        target=_run_background_matrix_job,
        args=(job_id, request.content, dict(request.params or {}), work_items),
        daemon=True,
    ).start()
    return deepcopy(job)


def get_background_matrix_job(job_id: str) -> dict[str, Any] | None:
    return _snapshot(job_id)


def _run_background_matrix_job(
    job_id: str,
    content: str,
    params: dict[str, Any],
    work_items: list[tuple[str, str]],
) -> None:
    started_at = time.monotonic()
    with _jobs_lock:
        _jobs[job_id]["status"] = "running"

    try:
        for family, background in work_items:
            request = SimpleNamespace(
                content=content,
                params=dict(params),
                matrix={"families": [family], "backgroundPresets": [background]},
            )
            result = run_background_variant_matrix(request)
            with _jobs_lock:
                job = _jobs[job_id]
                job["items"].extend(result["items"])
                job["completed"] = len(job["items"])
                job["totalElapsedMs"] = int((time.monotonic() - started_at) * 1000)

        with _jobs_lock:
            _jobs[job_id]["status"] = "completed"
            _jobs[job_id]["totalElapsedMs"] = int((time.monotonic() - started_at) * 1000)
    except Exception as exc:
        with _jobs_lock:
            job = _jobs[job_id]
            job["status"] = "failed"
            job["error"] = f"{type(exc).__name__}: {exc}"
            job["totalElapsedMs"] = int((time.monotonic() - started_at) * 1000)
