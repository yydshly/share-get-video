"""
tests/test_style_sweep_asset_scan.py
Stage 3A-4: Dry-run scan for Style Sweep runtime assets.

Coverage:
1. normalize_asset_ref handles runtime paths, /runtime paths, URL paths, Windows paths
2. collect_referenced_assets collects output / asset_meta / job_run.asset_refs
3. scan marks sample-referenced files as protectedItems
4. scan marks unreferenced+old files as deletableItems
5. scan marks unreferenced+new files as skippedItems
6. scan skips style_sweep/jobs directory (job JSON)
7. GET /style-sweep-assets/scan returns dryRun=true
8. scan does not delete any files
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.video_lab.services.style_sweep_asset_cleanup_service import (
    normalize_asset_ref,
    collect_referenced_assets,
    scan_style_sweep_assets,
)
from app.video_lab.style_gallery import store as sg_store


# ─── normalize_asset_ref tests ─────────────────────────────────────────────────

class TestNormalizeAssetRef:
    """normalize_asset_ref normalizes various path formats to consistent POSIX form."""

    @pytest.mark.parametrize("input_val,expected", [
        # Basic runtime paths
        ("runtime/video_lab/experiments/abc/final.mp4", "runtime/video_lab/experiments/abc/final.mp4"),
        ("runtime/video_lab/remotion/test.srt", "runtime/video_lab/remotion/test.srt"),
        # Leading slash
        ("/runtime/video_lab/experiments/abc/final.mp4", "runtime/video_lab/experiments/abc/final.mp4"),
        # URL with http/https
        ("http://localhost:8777/runtime/video_lab/experiments/abc/final.mp4", "runtime/video_lab/experiments/abc/final.mp4"),
        ("https://cdn.example.com/runtime/video_lab/abc.mp4", "runtime/video_lab/abc.mp4"),
        # Windows backslashes
        (r"D:\projects\runtime\video_lab\experiments\abc\final.mp4", "runtime/video_lab/experiments/abc/final.mp4"),
        (r"D:\runtime\video_lab\experiments\abc\final.mp4", "runtime/video_lab/experiments/abc/final.mp4"),
        # Mixed Windows forward slash
        ("D:/projects/runtime/video_lab/experiments/abc/final.mp4", "runtime/video_lab/experiments/abc/final.mp4"),
        # style_gallery paths
        ("style_gallery/records/style_samples.jsonl", "style_gallery/records/style_samples.jsonl"),
        ("/style_gallery/records/style_samples.jsonl", "style_gallery/records/style_samples.jsonl"),
        # Absolute Unix path
        ("/home/user/project/runtime/video_lab/experiments/abc.mp4", "runtime/video_lab/experiments/abc.mp4"),
        # Empty / None
        ("", ""),
        ("/runtime/", "runtime"),
        # Double slashes
        ("//runtime/video_lab/abc.mp4", "runtime/video_lab/abc.mp4"),
    ])
    def test_normalize_formats(self, input_val, expected):
        result = normalize_asset_ref(input_val)
        assert result == expected, f"normalize_asset_ref({input_val!r}) = {result!r}, expected {expected!r}"


# ─── collect_referenced_assets tests ──────────────────────────────────────────

class TestCollectReferencedAssets:
    """collect_referenced_assets builds map of sample-referenced asset paths."""

    def setup_method(self):
        """Redirect sg_store to a temp directory with known samples."""
        self._tmp = tempfile.mkdtemp()
        self._records_dir = Path(self._tmp) / "records"
        self._records_dir.mkdir(parents=True)
        self._sg_runtime = Path(self._tmp) / "style_gallery"
        self._sg_runtime.mkdir(parents=True)
        self._jsonl = self._records_dir / "style_samples.jsonl"

        import app.video_lab.style_gallery.store as store
        self._orig_runtime = store._RUNTIME
        self._orig_records = store._RECORDS_DIR
        self._orig_jsonl = store._JSONL_PATH

        store._RUNTIME = self._sg_runtime
        store._RECORDS_DIR = self._records_dir
        store._JSONL_PATH = self._jsonl
        store._ensure_dirs()

    def teardown_method(self):
        import app.video_lab.style_gallery.store as store
        store._RUNTIME = self._orig_runtime
        store._RECORDS_DIR = self._orig_records
        store._JSONL_PATH = self._orig_jsonl

    def _write_sample(self, sample_dict: dict) -> None:
        with open(self._jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample_dict, ensure_ascii=False) + "\n")

    def test_collects_output_fields(self):
        """output.path / poster / audio_url / srt_url / manifest_url are collected."""
        self._write_sample({
            "id": "sample_out_001",
            "route_id": "local_frame_compose",
            "route_name": "Pillow",
            "style_name": "Test",
            "status": "candidate",
            "params": {},
            "output": {
                "type": "mp4",
                "path": "runtime/video_lab/experiments/abc/final.mp4",
                "poster": "runtime/video_lab/experiments/abc/poster.jpg",
                "audio_url": "runtime/video_lab/experiments/abc/audio.mp3",
                "srt_url": "runtime/video_lab/experiments/abc/subs.srt",
                "manifest_url": "runtime/video_lab/experiments/abc/manifest.json",
            },
            "evaluation": {},
            "tags": [],
            "created_at": "2026-06-01T10:00:00+00:00",
        })

        refs = collect_referenced_assets()
        assert "runtime/video_lab/experiments/abc/final.mp4" in refs
        assert "runtime/video_lab/experiments/abc/poster.jpg" in refs
        assert "runtime/video_lab/experiments/abc/audio.mp3" in refs
        assert "runtime/video_lab/experiments/abc/subs.srt" in refs
        assert "runtime/video_lab/experiments/abc/manifest.json" in refs

    def test_collects_asset_meta_fields(self):
        """asset_meta fields are collected."""
        self._write_sample({
            "id": "sample_am_001",
            "route_id": "template_programmatic_render",
            "route_name": "Remotion",
            "style_name": "Test",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "dummy.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-06-01T10:00:00+00:00",
            "asset_meta": {
                "final_video_url": "runtime/video_lab/remotion/out/final.mp4",
                "cover_url": "runtime/video_lab/remotion/out/poster.jpg",
                "audio_url": "runtime/video_lab/remotion/out/audio.mp3",
                "srt_url": "runtime/video_lab/remotion/out/subs.srt",
                "manifest_url": "runtime/video_lab/remotion/out/manifest.json",
            },
        })

        refs = collect_referenced_assets()
        assert "runtime/video_lab/remotion/out/final.mp4" in refs
        assert "runtime/video_lab/remotion/out/poster.jpg" in refs
        assert "runtime/video_lab/remotion/out/audio.mp3" in refs

    def test_collects_job_run_asset_refs(self):
        """job_run.asset_refs fields are collected."""
        self._write_sample({
            "id": "sample_jr_001",
            "route_id": "ai_asset_then_compose",
            "route_name": "AI 素材",
            "style_name": "Test",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "dummy.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-06-01T10:00:00+00:00",
            "job_run": {
                "asset_refs": {
                    "video_url": "runtime/video_lab/ai/out/final.mp4",
                    "audio_url": "runtime/video_lab/ai/out/audio.mp3",
                    "ass_url": "runtime/video_lab/ai/out/subs.ass",
                    "cover_url": "runtime/video_lab/ai/out/poster.jpg",
                    "manifest_url": "runtime/video_lab/ai/out/manifest.json",
                }
            },
        })

        refs = collect_referenced_assets()
        assert "runtime/video_lab/ai/out/final.mp4" in refs
        assert "runtime/video_lab/ai/out/ass_url" not in refs  # key is ass_url, value is path
        assert "runtime/video_lab/ai/out/subs.ass" in refs

    def test_multiple_samples_same_path(self):
        """Same path referenced by multiple samples appears once, with both sample IDs."""
        for i in range(3):
            self._write_sample({
                "id": f"sample_multi_{i}",
                "route_id": "local_frame_compose",
                "route_name": "Pillow",
                "style_name": f"Test {i}",
                "status": "candidate",
                "params": {},
                "output": {"type": "mp4", "path": "runtime/video_lab/shared/abc.mp4"},
                "evaluation": {},
                "tags": [],
                "created_at": "2026-06-01T10:00:00+00:00",
            })

        refs = collect_referenced_assets()
        assert "runtime/video_lab/shared/abc.mp4" in refs
        assert len(refs["runtime/video_lab/shared/abc.mp4"]) == 3


# ─── scan_style_sweep_assets tests ───────────────────────────────────────────

class TestScanStyleSweepAssets:
    """scan_style_sweep_assets returns correct categorization without deleting files."""

    def setup_method(self):
        """Set up a fake RUNTIME_DIR with known files."""
        import app.video_lab.services.style_sweep_asset_cleanup_service as svc

        self._tmp = tempfile.mkdtemp()
        self._runtime_root = Path(self._tmp)
        self._video_lab_dir = self._runtime_root / "video_lab"
        self._video_lab_dir.mkdir(parents=True)

        # Protected: referenced by a sample (created below)
        self._protected_dir = self._video_lab_dir / "experiments" / "protected"
        self._protected_dir.mkdir(parents=True)
        self._protected_file = self._protected_dir / "final.mp4"
        self._protected_file.write_text("protected")

        # Deletable: unreferenced + old
        self._old_dir = self._video_lab_dir / "experiments" / "old"
        self._old_dir.mkdir(parents=True)
        self._old_file = self._old_dir / "final.mp4"
        self._old_file.write_text("old")
        old_mtime = time.time() - 20 * 86400  # 20 days ago
        os.utime(self._old_file, (old_mtime, old_mtime))

        # Skipped: unreferenced + too new
        self._new_dir = self._video_lab_dir / "experiments" / "new"
        self._new_dir.mkdir(parents=True)
        self._new_file = self._new_dir / "final.mp4"
        self._new_file.write_text("new")

        # Job JSON dir (should be skipped)
        self._jobs_dir = self._runtime_root / "video_lab" / "style_sweep" / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._job_json = self._jobs_dir / "sweep_test.json"
        self._job_json.write_text('{"jobId": "sweep_test"}')
        job_mtime = time.time() - 20 * 86400
        os.utime(self._job_json, (job_mtime, job_mtime))

        # Save original and patch
        self._orig_runtime_dir = svc.RUNTIME_DIR
        svc.RUNTIME_DIR = self._runtime_root

        # Set up sg_store with a protected sample referencing _protected_file
        import app.video_lab.style_gallery.store as store
        self._orig_sg_runtime = store._RUNTIME
        self._orig_sg_records = store._RECORDS_DIR
        self._orig_sg_jsonl = store._JSONL_PATH

        self._sg_tmp = tempfile.mkdtemp()
        self._sg_records = Path(self._sg_tmp) / "records"
        self._sg_records.mkdir(parents=True)
        self._sg_runtime = Path(self._sg_tmp) / "style_gallery"
        self._sg_runtime.mkdir(parents=True)
        self._sg_jsonl = self._sg_records / "style_samples.jsonl"

        store._RUNTIME = self._sg_runtime
        store._RECORDS_DIR = self._sg_records
        store._JSONL_PATH = self._sg_jsonl
        store._ensure_dirs()

        # Write a sample that references the protected file (with runtime/ prefix to match real Style Gallery format)
        protected_rel = str(self._protected_file.relative_to(self._runtime_root)).replace("\\", "/")
        with open(self._sg_jsonl, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "id": "sample_protected",
                "route_id": "local_frame_compose",
                "route_name": "Pillow",
                "style_name": "Protected",
                "status": "candidate",
                "params": {},
                "output": {"type": "mp4", "path": f"runtime/{protected_rel}"},
                "evaluation": {},
                "tags": [],
                "created_at": "2026-06-01T10:00:00+00:00",
            }, ensure_ascii=False) + "\n")

    def teardown_method(self):
        import app.video_lab.services.style_sweep_asset_cleanup_service as svc
        import app.video_lab.style_gallery.store as store
        svc.RUNTIME_DIR = self._orig_runtime_dir
        store._RUNTIME = self._orig_sg_runtime
        store._RECORDS_DIR = self._orig_sg_records
        store._JSONL_PATH = self._orig_sg_jsonl

    def test_scan_returns_dry_run_true(self):
        """scan result always has dryRun=True."""
        result = scan_style_sweep_assets(min_age_days=7)
        assert result["dryRun"] is True

    def test_protected_file_in_protected_items(self):
        """File referenced by a Style Gallery sample goes to protectedItems."""
        result = scan_style_sweep_assets(min_age_days=7, include_protected=True)
        protected_paths = [p["path"] for p in result["protectedItems"]]
        # API returns runtime/video_lab/... format (matching Style Gallery references)
        protected_rel = str(self._protected_file.relative_to(self._runtime_root)).replace("\\", "/")
        assert f"runtime/{protected_rel}" in protected_paths

    def test_old_unreferenced_file_in_deletable_items(self):
        """Unreferenced file older than min_age goes to deletableItems."""
        result = scan_style_sweep_assets(min_age_days=7)
        deletable_paths = [p["path"] for p in result["deletableItems"]]
        old_rel = str(self._old_file.relative_to(self._runtime_root)).replace("\\", "/")
        assert f"runtime/{old_rel}" in deletable_paths

    def test_new_unreferenced_file_in_skipped_items(self):
        """Unreferenced file newer than min_age goes to skippedItems."""
        result = scan_style_sweep_assets(min_age_days=7)
        skipped_paths = [p["path"] for p in result["skippedItems"]]
        new_rel = str(self._new_file.relative_to(self._runtime_root)).replace("\\", "/")
        assert f"runtime/{new_rel}" in skipped_paths

    def test_job_json_not_in_results(self):
        """Files under style_sweep/jobs are skipped entirely."""
        result = scan_style_sweep_assets(min_age_days=0)
        all_paths = (
            [p["path"] for p in result["protectedItems"]] +
            [p["path"] for p in result["deletableItems"]] +
            [p["path"] for p in result["skippedItems"]]
        )
        # API returns runtime/video_lab/... format
        job_rel = str(self._job_json.relative_to(self._runtime_root)).replace("\\", "/")
        assert f"runtime/{job_rel}" not in all_paths

    def test_no_files_are_deleted(self):
        """After scan, all files still exist on disk."""
        result = scan_style_sweep_assets(min_age_days=7)
        assert self._protected_file.exists()
        assert self._old_file.exists()
        assert self._new_file.exists()
        assert self._job_json.exists()

    def test_counts_sum_to_total(self):
        """protectedCount + deletableCount + skippedCount == totalAssetFiles."""
        result = scan_style_sweep_assets(min_age_days=7)
        total_classified = result["protectedCount"] + result["deletableCount"] + result["skippedCount"]
        assert total_classified == result["totalAssetFiles"]

    def test_scan_protects_runtime_prefixed_sample_asset(self):
        """A file whose Style Gallery reference uses runtime/video_lab/... is correctly protected.

        Regression test: previously the scan used fpath.relative_to(RUNTIME_DIR) giving
        video_lab/... while sample references use runtime/video_lab/..., causing
        protected assets to be mis-classified as deletable.
        """
        result = scan_style_sweep_assets(min_age_days=0)
        # The protected file has a matching sample reference with runtime/ prefix
        assert result["protectedCount"] >= 1
        protected_paths = [p["path"] for p in result["protectedItems"]]
        protected_rel = str(self._protected_file.relative_to(self._runtime_root)).replace("\\", "/")
        assert f"runtime/{protected_rel}" in protected_paths
        # Must NOT appear in deletableItems
        deletable_paths = [p["path"] for p in result["deletableItems"]]
        assert f"runtime/{protected_rel}" not in deletable_paths

    def test_estimated_bytes_accumulates_deletable(self):
        """estimatedDeletableBytes is sum of sizeBytes of deletableItems."""
        result = scan_style_sweep_assets(min_age_days=7)
        expected = sum(p["sizeBytes"] for p in result["deletableItems"])
        assert result["estimatedDeletableBytes"] == expected


# ─── Router test ────────────────────────────────────────────────────────────────

class TestScanRouter:
    """GET /style-sweep-assets/scan endpoint."""

    def setup_method(self):
        import tempfile
        from pathlib import Path
        import app.video_lab.services.style_sweep_asset_cleanup_service as svc

        self._tmp = tempfile.mkdtemp()
        self._runtime_root = Path(self._tmp)
        self._video_lab_dir = self._runtime_root / "video_lab"
        self._video_lab_dir.mkdir(parents=True)

        self._orig_runtime_dir = svc.RUNTIME_DIR
        svc.RUNTIME_DIR = self._runtime_root

        import app.video_lab.style_gallery.store as store
        self._orig_sg_runtime = store._RUNTIME
        self._orig_sg_records = store._RECORDS_DIR
        self._orig_sg_jsonl = store._JSONL_PATH

        self._sg_tmp = tempfile.mkdtemp()
        self._sg_records = Path(self._sg_tmp) / "records"
        self._sg_records.mkdir(parents=True)
        self._sg_runtime = Path(self._sg_tmp) / "style_gallery"
        self._sg_runtime.mkdir(parents=True)
        self._sg_jsonl = self._sg_records / "style_samples.jsonl"

        store._RUNTIME = self._sg_runtime
        store._RECORDS_DIR = self._sg_records
        store._JSONL_PATH = self._sg_jsonl
        store._ensure_dirs()

    def teardown_method(self):
        import app.video_lab.services.style_sweep_asset_cleanup_service as svc
        import app.video_lab.style_gallery.store as store
        svc.RUNTIME_DIR = self._orig_runtime_dir
        store._RUNTIME = self._orig_sg_runtime
        store._RECORDS_DIR = self._orig_sg_records
        store._JSONL_PATH = self._orig_sg_jsonl

    def test_scan_returns_200_and_dry_run(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/video-lab/style-sweep-assets/scan")
        assert response.status_code == 200
        data = response.json()
        assert data["dryRun"] is True
        assert "totalAssetFiles" in data
        assert "protectedCount" in data
        assert "deletableCount" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
