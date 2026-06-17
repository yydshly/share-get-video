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
    delete_sweep_job,
    _get_jobs_dir,
    _save_job,
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


class TestDeleteSweepJob:
    """delete_sweep_job removes only the job JSON, not any assets."""

    def setup_method(self):
        import tempfile
        from pathlib import Path
        import app.video_lab.style_sweep_jobs as ssj

        self._tmp = tempfile.mkdtemp()
        self._jobs_dir = Path(self._tmp) / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._orig = ssj._RUNTIME_DIR
        ssj._RUNTIME_DIR = self._jobs_dir

    def teardown_method(self):
        import app.video_lab.style_sweep_jobs as ssj
        ssj._RUNTIME_DIR = self._orig

    def test_delete_existing_job_returns_true(self):
        """Deleting a job that exists returns True."""
        job_id = "sweep_deletetest001"
        job = SweepJob(
            jobId=job_id,
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=2,
        )
        _save_job(job)

        result = delete_sweep_job(job_id)
        assert result is True

    def test_delete_nonexistent_job_returns_false(self):
        """Deleting a job that does not exist returns False."""
        result = delete_sweep_job("sweep_does_not_exist_xyz")
        assert result is False

    def test_deleted_job_no_longer_in_list(self):
        """After deletion, the job does not appear in list_sweep_jobs."""
        job_id = "sweep_deletetest002"
        job = SweepJob(
            jobId=job_id,
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=1,
        )
        _save_job(job)

        # Verify it appears in list
        jobs = list_sweep_jobs()
        assert any(j["jobId"] == job_id for j in jobs)

        # Delete it
        deleted = delete_sweep_job(job_id)
        assert deleted is True

        # Verify it's gone
        jobs_after = list_sweep_jobs()
        assert not any(j["jobId"] == job_id for j in jobs_after)

    def test_delete_does_not_affect_other_jobs(self):
        """Deleting one job does not remove other jobs."""
        job_a = SweepJob(
            jobId="sweep_del_other_a",
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=1,
        )
        job_b = SweepJob(
            jobId="sweep_del_other_b",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion",
            total=1,
        )
        _save_job(job_a)
        _save_job(job_b)

        delete_sweep_job("sweep_del_other_a")

        jobs_after = list_sweep_jobs()
        assert any(j["jobId"] == "sweep_del_other_b" for j in jobs_after)
        assert not any(j["jobId"] == "sweep_del_other_a" for j in jobs_after)


class TestDeleteRouter:
    """DELETE /style-sweep-jobs/{job_id} endpoint."""

    def setup_method(self):
        import tempfile
        from pathlib import Path
        import app.video_lab.style_sweep_jobs as ssj

        self._tmp = tempfile.mkdtemp()
        self._jobs_dir = Path(self._tmp) / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._orig = ssj._RUNTIME_DIR
        ssj._RUNTIME_DIR = self._jobs_dir

    def teardown_method(self):
        import app.video_lab.style_sweep_jobs as ssj
        ssj._RUNTIME_DIR = self._orig

    def test_delete_existing_job_returns_deleted_true(self):
        """DELETE existing job returns deleted=true."""
        from fastapi.testclient import TestClient
        from app.main import app

        job_id = "sweep_del_router001"
        job = SweepJob(
            jobId=job_id,
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=1,
        )
        _get_jobs_dir().mkdir(parents=True, exist_ok=True)
        _save_job(job)

        client = TestClient(app)
        response = client.delete(f"/video-lab/style-sweep-jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["deletedAssets"] is False
        assert data["jobId"] == job_id

    def test_delete_nonexistent_job_returns_404(self):
        """DELETE non-existent job returns 404."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.delete("/video-lab/style-sweep-jobs/sweep_does_not_exist_xyz")
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
