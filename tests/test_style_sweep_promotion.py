"""
tests/test_style_sweep_promotion.py
Stage 2A: Promote Style Sweep results to Style Gallery samples.

Coverage:
1. job not found → raises ValueError
2. styleIds empty → raises ValueError
3. successful result → creates Style Gallery sample
4. failed result → skipped, not promoted
5. non-existent styleId → skipped
6. duplicate promote → returns existing sample, reused=True
7. promoted sample preserves videoUrl / manifestUrl / audioUrl / srtUrl
8. promoted sample preserves manualMarks
9. promoted sample preserves subtitleDiagnostics from rawOutput
10. promoted sample has source=style_sweep, sweepJobId, styleId tags
"""

import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

from app.video_lab.style_sweep_jobs import (
    SweepJob,
    StyleResultEntry,
    _save_job,
    _get_jobs_dir,
    get_sweep_job,
)
from app.video_lab.style_gallery import store as sg_store
from app.video_lab.services.style_sweep_promotion_service import (
    promote_sweep_results_to_gallery,
    _find_sample_by_sweep_ref,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

class TestPromoteService:
    """Tests for promote_sweep_results_to_gallery()."""

    def setup_method(self):
        """Save a real job JSON to a temp dir for each test."""
        self._tmp = tempfile.mkdtemp()
        self._jobs_dir = Path(self._tmp) / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._records_dir = Path(self._tmp) / "records"
        self._records_dir.mkdir(parents=True)

        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store

        # Redirect paths
        self._orig_jobs_dir = ssj._RUNTIME_DIR
        self._orig_sg_runtime = store._RUNTIME
        self._orig_sg_records = store._RECORDS_DIR
        self._orig_sg_jsonl = store._JSONL_PATH

        ssj._RUNTIME_DIR = self._jobs_dir
        store._RUNTIME = Path(self._tmp) / "style_gallery"
        store._RECORDS_DIR = self._records_dir
        store._JSONL_PATH = self._records_dir / "style_samples.jsonl"

        store._ensure_dirs()

    def teardown_method(self):
        """Restore original paths."""
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store

        ssj._RUNTIME_DIR = self._orig_jobs_dir
        store._RUNTIME = self._orig_sg_runtime
        store._RECORDS_DIR = self._orig_sg_records
        store._JSONL_PATH = self._orig_sg_jsonl

    # ─── 1. job not found ───────────────────────────────────────────────────

    def test_job_not_found_raises(self):
        """promote_sweep_results_to_gallery with unknown job_id raises ValueError."""
        import pytest

        with tempfile.TemporaryDirectory() as tmp:
            import app.video_lab.style_sweep_jobs as ssj
            ssj._RUNTIME_DIR = Path(tmp) / "jobs"
            ssj._RUNTIME_DIR.mkdir(parents=True)

            with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
                jsonl_path = f.name

            import app.video_lab.style_gallery.store as store
            store._RUNTIME = Path(tmp) / "sg"
            store._RECORDS_DIR = Path(tmp) / "sg" / "records"
            store._RECORDS_DIR.mkdir(parents=True)
            store._JSONL_PATH = Path(jsonl_path)
            store._ensure_dirs()

            with pytest.raises(ValueError) as ctx:
                promote_sweep_results_to_gallery(
                    job_id="sweep_does_not_exist",
                    style_ids=["pillow_data_card"],
                )
            assert "Job not found" in str(ctx.value)

    # ─── 2. styleIds empty ─────────────────────────────────────────────────

    def test_empty_style_ids_raises(self):
        """Empty styleIds list raises ValueError."""
        import pytest

        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "jobs"
            jobs_dir.mkdir(parents=True)
            import app.video_lab.style_sweep_jobs as ssj
            ssj._RUNTIME_DIR = jobs_dir

            with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
                jsonl_path = f.name

            import app.video_lab.style_gallery.store as store
            store._RUNTIME = Path(tmp) / "sg"
            store._RECORDS_DIR = Path(tmp) / "sg" / "records"
            store._RECORDS_DIR.mkdir(parents=True)
            store._JSONL_PATH = Path(jsonl_path)
            store._ensure_dirs()

            # Save a real job so we hit the "empty styleIds" check
            job = SweepJob(
                jobId="sweep_promo001",
                status="completed",
                routeId="local_frame_compose",
                routeName="Pillow 静态卡",
                total=1,
            )
            _save_job(job)

            with pytest.raises(ValueError) as ctx:
                promote_sweep_results_to_gallery(
                    job_id="sweep_promo001",
                    style_ids=[],
                )
            assert "styleIds must not be empty" in str(ctx.value)

    # ─── 3. successful result promotes ─────────────────────────────────────

    def test_successful_result_creates_sample(self):
        """A succeeded result with finalVideoUrl creates a Style Gallery sample."""
        job = SweepJob(
            jobId="sweep_promo_ok",
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow 静态卡",
            total=3,
            succeeded=1,
            manualMarks={
                "pillow_data_card": {
                    "issues": ["ok"],
                    "note": "可用",
                }
            },
        )
        entry = StyleResultEntry(
            styleId="pillow_data_card",
            styleName="数据卡片",
            description="数据展示卡片样式",
            tags=["pillow", "data"],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/video_lab/experiments/abc/final.mp4",
                "manifestUrl": "runtime/video_lab/experiments/abc/manifest.json",
                "audioUrl": "runtime/video_lab/experiments/abc/audio.mp3",
                "srtUrl": "runtime/video_lab/experiments/abc/subs.srt",
                "assUrl": "",
                "coverUrl": "runtime/video_lab/experiments/abc/poster.jpg",
                "rawOutput": {
                    "subtitleDiagnostics": {
                        "characterCount": 120,
                        "lineCount": 3,
                    }
                },
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_ok",
            style_ids=["pillow_data_card"],
            note="测试提升",
        )

        assert result["promotedCount"] == 1
        assert result["skippedCount"] == 0
        assert len(result["samples"]) == 1
        sample_info = result["samples"][0]
        assert sample_info["styleId"] == "pillow_data_card"
        assert sample_info["routeId"] == "local_frame_compose"
        assert sample_info["reused"] is False
        assert sample_info["videoUrl"] == "runtime/video_lab/experiments/abc/final.mp4"
        assert sample_info["manifestUrl"] == "runtime/video_lab/experiments/abc/manifest.json"

        # Verify the sample was actually saved
        saved = sg_store.get_sample(sample_info["sampleId"])
        assert saved is not None
        assert saved.route_id == "local_frame_compose"
        assert saved.style_name == "数据卡片"
        assert saved.source.source_type == "style_sweep"
        assert saved.source.job_id == "sweep_promo_ok"
        assert saved.source.run_id == "pillow_data_card"
        assert saved.asset_meta.final_video_url == "runtime/video_lab/experiments/abc/final.mp4"
        assert saved.asset_meta.manifest_url == "runtime/video_lab/experiments/abc/manifest.json"
        assert saved.asset_meta.audio_url == "runtime/video_lab/experiments/abc/audio.mp3"
        assert saved.asset_meta.srt_url == "runtime/video_lab/experiments/abc/subs.srt"
        # job_run contains manualMark and subtitleDiagnostics
        assert saved.job_run["manual_mark"] == {"issues": ["ok"], "note": "可用"}
        assert saved.job_run["subtitle_diagnostics"] == {"characterCount": 120, "lineCount": 3}
        assert "style_sweep" in saved.tags
        assert "validated_candidate" in saved.tags  # because issues=["ok"]

    # ─── 4. failed result skipped ──────────────────────────────────────────

    def test_failed_result_skipped(self):
        """A result with status!=succeeded goes into skipped list."""
        job = SweepJob(
            jobId="sweep_promo_fail",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion 动效",
            total=1,
            succeeded=0,
        )
        entry = StyleResultEntry(
            styleId="remotion_broken",
            styleName="坏掉的样式",
            description="",
            tags=[],
            result={
                "status": "failed",
                "failedReason": "render error",
                "finalVideoUrl": "",
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_fail",
            style_ids=["remotion_broken"],
        )

        assert result["promotedCount"] == 0
        assert result["skippedCount"] == 1
        assert result["skipped"][0]["styleId"] == "remotion_broken"
        assert result["skipped"][0]["reason"] == "result_not_succeeded"

    # ─── 5. non-existent styleId skipped ──────────────────────────────────

    def test_unknown_style_id_skipped(self):
        """A styleId not present in job.results goes into skipped list."""
        job = SweepJob(
            jobId="sweep_promo_unknown",
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=1,
        )
        entry = StyleResultEntry(
            styleId="pillow_ok",
            styleName="好的样式",
            description="",
            tags=[],
            result={"status": "succeeded", "finalVideoUrl": "runtime/x.mp4"},
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_unknown",
            style_ids=["this_style_does_not_exist"],
        )

        assert result["promotedCount"] == 0
        assert result["skippedCount"] == 1
        assert result["skipped"][0]["styleId"] == "this_style_does_not_exist"
        assert result["skipped"][0]["reason"] == "style_id_not_found"

    # ─── 6. duplicate promote is idempotent ───────────────────────────────

    def test_duplicate_promote_returns_existing_sample(self):
        """Promoting the same job_id+styleId twice returns the existing sample with reused=True."""
        job = SweepJob(
            jobId="sweep_promo_dup",
            status="completed",
            routeId="ai_asset_then_compose",
            routeName="AI 素材",
            total=1,
        )
        entry = StyleResultEntry(
            styleId="ai_card",
            styleName="AI 卡片",
            description="",
            tags=["ai"],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/ai_test.mp4",
                "manifestUrl": "",
                "audioUrl": "",
                "srtUrl": "",
            },
        )
        job.results.append(entry)
        _save_job(job)

        # First promote
        r1 = promote_sweep_results_to_gallery(
            job_id="sweep_promo_dup",
            style_ids=["ai_card"],
        )
        assert r1["promotedCount"] == 1
        first_sample_id = r1["samples"][0]["sampleId"]

        # Second promote — should return same sample with reused=True
        r2 = promote_sweep_results_to_gallery(
            job_id="sweep_promo_dup",
            style_ids=["ai_card"],
        )
        assert r2["promotedCount"] == 1
        assert r2["samples"][0]["sampleId"] == first_sample_id
        assert r2["samples"][0]["reused"] is True

    # ─── 7. promoted sample preserves all URLs ────────────────────────────

    def test_promoted_sample_preserves_all_asset_urls(self):
        """All asset URLs from the job result are stored in the sample."""
        job = SweepJob(
            jobId="sweep_promo_urls",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion 动效",
            total=1,
        )
        entry = StyleResultEntry(
            styleId="remotion_complex",
            styleName="复杂动效",
            description="",
            tags=["remotion"],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/video_lab/remotion/test.mp4",
                "videoUrl": "",  # only finalVideoUrl is set
                "manifestUrl": "runtime/video_lab/remotion/manifest.json",
                "audioUrl": "runtime/video_lab/remotion/audio.mp3",
                "srtUrl": "runtime/video_lab/remotion/subs.srt",
                "assUrl": "runtime/video_lab/remotion/subs.ass",
                "coverUrl": "runtime/video_lab/remotion/poster.jpg",
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_urls",
            style_ids=["remotion_complex"],
        )

        sample_info = result["samples"][0]
        saved = sg_store.get_sample(sample_info["sampleId"])
        assert saved.asset_meta.final_video_url == "runtime/video_lab/remotion/test.mp4"
        assert saved.asset_meta.manifest_url == "runtime/video_lab/remotion/manifest.json"
        assert saved.asset_meta.audio_url == "runtime/video_lab/remotion/audio.mp3"
        assert saved.asset_meta.srt_url == "runtime/video_lab/remotion/subs.srt"
        assert saved.asset_meta.cover_url == "runtime/video_lab/remotion/poster.jpg"
        assert saved.output.path == "runtime/video_lab/remotion/test.mp4"
        assert saved.output.audio_url == "runtime/video_lab/remotion/audio.mp3"

    # ─── 8. promoted sample preserves manualMarks ─────────────────────────

    def test_promoted_sample_preserves_manual_marks(self):
        """manualMarks from the job are stored in job_run.job_run."""
        job = SweepJob(
            jobId="sweep_promo_marks",
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=1,
            manualMarks={
                "pillow_marked": {
                    "issues": ["ok", "covers_text"],
                    "note": "字幕有点挡",
                }
            },
        )
        entry = StyleResultEntry(
            styleId="pillow_marked",
            styleName="有标注的样式",
            description="",
            tags=[],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/p.mp4",
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_marks",
            style_ids=["pillow_marked"],
        )

        saved = sg_store.get_sample(result["samples"][0]["sampleId"])
        assert saved.job_run["manual_mark"] == {
            "issues": ["ok", "covers_text"],
            "note": "字幕有点挡",
        }
        # Tag validated_candidate only when "ok" is in issues
        assert "validated_candidate" in saved.tags

    # ─── 9. promoted sample preserves subtitleDiagnostics ─────────────────

    def test_promoted_sample_preserves_subtitle_diagnostics(self):
        """subtitleDiagnostics from rawOutput.subtitleDiagnostics is stored in job_run."""
        job = SweepJob(
            jobId="sweep_promo_subdiag",
            status="completed",
            routeId="ai_asset_then_compose",
            routeName="AI 素材",
            total=1,
        )
        entry = StyleResultEntry(
            styleId="ai_with_subs",
            styleName="AI 带字幕",
            description="",
            tags=[],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/ai.mp4",
                "rawOutput": {
                    "subtitleDiagnostics": {
                        "characterCount": 250,
                        "lineCount": 5,
                        "warnings": [],
                    }
                },
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_subdiag",
            style_ids=["ai_with_subs"],
        )

        saved = sg_store.get_sample(result["samples"][0]["sampleId"])
        assert saved.job_run["subtitle_diagnostics"] == {
            "characterCount": 250,
            "lineCount": 5,
            "warnings": [],
        }
        # Also in quality_meta.steps (via result.steps)
        assert saved.quality_meta.steps == []

    # ─── 10. source=style_sweep and tags include sweep refs ──────────────

    def test_source_and_tags_are_correct(self):
        """Sample has source_type=style_sweep, sweepJobId in source.job_id, and sweep tags."""
        job = SweepJob(
            jobId="sweep_promo_src",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion",
            total=1,
            params={"targetDuration": 60},
        )
        entry = StyleResultEntry(
            styleId="remotion_src_test",
            styleName="源测试样式",
            description="用于验证source字段",
            tags=["remotion", "motion"],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/rem.mp4",
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_src",
            style_ids=["remotion_src_test"],
            note="来源验证",
        )

        saved = sg_store.get_sample(result["samples"][0]["sampleId"])
        assert saved.source.source_type == "style_sweep"
        assert saved.source.job_id == "sweep_promo_src"
        assert saved.source.run_id == "remotion_src_test"
        assert saved.source.saved_from == "来源验证"
        assert "style_sweep" in saved.tags
        assert "remotion_src_test" in saved.tags
        assert saved.generation.visual_route == "template_programmatic_render"
        assert saved.generation.route_preset == "remotion_src_test"


# ─────────────────────────────────────────────────────────────────────────────
# Router-level tests using FastAPI TestClient
# ─────────────────────────────────────────────────────────────────────────────

class TestPromoteRouter:
    """Router-level tests for POST /style-sweep-jobs/{job_id}/promote."""

    def setup_method(self):
        """Set up temp dirs and monkeypatch stores before each test."""
        import tempfile
        from pathlib import Path
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store

        self._tmp = tempfile.mkdtemp()
        self._jobs_dir = Path(self._tmp) / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._records_dir = Path(self._tmp) / "records"
        self._records_dir.mkdir(parents=True)
        self._sg_runtime = Path(self._tmp) / "style_gallery"
        self._sg_runtime.mkdir(parents=True)

        self._orig_jobs_dir = ssj._RUNTIME_DIR
        self._orig_sg_runtime = store._RUNTIME
        self._orig_sg_records = store._RECORDS_DIR
        self._orig_sg_jsonl = store._JSONL_PATH

        ssj._RUNTIME_DIR = self._jobs_dir
        store._RUNTIME = self._sg_runtime
        store._RECORDS_DIR = self._records_dir
        store._JSONL_PATH = self._records_dir / "style_samples.jsonl"
        store._ensure_dirs()

    def teardown_method(self):
        """Restore original paths."""
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store
        ssj._RUNTIME_DIR = self._orig_jobs_dir
        store._RUNTIME = self._orig_sg_runtime
        store._RECORDS_DIR = self._orig_sg_records
        store._JSONL_PATH = self._orig_sg_jsonl

    # ─── 1. job not found → 404 ────────────────────────────────────────────

    def test_promote_unknown_job_returns_404(self):
        """POST /style-sweep-jobs/nonexistent/promote returns 404."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/video-lab/style-sweep-jobs/sweep_does_not_exist_xyz/promote",
            json={"styleIds": ["some_style"]},
        )
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    # ─── 2. empty styleIds → 400 ──────────────────────────────────────────

    def test_promote_empty_style_ids_returns_400(self):
        """POST with empty styleIds returns 400."""
        from fastapi.testclient import TestClient
        from app.main import app

        # First create a real job
        job = SweepJob(
            jobId="sweep_promo_empty_job",
            status="completed",
            routeId="local_frame_compose",
            routeName="Pillow",
            total=1,
        )
        entry = StyleResultEntry(
            styleId="pillow_ok",
            styleName="OK 样式",
            description="",
            tags=[],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/x.mp4",
            },
        )
        job.results.append(entry)
        _save_job(job)

        client = TestClient(app)
        response = client.post(
            "/video-lab/style-sweep-jobs/sweep_promo_empty_job/promote",
            json={"styleIds": []},
        )
        assert response.status_code == 400
        assert "styleIds must not be empty" in response.json()["detail"]


# ─────────────────────────────────────────────────────────────────────────────
# Additional service-level assertions
# ─────────────────────────────────────────────────────────────────────────────

class TestAssUrlSaved:
    """Verify ass_url is preserved in job_run["asset_refs"]."""

    def setup_method(self):
        import tempfile
        from pathlib import Path
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store

        self._tmp = tempfile.mkdtemp()
        self._jobs_dir = Path(self._tmp) / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._records_dir = Path(self._tmp) / "records"
        self._records_dir.mkdir(parents=True)
        self._sg_runtime = Path(self._tmp) / "style_gallery"
        self._sg_runtime.mkdir(parents=True)

        self._orig_jobs_dir = ssj._RUNTIME_DIR
        self._orig_sg_runtime = store._RUNTIME
        self._orig_sg_records = store._RECORDS_DIR
        self._orig_sg_jsonl = store._JSONL_PATH

        ssj._RUNTIME_DIR = self._jobs_dir
        store._RUNTIME = self._sg_runtime
        store._RECORDS_DIR = self._records_dir
        store._JSONL_PATH = self._records_dir / "style_samples.jsonl"
        store._ensure_dirs()

    def teardown_method(self):
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store
        ssj._RUNTIME_DIR = self._orig_jobs_dir
        store._RUNTIME = self._orig_sg_runtime
        store._RECORDS_DIR = self._orig_sg_records
        store._JSONL_PATH = self._orig_sg_jsonl

    def test_ass_url_saved_in_job_run_asset_refs(self):
        """assUrl from job result is stored in job_run.asset_refs.ass_url."""
        job = SweepJob(
            jobId="sweep_promo_ass",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion",
            total=1,
        )
        entry = StyleResultEntry(
            styleId="remotion_ass_test",
            styleName="ASS字幕样式",
            description="",
            tags=[],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/video_lab/remotion/final.mp4",
                "assUrl": "runtime/video_lab/remotion/subs.ass",
                "srtUrl": "runtime/video_lab/remotion/subs.srt",
                "audioUrl": "runtime/video_lab/remotion/audio.mp3",
                "manifestUrl": "runtime/video_lab/remotion/manifest.json",
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_promo_ass",
            style_ids=["remotion_ass_test"],
        )

        saved = sg_store.get_sample(result["samples"][0]["sampleId"])
        # ass_url must not be dropped
        assert saved.job_run["asset_refs"]["ass_url"] == "runtime/video_lab/remotion/subs.ass"
        # other refs also preserved
        assert saved.job_run["asset_refs"]["srt_url"] == "runtime/video_lab/remotion/subs.srt"
        assert saved.job_run["asset_refs"]["audio_url"] == "runtime/video_lab/remotion/audio.mp3"
        assert saved.job_run["asset_refs"]["manifest_url"] == "runtime/video_lab/remotion/manifest.json"
        assert saved.job_run["asset_refs"]["video_url"] == "runtime/video_lab/remotion/final.mp4"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])


# ─────────────────────────────────────────────────────────────────────────────
# V1.2.3: Idempotency beyond 200-sample cap & new aspect ratio fields
# ─────────────────────────────────────────────────────────────────────────────

class TestPromoteIdempotencyBeyond200:
    """V1.2.3: promote must find existing samples even when store has >200 style_sweep samples."""

    def setup_method(self):
        import tempfile
        from pathlib import Path
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store

        self._tmp = tempfile.mkdtemp()
        self._jobs_dir = Path(self._tmp) / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._records_dir = Path(self._tmp) / "records"
        self._records_dir.mkdir(parents=True)
        self._sg_runtime = Path(self._tmp) / "style_gallery"
        self._sg_runtime.mkdir(parents=True)

        self._orig_jobs_dir = ssj._RUNTIME_DIR
        self._orig_sg_runtime = store._RUNTIME
        self._orig_sg_records = store._RECORDS_DIR
        self._orig_sg_jsonl = store._JSONL_PATH

        ssj._RUNTIME_DIR = self._jobs_dir
        store._RUNTIME = self._sg_runtime
        store._RECORDS_DIR = self._records_dir
        store._JSONL_PATH = self._records_dir / "style_samples.jsonl"
        store._ensure_dirs()

    def teardown_method(self):
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store
        ssj._RUNTIME_DIR = self._orig_jobs_dir
        store._RUNTIME = self._orig_sg_runtime
        store._RECORDS_DIR = self._orig_sg_records
        store._JSONL_PATH = self._orig_sg_jsonl

    def test_duplicate_promote_works_with_over_200_style_sweep_samples(self):
        """When the store has >200 style_sweep samples, promote still finds the existing one."""
        from datetime import datetime, timezone
        from app.video_lab.style_gallery.models import SampleSource, SampleGenerationMeta, SampleAssetMeta, SampleStatus, StyleSampleOutput
        import app.video_lab.style_gallery.store as store

        # First promote creates a sample for this job+style
        job = SweepJob(
            jobId="sweep_over_200",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion",
            total=1,
        )
        entry = StyleResultEntry(
            styleId="style_first",
            styleName="第一个样式",
            description="",
            tags=[],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/first.mp4",
            },
        )
        job.results.append(entry)
        _save_job(job)

        r1 = promote_sweep_results_to_gallery(
            job_id="sweep_over_200",
            style_ids=["style_first"],
        )
        assert r1["promotedCount"] == 1
        first_id = r1["samples"][0]["sampleId"]

        # Fill the store with 210 other style_sweep samples (beyond the old limit=200)
        for i in range(210):
            fake = store.StyleSample(
                id=f"filler_{i:04d}",
                route_id="template_programmatic_render",
                route_name="填充",
                style_name=f"填充{i}",
                description="",
                status=SampleStatus.CANDIDATE,
                params={},
                output=StyleSampleOutput(type="mp4", path=f"filler_{i}.mp4"),
                tags=[],
                created_at=datetime.now(timezone.utc),
                source=SampleSource(source_type="style_sweep", job_id=f"other_job_{i}", run_id=f"style_{i}"),
                generation=SampleGenerationMeta(visual_route="template_programmatic_render"),
                asset_meta=SampleAssetMeta(),
            )
            store.save_sample(fake)

        # Second promote of the same job+style must find the existing sample
        # (was previously broken because list_samples had limit=200 and all 210 filler
        # records would push the original sample beyond the 200 limit)
        r2 = promote_sweep_results_to_gallery(
            job_id="sweep_over_200",
            style_ids=["style_first"],
        )
        assert r2["promotedCount"] == 1
        assert r2["samples"][0]["sampleId"] == first_id
        assert r2["samples"][0]["reused"] is True

        # Verify no extra sample was created
        all_ids = [r["id"] for r in store._read_all() if r["id"].startswith("sample_")]
        assert len(all_ids) == 1  # only the original sample


class TestPromoteNewAspectRatioFields:
    """V1.2.3: promote_sweep_results_to_gallery preserves new aspect ratio fields."""

    def setup_method(self):
        import tempfile
        from pathlib import Path
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store

        self._tmp = tempfile.mkdtemp()
        self._jobs_dir = Path(self._tmp) / "jobs"
        self._jobs_dir.mkdir(parents=True)
        self._records_dir = Path(self._tmp) / "records"
        self._records_dir.mkdir(parents=True)
        self._sg_runtime = Path(self._tmp) / "style_gallery"
        self._sg_runtime.mkdir(parents=True)

        self._orig_jobs_dir = ssj._RUNTIME_DIR
        self._orig_sg_runtime = store._RUNTIME
        self._orig_sg_records = store._RECORDS_DIR
        self._orig_sg_jsonl = store._JSONL_PATH

        ssj._RUNTIME_DIR = self._jobs_dir
        store._RUNTIME = self._sg_runtime
        store._RECORDS_DIR = self._records_dir
        store._JSONL_PATH = self._records_dir / "style_samples.jsonl"
        store._ensure_dirs()

    def teardown_method(self):
        import app.video_lab.style_sweep_jobs as ssj
        import app.video_lab.style_gallery.store as store
        ssj._RUNTIME_DIR = self._orig_jobs_dir
        store._RUNTIME = self._orig_sg_runtime
        store._RECORDS_DIR = self._orig_sg_records
        store._JSONL_PATH = self._orig_sg_jsonl

    def test_promote_preserves_generation_aspect_ratio_fields(self):
        """Promoted sample stores generation.output_aspect_ratio / display_aspect_ratio / fit_mode."""
        job = SweepJob(
            jobId="sweep_ar_job",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion",
            total=1,
            params={
                "aspectRatio": "9:16",
                "outputAspectRatio": "9:16.0",
                "displayAspectRatio": "9:16",
                "fitMode": "cover",
            },
        )
        entry = StyleResultEntry(
            styleId="style_ar",
            styleName="AR样式",
            description="",
            tags=[],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/ar.mp4",
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_ar_job",
            style_ids=["style_ar"],
        )
        saved = sg_store.get_sample(result["samples"][0]["sampleId"])

        assert saved is not None
        assert saved.generation.output_aspect_ratio == "9:16.0"
        assert saved.generation.display_aspect_ratio == "9:16"
        assert saved.generation.fit_mode == "cover"

    def test_promote_preserves_asset_meta_aspect_ratio_fields(self):
        """Promoted sample stores asset_meta.aspect_ratio / display_aspect_ratio / fit_mode."""
        job = SweepJob(
            jobId="sweep_am_ar_job",
            status="completed",
            routeId="template_programmatic_render",
            routeName="Remotion",
            total=1,
            params={
                "aspectRatio": "16:9",
                "outputAspectRatio": "16:9",
                "displayAspectRatio": "16:9.0",
                "fitMode": "contain",
            },
        )
        entry = StyleResultEntry(
            styleId="style_am_ar",
            styleName="AM_AR样式",
            description="",
            tags=[],
            result={
                "status": "succeeded",
                "finalVideoUrl": "runtime/am_ar.mp4",
            },
        )
        job.results.append(entry)
        _save_job(job)

        result = promote_sweep_results_to_gallery(
            job_id="sweep_am_ar_job",
            style_ids=["style_am_ar"],
        )
        saved = sg_store.get_sample(result["samples"][0]["sampleId"])

        assert saved is not None
        # generation also has the params stored
        assert saved.generation.aspect_ratio == "16:9"
        assert saved.generation.output_aspect_ratio == "16:9"
        assert saved.generation.display_aspect_ratio == "16:9.0"
        assert saved.generation.fit_mode == "contain"
        # asset_meta also carries these fields
        assert saved.asset_meta.aspect_ratio == "16:9"
        assert saved.asset_meta.display_aspect_ratio == "16:9.0"
        assert saved.asset_meta.fit_mode == "contain"
