"""
File Store - Manages runtime output directories for experiments.
Runtime paths are configured in app.video_lab.config.
"""

import json
from pathlib import Path

from app.video_lab.config import VIDEO_LAB_EXPERIMENTS_DIR as RUNTIME_BASE
from app.video_lab.config import PUBLIC_RUNTIME_URL_PREFIX
from app.video_lab.config import RUNTIME_DIR


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
    Convert a filesystem path to a URL path under PUBLIC_RUNTIME_URL_PREFIX.

    Strategy:
    1. If the resolved path is inside RUNTIME_DIR, use relative_to to get a clean
       path (works even with custom RUNTIME_DIR like D:/video-lab-runtime).
    2. Fallback: strip any existing /runtime/ prefix and rebuild with the
       current PUBLIC_RUNTIME_URL_PREFIX.

    Examples:
      path_to_url("runtime/video_lab/experiments/exp/final.mp4")
        → "/runtime/video_lab/experiments/exp/final.mp4"

      path_to_url("D:/video-lab-runtime/video_lab/experiments/exp/final.mp4")
        → "/runtime/video_lab/experiments/exp/final.mp4"
    """
    path = Path(file_path)
    prefix = PUBLIC_RUNTIME_URL_PREFIX.rstrip("/") or "/runtime"

    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    # 1. If path is inside RUNTIME_DIR, use relative_to for a clean sub-path.
    try:
        rel = resolved.relative_to(RUNTIME_DIR.resolve())
        return f"{prefix}/{rel.as_posix()}"
    except ValueError:
        pass

    # 2. Normalize to forward slashes and strip any existing /runtime/ prefix.
    normalized = resolved.as_posix().replace("\\", "/")

    # Strip /runtime/ if it appears after the mount point
    marker = "/runtime/"
    if marker in normalized:
        return f"{prefix}/" + normalized.split(marker, 1)[1]

    # 3. Fallback: strip leading slashes and put everything under the prefix.
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
