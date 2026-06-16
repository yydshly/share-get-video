"""
experiment_manifest.py - Unified experiment manifest for Video Lab.

Every Video Lab experiment (preview, compose, sweep, probe) writes a
manifest.json to RUNTIME_DIR/video_lab/experiments/{experimentId}/.

The manifest has a stable schema version and is written on both success
and failure so operators can always inspect what happened.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import get_experiment_dir
from app.video_lab.path_contract import path_to_runtime_url

SCHEMA_VERSION = "video-lab-experiment-v1"


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def build_experiment_manifest(
    *,
    experiment_id: str,
    run_id: str,
    mode: str,
    route_id: str,
    status: str,
    input_data: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
    props: dict[str, Any] | None = None,
    timeline: dict[str, Any] | None = None,
    artifacts: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    logs: list[str] | None = None,
    warnings: list[str] | None = None,
    error: dict[str, Any] | None = None,
    raw_output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a complete experiment manifest dict.

    Args:
        experiment_id: stable experiment identity
        run_id: unique per-execution identity
        mode: "preview" | "compose" | "sweep" | "probe"
        route_id: "template_programmatic_render" | "ai_asset_then_compose" | "local_frame_compose"
        status: "success" | "failed"
        input_data: raw input snapshot
        plan: LLM-generated plan (voiceover plan, content structure, etc.)
        props: Remotion props or frame render params
        timeline: segment timing information
        artifacts: output URLs (cover, video, audio, subtitles, manifest)
        quality: quality scores (if available)
        logs: execution log lines
        warnings: non-fatal warnings
        error: structured error (from errors.py) — only set when status="failed"
        raw_output: raw output from each step

    Returns:
        Complete manifest dict with schemaVersion.
    """
    return {
        "schemaVersion": SCHEMA_VERSION,
        "experimentId": experiment_id,
        "runId": run_id,
        "mode": mode,
        "routeId": route_id,
        "status": status,
        "input": input_data or {},
        "plan": plan or {},
        "props": props or {},
        "timeline": timeline or {},
        "artifacts": artifacts or {
            "cover": None,
            "frames": [],
            "silentVideo": None,
            "audio": None,
            "subtitles": None,
            "finalVideo": None,
            "manifest": None,
        },
        "quality": quality or {},
        "logs": logs or [],
        "warnings": warnings or [],
        "error": error,
        "rawOutput": raw_output or {},
        "createdAt": utc_now_iso(),
    }


def write_experiment_manifest(
    experiment_id: str,
    manifest: dict[str, Any],
) -> dict[str, str]:
    """
    Write manifest JSON to the experiment directory and return path + URL.

    Always writes to: RUNTIME_DIR/video_lab/experiments/{experimentId}/manifest.json
    The manifestUrl is generated via path_contract so it respects PUBLIC_RUNTIME_URL_PREFIX.

    Args:
        experiment_id: experiment identity (determines directory)
        manifest: manifest dict from build_experiment_manifest()

    Returns:
        {"path": "...", "url": "..."}
    """
    exp_dir = get_experiment_dir(experiment_id)
    manifest_path = exp_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return {
        "path": str(manifest_path),
        "url": path_to_runtime_url(manifest_path),
    }
