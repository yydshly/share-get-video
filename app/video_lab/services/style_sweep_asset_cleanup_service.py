"""
style_sweep_asset_cleanup_service.py
Stage 3A-4: Dry-run scan for Style Sweep runtime assets.

This module does NOT delete any files. It only scans and reports.
Actual deletion is deferred to Stage 3A-5.

Key concepts:
- referenced_assets: files still protected by Style Gallery sample references
- deletable_assets: unreferenced files old enough to be safely considered for cleanup
- skipped_assets: unreferenced files too new to delete
"""

import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.video_lab.config import RUNTIME_DIR
from app.video_lab.style_gallery import store as sg_store


# ─── Path normalization ────────────────────────────────────────────────────────

# Known top-level runtime directories we care about
RUNTIME_TOP_LEVELS = ("video_lab", "style_gallery", "runtime")


def normalize_asset_ref(value: str) -> str:
    """Normalize an asset reference to a consistent POSIX-style path.

    Handles:
    - runtime/video_lab/...                    → runtime/video_lab/...
    - /runtime/video_lab/...                   → runtime/video_lab/...
    - http://host/runtime/video_lab/...       → runtime/video_lab/...
    - https://host/runtime/video_lab/...       → runtime/video_lab/...
    - D:\\...\\runtime\\video_lab\\...       → runtime/video_lab/...
    - D:/.../runtime/video_lab/...            → runtime/video_lab/...
    - /absolute/path/to/runtime/video_lab/...  → runtime/video_lab/... (strip prefix)

    Returns "" for empty / None values.
    """
    if not value:
        return ""

    # Step 1: strip URL origin
    # matches http://host/path or https://host/path
    stripped = re.sub(r"^https?://[^/]+", "", value, flags=re.IGNORECASE)

    # Step 2: replace backslashes with forward slashes
    stripped = stripped.replace("\\", "/")

    # Step 3: strip leading slashes
    stripped = stripped.lstrip("/")

    # Step 4: extract runtime/video_lab/... or runtime/style_gallery/... part
    # Look for "runtime/" prefix first (special case — maps to runtime/...)
    rt_idx = stripped.find("runtime/")
    if rt_idx != -1:
        result = stripped[rt_idx:]
        return result.rstrip("/")

    # Otherwise look for video_lab/ or style_gallery/ (from project root or absolute)
    for top in ("video_lab", "style_gallery"):
        idx = stripped.find(f"{top}/")
        if idx != -1:
            return stripped[idx:]

    return stripped


# ─── Reference collection ─────────────────────────────────────────────────────

def collect_referenced_assets() -> dict[str, set[str]]:
    """Collect all asset paths referenced by Style Gallery samples.

    Returns
    -------
    dict[str, set[str]]
        normalized_path → set of sample_ids that reference it
    """
    ref_map: dict[str, set[str]] = {}

    def _add(path: str, sample_id: str) -> None:
        if not path:
            return
        norm = normalize_asset_ref(path)
        if not norm:
            return
        ref_map.setdefault(norm, set()).add(sample_id)

    try:
        samples = sg_store.list_samples(limit=10000)
    except Exception:
        # If store is unavailable or empty, return empty map
        return {}

    for sample in samples:
        sid = sample.id

        # output fields
        out = sample.output
        _add(out.path, sid)
        _add(out.poster, sid)
        _add(out.audio_url, sid)
        _add(out.srt_url, sid)
        _add(out.manifest_url, sid)

        # asset_meta fields
        am = sample.asset_meta
        _add(am.final_video_url, sid)
        _add(am.cover_url, sid)
        _add(am.audio_url, sid)
        _add(am.srt_url, sid)
        _add(am.manifest_url, sid)

        # job_run.asset_refs
        job_run = sample.job_run or {}
        asset_refs = job_run.get("asset_refs") or {}
        for val in asset_refs.values():
            _add(val, sid)

    return ref_map


# ─── File scanning ────────────────────────────────────────────────────────────

# Extensions considered runtime assets
ASSET_EXTENSIONS = {
    ".mp4", ".mp3", ".wav", ".srt", ".ass",
    ".json", ".png", ".jpg", ".jpeg", ".webp",
    ".gif", ".bmp", ".avi", ".mov", ".mkv",
}

# Directories to skip entirely
SKIP_DIRS = {"style_sweep/jobs", "style_sweep/jobs/"}


def _iter_asset_files(root: Path, skip_dirs: set[str]) -> list[tuple[Path, int, float]]:
    """Walk root recursively, yield (file_path, size_bytes, mtime_ts) for asset files.

    Skips directories in skip_dirs (checked as path prefixes).
    """
    results = []
    now = time.time()

    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        # Normalize to forward slashes for comparison
        dp_str = str(dp).replace("\\", "/")

        # Prune skip dirs in-place to avoid descending
        dirnames[:] = [
            d for d in dirnames
            if not any(sd.rstrip("/") in f"{dp_str}/{d}".replace("\\", "/")
                       for sd in skip_dirs)
        ]

        for fname in filenames:
            fpath = dp / fname
            # Check extension
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ASSET_EXTENSIONS:
                continue
            try:
                stat = fpath.stat()
                results.append((fpath, stat.st_size, stat.st_mtime))
            except OSError:
                continue

    return results


# ─── Main scan logic ──────────────────────────────────────────────────────────

def scan_style_sweep_assets(
    min_age_days: int = 7,
    include_protected: bool = True,
    limit: int = 500,
) -> dict[str, Any]:
    """Scan Style Sweep runtime assets (dry-run only).

    Parameters
    ----------
    min_age_days
        Only mark unreferenced files older than this as deletable.
    include_protected
        Whether to include protectedItems in the response.
    limit
        Max items per items list (protected / deletable / skipped).

    Returns
    -------
    dict with keys:
        dryRun, root, minAgeDays, totalAssetFiles, protectedCount,
        deletableCount, skippedCount, estimatedDeletableBytes,
        protectedItems, deletableItems, skippedItems, warnings
    """
    # Build referenced asset map
    referenced_map = collect_referenced_assets()
    referenced_paths: set[str] = set(referenced_map.keys())

    # Scan runtime/video_lab
    scan_root = RUNTIME_DIR / "video_lab"
    warnings: list[str] = []

    if not scan_root.exists():
        warnings.append(f"Scan root does not exist: {scan_root}")

    files: list[tuple[Path, int, float]] = []
    if scan_root.exists():
        files = _iter_asset_files(scan_root, SKIP_DIRS)

    now_ts = time.time()
    min_age_seconds = min_age_days * 86400

    protected_items: list[dict[str, Any]] = []
    deletable_items: list[dict[str, Any]] = []
    skipped_items: list[dict[str, Any]] = []

    total_count = len(files)
    protected_count = 0
    deletable_count = 0
    skipped_count = 0
    estimated_deletable_bytes = 0

    for fpath, size, mtime in files:
        rel = fpath.relative_to(RUNTIME_DIR)
        norm = str(rel).replace("\\", "/")

        # Check if protected
        if norm in referenced_paths or fpath.name in referenced_paths:
            protected_count += 1
            if include_protected and len(protected_items) < limit:
                sample_ids = list(referenced_map.get(norm, set()) | referenced_paths.difference(referenced_map).intersection({fpath.name}))
                protected_items.append({
                    "path": str(rel),
                    "sizeBytes": size,
                    "reason": "referenced_by_style_gallery",
                    "sampleIds": list(referenced_map.get(norm, set())),
                })
        else:
            age = now_ts - mtime
            if age < min_age_seconds:
                skipped_count += 1
                if len(skipped_items) < limit:
                    skipped_items.append({
                        "path": str(rel),
                        "sizeBytes": size,
                        "lastModified": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                        "reason": "unreferenced_but_too_new",
                    })
            else:
                deletable_count += 1
                estimated_deletable_bytes += size
                if len(deletable_items) < limit:
                    deletable_items.append({
                        "path": str(rel),
                        "sizeBytes": size,
                        "lastModified": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                        "reason": "unreferenced_older_than_min_age",
                    })

    return {
        "dryRun": True,
        "root": str(scan_root),
        "minAgeDays": min_age_days,
        "totalAssetFiles": total_count,
        "protectedCount": protected_count,
        "deletableCount": deletable_count,
        "skippedCount": skipped_count,
        "estimatedDeletableBytes": estimated_deletable_bytes,
        "protectedItems": protected_items,
        "deletableItems": deletable_items,
        "skippedItems": skipped_items,
        "warnings": warnings,
    }
