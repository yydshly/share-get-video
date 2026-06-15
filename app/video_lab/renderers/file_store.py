"""
File Store - Manages runtime output directories for experiments.
Runtime paths are configured in app.video_lab.config.
"""

import json
from pathlib import Path

from app.video_lab.config import VIDEO_LAB_EXPERIMENTS_DIR as RUNTIME_BASE
from app.video_lab.config import PUBLIC_RUNTIME_URL_PREFIX


def get_experiment_dir(experiment_id: str) -> Path:
    """Get or create experiment output directory"""
    exp_dir = RUNTIME_BASE / experiment_id
    frames_dir = exp_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    return exp_dir


def get_frames_dir(experiment_id: str) -> Path:
    """Get frames directory for an experiment"""
    return get_experiment_dir(experiment_id) / "frames"


def ensure_runtime_exists() -> None:
    """Ensure runtime base directory exists"""
    RUNTIME_BASE.mkdir(parents=True, exist_ok=True)


def path_to_url(file_path: Path | str) -> str:
    """
    Convert filesystem path to a URL-compatible path under PUBLIC_RUNTIME_URL_PREFIX.

    Handles:
    - POSIX paths: runtime/video_lab/experiments/exp_abc/output.mp4
    - Windows paths: runtime\\video_lab\\experiments\\exp_abc\\output.mp4
    - Absolute paths containing the runtime marker
    """
    path = Path(file_path)
    path_str = path.as_posix()

    prefix = PUBLIC_RUNTIME_URL_PREFIX.rstrip("/")

    # If already under runtime/, keep the full relative path from runtime/.
    if path_str.startswith("runtime/"):
        return f"{prefix}/{path_str}"

    # Normalize Windows backslashes and look for /runtime/ marker.
    normalized = path_str.replace("\\", "/")
    runtime_marker = "/runtime/"
    if runtime_marker in normalized:
        return f"{prefix}/" + normalized.split(runtime_marker, 1)[1]

    # Fallback: strip leading slashes and use basename under the prefix.
    return f"{prefix}/" + normalized.lstrip("/")


def write_manifest(experiment_id: str, manifest: dict) -> Path:
    """Write manifest.json to experiment directory"""
    exp_dir = get_experiment_dir(experiment_id)
    manifest_path = exp_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest_path


def read_manifest(experiment_id: str) -> dict | None:
    """Read manifest.json from experiment directory"""
    manifest_path = get_experiment_dir(experiment_id) / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def cleanup_experiment_runtime(experiment_id: str) -> bool:
    """
    Remove an experiment's runtime directory.
    Returns True if removed, False if it did not exist.
    Does NOT create the directory if it is missing.
    """
    import shutil

    exp_dir = RUNTIME_BASE / experiment_id
    if not exp_dir.exists():
        return False

    shutil.rmtree(exp_dir)
    return True
