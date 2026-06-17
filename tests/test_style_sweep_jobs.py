"""
Tests for V1.2.3 P1B style_sweep_jobs:
- list_sweep_jobs summary (no full results, sorted by updatedAt desc)
- update_sweep_job_marks persists manualMarks
- get_sweep_job returns manualMarks
- from_dict handles old job JSONs without contentPreview / params / manualMarks
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.style_sweep_jobs import (
    SweepJob,
    StyleResultEntry,
    list_sweep_jobs,
    update_sweep_job_marks,
)


class TestListSweepJobsSummary:
    """list_sweep_jobs returns summary dicts (no full results), sorted desc."""

    def test_returns_summary_not_results(self):
        """Summary should not contain 'results' key."""
        jobs = list_sweep_jobs()
        assert isinstance(jobs, list)

    def test_sorted_by_updated_at_desc(self):
        """Jobs should be sorted by updatedAt/startedAt descending."""
        jobs = list_sweep_jobs(limit=10)
        for i in range(len(jobs) - 1):
            curr = jobs[i].get("updatedAt") or jobs[i].get("startedAt") or ""
            next_ = jobs[i + 1].get("updatedAt") or jobs[i + 1].get("startedAt") or ""
            assert curr >= next_, f"Job {i} updatedAt '{curr}' < Job {i+1} '{next_}'"


class TestUpdateSweepJobMarks:
    """update_sweep_job_marks writes manualMarks back to the job JSON."""

    def test_update_marks_writes_field(self):
        """Patching marks should store them in the job."""
        job_id = "sweep_testmarks001"
        job = SweepJob(
            jobId=job_id,
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow 静态卡",
            total=5,
            startedAt="2026-06-17T00:00:00Z",
            updatedAt="2026-06-17T00:01:00Z",
        )
        from app.video_lab.style_sweep_jobs import _save_job, _get_jobs_dir
        _get_jobs_dir().mkdir(parents=True, exist_ok=True)
        _save_job(job)

        marks = {
            "style_001": {"issues": ["ok"], "note": "可用"},
            "style_002": {"issues": ["missing_visual"], "note": "缺图"},
        }
        updated = update_sweep_job_marks(job_id, marks)
        assert updated is not None
        assert updated.manualMarks == marks

    def test_update_nonexistent_returns_none(self):
        """Updating a non-existent job should return None."""
        result = update_sweep_job_marks("sweep_does_not_exist_xyz", {})
        assert result is None

    def test_get_sweep_job_returns_manual_marks(self):
        """get_sweep_job should return the manualMarks field."""
        job_id = "sweep_testmarks002"
        job = SweepJob(
            jobId=job_id,
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion 动效",
            total=14,
            startedAt="2026-06-17T00:00:00Z",
            updatedAt="2026-06-17T00:02:00Z",
            manualMarks={"style_x": {"issues": ["ok"], "note": "ok"}},
        )
        from app.video_lab.style_sweep_jobs import _save_job, _get_jobs_dir, get_sweep_job
        _get_jobs_dir().mkdir(parents=True, exist_ok=True)
        _save_job(job)

        loaded = get_sweep_job(job_id)
        assert loaded is not None
        assert loaded.manualMarks == {"style_x": {"issues": ["ok"], "note": "ok"}}


class TestOldJobCompatibility:
    """from_dict must not crash on old job JSONs missing new fields."""

    def test_from_dict_missing_content_preview(self):
        """Old job without contentPreview should default to ''."""
        d = {
            "jobId": "sweep_old001",
            "status": "completed",
            "routeId": "local_frame_compose",
            "routeName": "Pillow",
            "total": 5,
        }
        job = SweepJob.from_dict(d)
        assert job.contentPreview == ""
        assert job.params == {}
        assert job.manualMarks == {}

    def test_from_dict_missing_params(self):
        """Old job without params should default to {}."""
        d = {
            "jobId": "sweep_old002",
            "status": "completed",
            "routeId": "local_frame_compose",
            "routeName": "Pillow",
            "total": 3,
            "contentPreview": "一些内容",
        }
        job = SweepJob.from_dict(d)
        assert job.params == {}
        assert job.manualMarks == {}

    def test_from_dict_missing_manual_marks(self):
        """Old job without manualMarks should default to {}."""
        d = {
            "jobId": "sweep_old003",
            "status": "completed",
            "routeId": "ai_asset_then_compose",
            "routeName": "AI 素材",
            "total": 2,
            "contentPreview": "内容",
            "params": {"targetDuration": 45},
        }
        job = SweepJob.from_dict(d)
        assert job.manualMarks == {}


class TestSweepJobToDict:
    """to_dict must include all new fields."""

    def test_to_dict_includes_content_preview(self):
        job = SweepJob(
            jobId="sweep_dict001",
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=5,
            contentPreview="今日 AI 前沿三条要点...",
            params={"targetDuration": 45},
            manualMarks={"s1": {"issues": ["ok"], "note": ""}},
        )
        d = job.to_dict()
        assert d["contentPreview"] == "今日 AI 前沿三条要点..."
        assert d["params"] == {"targetDuration": 45}
        assert d["manualMarks"] == {"s1": {"issues": ["ok"], "note": ""}}

    def test_list_jobs_excludes_results(self):
        """list_sweep_jobs summary must not include 'results' key."""
        jobs = list_sweep_jobs()
        for j in jobs:
            assert "results" not in j, "Summary should not contain full results"
            assert "contentPreview" in j
            assert "params" in j


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
