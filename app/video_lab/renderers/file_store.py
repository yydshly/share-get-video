"""
File Store - Manages runtime output directories for experiments
"""

import json
from pathlib import Path


RUNTIME_BASE = Path("runtime/video_lab/experiments")


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
    """Convert filesystem path to URL-compatible path"""
    path_str = str(file_path)
    path_str = path_str.replace("\\", "/")
    if str(RUNTIME_BASE) in path_str:
        path_str = path_str.split(str(RUNTIME_BASE))[-1]
    if path_str.startswith("/"):
        path_str = path_str[1:]
    return f"/runtime/{path_str}"


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
