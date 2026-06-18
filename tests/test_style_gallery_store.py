"""
tests/test_style_gallery_store.py
V0.3.7.1: Style Gallery URL resolution and status management tests
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path

from app.video_lab.style_gallery.models import StyleSample, StyleSampleOutput, SampleStatus
from app.video_lab.style_gallery import store as sg_store


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_records_dir(monkeypatch, tmp_path):
    """Redirect _RUNTIME and _RECORDS_DIR to a temp directory."""
    runtime = tmp_path / "runtime" / "style_gallery"
    records_dir = runtime / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = records_dir / "style_samples.jsonl"

    # Patch the module-level path constants
    monkeypatch.setattr(sg_store, "_RUNTIME", runtime)
    monkeypatch.setattr(sg_store, "_RECORDS_DIR", records_dir)
    monkeypatch.setattr(sg_store, "_JSONL_PATH", jsonl_path)
    return records_dir


def make_sample(
    sample_id: str,
    path: str = "",
    poster: str = "",
    audio_url: str = "",
    srt_url: str = "",
    manifest_url: str = "",
    status: str = "candidate",
) -> StyleSample:
    out = StyleSampleOutput(
        type="mp4",
        path=path,
        poster=poster,
        audio_url=audio_url,
        srt_url=srt_url,
        manifest_url=manifest_url,
    )
    return StyleSample(
        id=sample_id,
        route_id="local_frame_compose",
        route_name="Pillow 信息卡路线",
        style_name="测试风格",
        description="测试描述",
        status=SampleStatus(status),
        params={},
        output=out,
        tags=[],
        created_at=datetime.utcnow(),
    )


# ─── URL Resolution Tests ────────────────────────────────────────────────────

class TestToRuntimeUrl:
    """Test the to_runtime_url helper in various path formats."""

    def test_absolute_runtime_path_unchanged(self):
        assert sg_store.to_runtime_url("/runtime/video_lab/experiments/abc/final.mp4") == \
            "/runtime/video_lab/experiments/abc/final.mp4"

    def test_runtime_prefix_without_leading_slash(self):
        assert sg_store.to_runtime_url("runtime/video_lab/experiments/abc/final.mp4") == \
            "/runtime/video_lab/experiments/abc/final.mp4"

    def test_video_lab_path(self):
        assert sg_store.to_runtime_url("video_lab/experiments/abc/final.mp4") == \
            "/runtime/video_lab/experiments/abc/final.mp4"

    def test_style_gallery_path(self):
        assert sg_store.to_runtime_url("style_gallery/remotion/xyz.mp4") == \
            "/runtime/style_gallery/remotion/xyz.mp4"

    def test_remotion_path_defaults_to_style_gallery(self):
        assert sg_store.to_runtime_url("remotion/xyz.mp4") == \
            "/runtime/style_gallery/remotion/xyz.mp4"

    def test_already_has_runtime_style_gallery(self):
        assert sg_store.to_runtime_url("/runtime/style_gallery/remotion/xyz.mp4") == \
            "/runtime/style_gallery/remotion/xyz.mp4"

    def test_http_url_unchanged(self):
        assert sg_store.to_runtime_url("https://example.com/video.mp4") == \
            "https://example.com/video.mp4"

    def test_empty_string(self):
        assert sg_store.to_runtime_url("") == ""

    def test_root_path(self):
        assert sg_store.to_runtime_url("/") == ""


class TestResolveSampleUrls:
    """Test resolve_sample_urls with different path formats."""

    def test_resolve_video_lab_experiments_path(self, temp_records_dir):
        sample = make_sample("s1", path="video_lab/experiments/abc/final.mp4")
        urls = sg_store.resolve_sample_urls(sample)
        assert urls["video_url"] == "/runtime/video_lab/experiments/abc/final.mp4"

    def test_resolve_runtime_absolute_path(self, temp_records_dir):
        sample = make_sample("s2", path="/runtime/video_lab/experiments/def/g.mp4")
        urls = sg_store.resolve_sample_urls(sample)
        assert urls["video_url"] == "/runtime/video_lab/experiments/def/g.mp4"

    def test_resolve_style_gallery_path(self, temp_records_dir):
        sample = make_sample("s3", path="style_gallery/remotion/xyz.mp4")
        urls = sg_store.resolve_sample_urls(sample)
        assert urls["video_url"] == "/runtime/style_gallery/remotion/xyz.mp4"

    def test_resolve_remotion_path(self, temp_records_dir):
        sample = make_sample("s4", path="remotion/motion.mp4")
        urls = sg_store.resolve_sample_urls(sample)
        assert urls["video_url"] == "/runtime/style_gallery/remotion/motion.mp4"

    def test_resolve_multiple_fields(self, temp_records_dir):
        sample = make_sample(
            "s5",
            path="video_lab/experiments/abc/final.mp4",
            poster="video_lab/experiments/abc/poster.jpg",
            audio_url="video_lab/experiments/abc/audio.mp3",
            srt_url="video_lab/experiments/abc/subs.srt",
            manifest_url="video_lab/experiments/abc/manifest.json",
        )
        urls = sg_store.resolve_sample_urls(sample)
        assert urls["video_url"] == "/runtime/video_lab/experiments/abc/final.mp4"
        assert urls["poster_url"] == "/runtime/video_lab/experiments/abc/poster.jpg"
        assert urls["audio_url"] == "/runtime/video_lab/experiments/abc/audio.mp3"
        assert urls["srt_url"] == "/runtime/video_lab/experiments/abc/subs.srt"
        assert urls["manifest_url"] == "/runtime/video_lab/experiments/abc/manifest.json"

    def test_resolve_empty_fields(self, temp_records_dir):
        sample = make_sample("s6", path="", poster="", audio_url="")
        urls = sg_store.resolve_sample_urls(sample)
        assert urls["video_url"] == ""
        assert urls["poster_url"] == ""
        assert urls["audio_url"] == ""


# ─── Delete Tests ───────────────────────────────────────────────────────────

class TestDeleteSample:
    """Test that delete_sample only removes the record, not files."""

    def test_delete_removes_record(self, temp_records_dir):
        sample = make_sample("del_s1", path="some_path.mp4")
        sg_store.save_sample(sample)

        # Verify record exists
        retrieved = sg_store.get_sample("del_s1")
        assert retrieved is not None

        # Delete
        deleted = sg_store.delete_sample("del_s1")
        assert deleted is True

        # Verify record is gone
        assert sg_store.get_sample("del_s1") is None

    def test_delete_nonexistent_returns_false(self, temp_records_dir):
        deleted = sg_store.delete_sample("nonexistent_id")
        assert deleted is False

    def test_delete_only_affects_target(self, temp_records_dir):
        s1 = make_sample("del_s2", path="p1.mp4")
        s2 = make_sample("del_s3", path="p2.mp4")
        sg_store.save_sample(s1)
        sg_store.save_sample(s2)

        sg_store.delete_sample("del_s2")

        assert sg_store.get_sample("del_s2") is None
        assert sg_store.get_sample("del_s3") is not None


# ─── Status Management Tests ───────────────────────────────────────────────

class TestSampleStatusManagement:
    """Test sample status transitions via save_sample."""

    def test_status_default_is_candidate(self, temp_records_dir):
        sample = make_sample("st_s1", status="candidate")
        sg_store.save_sample(sample)
        retrieved = sg_store.get_sample("st_s1")
        assert retrieved is not None
        assert retrieved.status == SampleStatus.CANDIDATE

    def test_status_can_be_updated_to_comparing(self, temp_records_dir):
        sample = make_sample("st_s2", status="candidate")
        sg_store.save_sample(sample)

        sample.status = SampleStatus.COMPARING
        sg_store.save_sample(sample)

        retrieved = sg_store.get_sample("st_s2")
        assert retrieved.status == SampleStatus.COMPARING

    def test_status_transition_comparing_to_candidate(self, temp_records_dir):
        sample = make_sample("st_s3", status="comparing")
        sg_store.save_sample(sample)

        sample.status = SampleStatus.CANDIDATE
        sg_store.save_sample(sample)

        retrieved = sg_store.get_sample("st_s3")
        assert retrieved.status == SampleStatus.CANDIDATE


# ─── V1.2.3: New field tests ─────────────────────────────────────────────────

class TestFindSampleBySource:
    """V1.2.3: find_sample_by_source bypasses limit cap for idempotency checks."""

    def test_find_sample_by_source_finds_exact_match(self, temp_records_dir):
        """find_sample_by_source returns the sample when source fields match."""
        from app.video_lab.style_gallery.models import SampleSource, SampleGenerationMeta

        s1 = make_sample("src_001")
        s1.source = SampleSource(source_type="style_sweep", job_id="job_abc", run_id="style_x")
        sg_store.save_sample(s1)

        found = sg_store.find_sample_by_source("style_sweep", "job_abc", "style_x")
        assert found is not None
        assert found.id == "src_001"

    def test_find_sample_by_source_returns_none_when_no_match(self, temp_records_dir):
        """find_sample_by_source returns None when no sample matches."""
        found = sg_store.find_sample_by_source("style_sweep", "nonexistent_job", "style_y")
        assert found is None

    def test_find_sample_by_source_returns_most_recent_when_multiple(self, temp_records_dir):
        """When multiple samples match, returns the most recently created one."""
        from app.video_lab.style_gallery.models import SampleSource
        import time

        # First sample (older)
        s1 = make_sample("src_old")
        s1.source = SampleSource(source_type="style_sweep", job_id="job_multi", run_id="style_m")
        sg_store.save_sample(s1)

        # Second sample (newer) — slightly different id
        s2 = make_sample("src_new")
        s2.source = SampleSource(source_type="style_sweep", job_id="job_multi", run_id="style_m")
        time.sleep(0.01)  # ensure different timestamps
        sg_store.save_sample(s2)

        found = sg_store.find_sample_by_source("style_sweep", "job_multi", "style_m")
        assert found is not None
        assert found.id == "src_new"  # most recent

    def test_find_sample_by_source_wrong_source_type_returns_none(self, temp_records_dir):
        """source_type must match exactly."""
        from app.video_lab.style_gallery.models import SampleSource

        s1 = make_sample("src_type_001")
        s1.source = SampleSource(source_type="workbench", job_id="job_wb", run_id="run_wb")
        sg_store.save_sample(s1)

        # Different source_type — not found
        found = sg_store.find_sample_by_source("style_sweep", "job_wb", "run_wb")
        assert found is None


class TestContinuousUpdateNoDuplicate:
    """V1.2.3: save_sample() to the same ID must overwrite, not create duplicates."""

    def test_continuous_updates_same_id_no_duplicate(self, temp_records_dir):
        """Calling save_sample() multiple times with the same ID must not create multiple records."""
        sample = make_sample("dup_001")
        sg_store.save_sample(sample)

        # Update the same sample 4 times: APPROVED → CANDIDATE → APPROVED → CANDIDATE
        for i in range(4):
            sample.status = SampleStatus.CANDIDATE if i % 2 == 1 else SampleStatus.APPROVED
            sg_store.save_sample(sample)

        # Only one record with this ID should exist
        records = sg_store._read_all()
        matching = [r for r in records if r.get("id") == "dup_001"]
        assert len(matching) == 1

        # The last status should be preserved (last i=3 → CANDIDATE)
        retrieved = sg_store.get_sample("dup_001")
        assert retrieved is not None
        assert retrieved.status == SampleStatus.CANDIDATE

    def test_concurrent_saves_same_id_no_corruption(self, temp_records_dir):
        """Concurrent save_sample() calls for the same ID must not corrupt the record."""
        import threading

        sample = make_sample("concurrent_001")
        sg_store.save_sample(sample)

        errors: list[str] = []

        def update_status(idx: int):
            try:
                s = sg_store.get_sample("concurrent_001")
                if s:
                    s.status = SampleStatus.APPROVED if idx % 2 == 0 else SampleStatus.CANDIDATE
                    sg_store.save_sample(s)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=update_status, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent save errors: {errors}"
        # Should still have exactly 1 record
        records = sg_store._read_all()
        matching = [r for r in records if r.get("id") == "concurrent_001"]
        assert len(matching) == 1
        # Record should still be valid (not corrupted JSON)
        retrieved = sg_store.get_sample("concurrent_001")
        assert retrieved is not None
        assert retrieved.id == "concurrent_001"


class TestNewAspectRatioFields:
    """V1.2.3: generation and asset_meta new aspect ratio fields roundtrip correctly."""

    def test_generation_output_aspect_ratio_field_saves_and_retrieves(self, temp_records_dir):
        """generation.output_aspect_ratio is persisted correctly."""
        from app.video_lab.style_gallery.models import SampleGenerationMeta

        sample = make_sample("gen_ar_001")
        sample.generation = SampleGenerationMeta(
            visual_route="pillow",
            aspect_ratio="9:16",
            output_aspect_ratio="9:16",
            display_aspect_ratio="9:16.0",
            fit_mode="cover",
        )
        sg_store.save_sample(sample)

        retrieved = sg_store.get_sample("gen_ar_001")
        assert retrieved is not None
        assert retrieved.generation.output_aspect_ratio == "9:16"
        assert retrieved.generation.display_aspect_ratio == "9:16.0"
        assert retrieved.generation.fit_mode == "cover"

    def test_asset_meta_aspect_ratio_fields_saves_and_retrieves(self, temp_records_dir):
        """asset_meta.aspect_ratio, display_aspect_ratio, fit_mode are persisted correctly."""
        from app.video_lab.style_gallery.models import SampleAssetMeta

        sample = make_sample("asset_ar_001")
        sample.asset_meta = SampleAssetMeta(
            final_video_url="/runtime/out.mp4",
            aspect_ratio="16:9",
            display_aspect_ratio="16:9",
            fit_mode="contain",
        )
        sg_store.save_sample(sample)

        retrieved = sg_store.get_sample("asset_ar_001")
        assert retrieved is not None
        assert retrieved.asset_meta.aspect_ratio == "16:9"
        assert retrieved.asset_meta.display_aspect_ratio == "16:9"
        assert retrieved.asset_meta.fit_mode == "contain"

    def test_old_record_missing_new_fields_still_loads(self):
        """A record saved before V1.2.3 (without new fields) still loads via from_dict."""
        from app.video_lab.style_gallery.models import StyleSample

        old_record = {
            "id": "pre_v123_001",
            "route_id": "local_frame_compose",
            "route_name": "旧路线",
            "style_name": "旧风格",
            "description": "",
            "status": "candidate",
            "params": {},
            "output": {
                "type": "mp4",
                "path": "out.mp4",
                "poster": "",
                "audio_url": "",
                "srt_url": "",
                "manifest_url": "",
            },
            "evaluation": {
                "readability": None, "motion": None, "visual_impact": None,
                "stability": None, "cost": None, "notes": "",
            },
            "tags": [],
            "content_preview": "",
            "duration_sec": 0.0,
            "audio_duration_sec": 0.0,
            "created_at": "2025-01-01T00:00:00",
            "visual_judgement": None,
            # V1.0.5 fields present
            "source": {"source_type": "workbench"},
            "generation": {
                "visual_route": "pillow",
                "aspect_ratio": "9:16",
            },
            "asset_meta": {
                "final_video_url": "/runtime/out.mp4",
            },
            "quality_meta": {},
            "review_meta": {},
            "job_run": {},
            "schema_version": "1.0.5",
            # V1.2.3 fields intentionally absent
        }
        sample = StyleSample.from_dict(old_record)
        assert sample.generation.output_aspect_ratio == ""  # default
        assert sample.generation.display_aspect_ratio == ""  # default
        assert sample.generation.fit_mode == ""  # default
        assert sample.asset_meta.aspect_ratio == ""  # default
        assert sample.asset_meta.display_aspect_ratio == ""  # default
        assert sample.asset_meta.fit_mode == ""  # default
