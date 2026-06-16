"""
tests/test_style_gallery_asset_formalization.py
V1.0.5: Style Gallery asset formalization — source/generation/asset_meta/quality_meta/review_meta/job_run
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from app.video_lab.style_gallery.models import (
    StyleSample, SampleStatus, StyleSampleOutput, EvaluationScore,
    SampleSource, SampleGenerationMeta, SampleAssetMeta,
    SampleQualityMeta, SampleReviewMeta,
)
from app.video_lab.style_gallery import store as sg_store


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_records_dir(monkeypatch, tmp_path):
    """Redirect store path constants to a temp directory."""
    runtime = tmp_path / "runtime" / "style_gallery"
    records_dir = runtime / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = records_dir / "style_samples.jsonl"

    monkeypatch.setattr(sg_store, "_RUNTIME", runtime)
    monkeypatch.setattr(sg_store, "_RECORDS_DIR", records_dir)
    monkeypatch.setattr(sg_store, "_JSONL_PATH", jsonl_path)
    return records_dir


def make_base_sample(sample_id: str, **overrides) -> StyleSample:
    """Make a minimal StyleSample for testing."""
    out = StyleSampleOutput(
        type="mp4",
        path="video_lab/experiments/abc/final.mp4",
        poster="video_lab/experiments/abc/poster.jpg",
        audio_url="video_lab/experiments/abc/audio.mp3",
        srt_url="video_lab/experiments/abc/subs.srt",
        manifest_url="video_lab/experiments/abc/manifest.json",
    )
    kwargs = dict(
        id=sample_id,
        route_id="local_frame_compose",
        route_name="Pillow 信息卡路线",
        style_name="测试风格",
        description="测试描述",
        status=SampleStatus.CANDIDATE,
        params={},
        output=out,
        tags=["workbench", "test"],
        created_at=datetime.utcnow(),
    )
    kwargs.update(overrides)
    return StyleSample(**kwargs)


# ─── Backward Compatibility Tests ─────────────────────────────────────────────

class TestOldRecordBackwardCompat:
    """V1.0.5: Old records without new fields must still load via from_dict."""

    def test_old_record_without_asset_fields_loads_successfully(self):
        """Old V0.4 record dict should not raise on from_dict."""
        old_record = {
            "id": "sample_old_001",
            "route_id": "local_frame_compose",
            "route_name": "Pillow 信息卡路线",
            "style_name": "旧风格",
            "description": "旧记录",
            "status": "candidate",
            "params": {},
            "output": {
                "type": "mp4",
                "path": "video_lab/experiments/abc/final.mp4",
                "poster": "",
                "audio_url": "",
                "srt_url": "",
                "manifest_url": "",
            },
            "evaluation": {
                "readability": None,
                "motion": None,
                "visual_impact": None,
                "stability": None,
                "cost": None,
                "notes": "",
            },
            "tags": ["old"],
            "content_preview": "",
            "duration_sec": 30.0,
            "audio_duration_sec": 28.0,
            "created_at": datetime.utcnow().isoformat(),
            "visual_judgement": None,
        }
        sample = StyleSample.from_dict(old_record)
        assert sample.id == "sample_old_001"
        # New fields must be present with defaults
        assert sample.source is not None
        assert sample.generation is not None
        assert sample.asset_meta is not None
        assert sample.quality_meta is not None
        assert sample.review_meta is not None
        assert sample.job_run == {}
        assert sample.schema_version == "1.0.4"  # pre-formalization marker

    def test_old_record_to_dict_roundtrip(self):
        """Old record dict → from_dict → to_dict must not lose old fields."""
        old_record = {
            "id": "sample_old_002",
            "route_id": "remotion_card_stack",
            "route_name": "Remotion 卡片堆叠",
            "style_name": "旧风格2",
            "description": "",
            "status": "approved",
            "params": {"aspectRatio": "9:16"},
            "output": {
                "type": "mp4",
                "path": "remotion/out.mp4",
                "poster": "",
                "audio_url": "",
                "srt_url": "",
                "manifest_url": "",
            },
            "evaluation": {
                "readability": 4,
                "motion": 3,
                "visual_impact": 5,
                "stability": 4,
                "cost": 3,
                "notes": "ok",
            },
            "tags": [],
            "content_preview": "测试内容",
            "duration_sec": 45.0,
            "audio_duration_sec": 44.0,
            "created_at": datetime.utcnow().isoformat(),
            "visual_judgement": None,
        }
        sample = StyleSample.from_dict(old_record)
        d = sample.to_dict()
        assert d["id"] == "sample_old_002"
        assert d["route_id"] == "remotion_card_stack"
        assert d["status"] == "approved"
        assert d["tags"] == []
        assert d["visual_judgement"] is None


# ─── New Asset Fields Tests ──────────────────────────────────────────────────

class TestNewAssetFields:
    """V1.0.5: New asset metadata fields roundtrip correctly."""

    def test_full_asset_fields_save_and_retrieve(self, temp_records_dir):
        """Save a sample with all V1.0.5 fields and retrieve them."""
        source = SampleSource(
            source_type="workbench",
            source_page="/video-lab/workbench",
            source_run_id="run_abc123",
            experiment_id="exp_xyz",
            job_id="job_789",
            run_id="run_abc123",
            workbench_route="pillow",
            saved_from="full_video_result",
        )
        generation = SampleGenerationMeta(
            visual_route="pillow",
            visual_profile="keypoint_v2",
            remotion_family="",
            route_preset="pillow",
            aspect_ratio="9:16",
            target_duration=45.0,
            key_point_count=6,
            content_hash="abc123hash",
        )
        asset_meta = SampleAssetMeta(
            final_video_url="/runtime/video_lab/experiments/abc/final.mp4",
            cover_url="/runtime/video_lab/experiments/abc/poster.jpg",
            audio_url="/runtime/video_lab/experiments/abc/audio.mp3",
            srt_url="/runtime/video_lab/experiments/abc/subs.srt",
            manifest_url="/runtime/video_lab/experiments/abc/manifest.json",
            runtime_prefix="/runtime",
            artifact_count=5,
        )
        quality_meta = SampleQualityMeta(
            structural_score=82.5,
            visual_score=78.0,
            warnings=["low_brightness"],
            steps=[{"name": "plan", "status": "succeeded"}],
        )
        review_meta = SampleReviewMeta(
            review_status="approved",
            review_notes="looks good",
            problem_tags=[],
        )
        job_run = {
            "jobId": "job_789",
            "runId": "run_abc123",
            "experimentId": "exp_xyz",
            "status": "succeeded",
            "stage": "compose",
            "progress": 100,
        }

        sample = make_base_sample(
            "sample_v105_001",
            source=source,
            generation=generation,
            asset_meta=asset_meta,
            quality_meta=quality_meta,
            review_meta=review_meta,
            job_run=job_run,
            schema_version="1.0.5",
        )

        sg_store.save_sample(sample)
        retrieved = sg_store.get_sample("sample_v105_001")

        assert retrieved is not None
        assert retrieved.source.source_type == "workbench"
        assert retrieved.source.experiment_id == "exp_xyz"
        assert retrieved.source.run_id == "run_abc123"
        assert retrieved.generation.visual_route == "pillow"
        assert retrieved.generation.visual_profile == "keypoint_v2"
        assert retrieved.generation.aspect_ratio == "9:16"
        assert retrieved.generation.key_point_count == 6
        assert retrieved.asset_meta.final_video_url == "/runtime/video_lab/experiments/abc/final.mp4"
        assert retrieved.asset_meta.artifact_count == 5
        assert retrieved.quality_meta.structural_score == 82.5
        assert retrieved.quality_meta.warnings == ["low_brightness"]
        assert retrieved.review_meta.review_status == "approved"
        assert retrieved.review_meta.review_notes == "looks good"
        assert retrieved.job_run["jobId"] == "job_789"
        assert retrieved.job_run["status"] == "succeeded"
        assert retrieved.schema_version == "1.0.5"

    def test_partial_asset_fields_use_defaults(self, temp_records_dir):
        """Sample with only some new fields — missing ones get defaults."""
        sample = make_base_sample(
            "sample_v105_002",
            source=SampleSource(source_type="style_gallery"),
            # generation, asset_meta, quality_meta, review_meta omitted → defaults
            job_run={"runId": "run_partial"},
            schema_version="1.0.5",
        )
        sg_store.save_sample(sample)
        retrieved = sg_store.get_sample("sample_v105_002")

        assert retrieved is not None
        assert retrieved.source.source_type == "style_gallery"
        assert retrieved.generation.visual_route == ""  # default
        assert retrieved.asset_meta.final_video_url == ""  # default
        assert retrieved.quality_meta.structural_score is None  # default
        assert retrieved.review_meta.review_status == ""  # default
        assert retrieved.job_run["runId"] == "run_partial"

    def test_to_dict_includes_all_new_fields(self):
        """to_dict must output all new fields (not drop them)."""
        sample = make_base_sample(
            "sample_v105_003",
            source=SampleSource(source_type="workbench", experiment_id="exp_test"),
            generation=SampleGenerationMeta(visual_route="pillow", aspect_ratio="16:9"),
            schema_version="1.0.5",
        )
        d = sample.to_dict()
        assert "source" in d
        assert "generation" in d
        assert "asset_meta" in d
        assert "quality_meta" in d
        assert "review_meta" in d
        assert "job_run" in d
        assert "schema_version" in d
        assert d["source"]["source_type"] == "workbench"
        assert d["generation"]["aspect_ratio"] == "16:9"


# ─── Filter Tests ────────────────────────────────────────────────────────────

class TestListSamplesFiltering:
    """V1.0.5: list_samples supports source_type and tag filters."""

    def test_filter_by_source_type(self, temp_records_dir):
        """source_type filter should only return samples with matching source.source_type."""
        s1 = make_base_sample("s_filter_001", tags=["tag_a"],
                             source=SampleSource(source_type="workbench"))
        s2 = make_base_sample("s_filter_002", tags=["tag_a"],
                             source=SampleSource(source_type="style_gallery"))
        s3 = make_base_sample("s_filter_003", tags=["tag_b"],
                             source=SampleSource(source_type="workbench"))
        for s in (s1, s2, s3):
            sg_store.save_sample(s)

        results = sg_store.list_samples(source_type="workbench")
        assert len(results) == 2
        ids = {r.id for r in results}
        assert ids == {"s_filter_001", "s_filter_003"}

    def test_filter_by_tag(self, temp_records_dir):
        """tag filter should only return samples containing that tag."""
        s1 = make_base_sample("s_tag_001", tags=["news", "breaking"])
        s2 = make_base_sample("s_tag_002", tags=["news", "analysis"])
        s3 = make_base_sample("s_tag_003", tags=["entertainment"])
        for s in (s1, s2, s3):
            sg_store.save_sample(s)

        results = sg_store.list_samples(tag="news")
        assert len(results) == 2
        ids = {r.id for r in results}
        assert ids == {"s_tag_001", "s_tag_002"}

    def test_filter_by_source_type_and_tag_combined(self, temp_records_dir):
        """source_type and tag filters can be combined."""
        s1 = make_base_sample("s_combo_001", tags=["gold"],
                             source=SampleSource(source_type="workbench"))
        s2 = make_base_sample("s_combo_002", tags=["gold"],
                             source=SampleSource(source_type="style_gallery"))
        s3 = make_base_sample("s_combo_003", tags=["silver"],
                             source=SampleSource(source_type="workbench"))
        for s in (s1, s2, s3):
            sg_store.save_sample(s)

        results = sg_store.list_samples(source_type="workbench", tag="gold")
        assert len(results) == 1
        assert results[0].id == "s_combo_001"

    def test_filter_no_match_returns_empty(self, temp_records_dir):
        """Filtering with no matching samples returns empty list."""
        s1 = make_base_sample("s_empty_001", tags=["only"],
                             source=SampleSource(source_type="workbench"))
        sg_store.save_sample(s1)
        results = sg_store.list_samples(source_type="nonexistent_type")
        assert results == []

    def test_filter_without_new_fields_still_matches(self, temp_records_dir):
        """Old records (no source_type field) should not match source_type filter."""
        old_record = {
            "id": "s_old_filter",
            "route_id": "local_frame_compose",
            "route_name": "旧路线",
            "style_name": "旧风格",
            "description": "",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "", "poster": "", "audio_url": "", "srt_url": "", "manifest_url": ""},
            "evaluation": {"readability": None, "motion": None, "visual_impact": None, "stability": None, "cost": None, "notes": ""},
            "tags": ["workbench"],
            "content_preview": "",
            "duration_sec": 0.0,
            "audio_duration_sec": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "visual_judgement": None,
        }
        sg_store.save_sample(StyleSample.from_dict(old_record))

        # Old record has source_type="unknown" after from_dict default-fill,
        # so filtering by "unknown" should return it
        results = sg_store.list_samples(source_type="unknown")
        assert len(results) == 1
        assert results[0].id == "s_old_filter"

        # Filtering by a specific type should not return old record
        results2 = sg_store.list_samples(source_type="workbench")
        assert all(r.source.source_type == "workbench" for r in results2)


# ─── Router Integration Tests ────────────────────────────────────────────────

class TestSaveStyleSampleRouter:
    """Test that POST /style-samples through the router handles V1.0.5 fields."""

    def test_save_request_missing_new_fields_still_succeeds(self, temp_records_dir):
        """A request without new asset fields should not 422 — defaults fill in."""
        from app.video_lab.schemas import StyleSampleSaveRequest

        # Minimal old-style request
        req = StyleSampleSaveRequest(
            id="s_req_001",
            route_id="local_frame_compose",
            route_name="Pillow 信息卡路线",
            style_name="测试",
            description="",
            status="candidate",
            params={},
            output_type="mp4",
            output_path="out.mp4",
            poster_path="",
            audio_url="",
            srt_url="",
            manifest_url="",
            content_preview="",
            duration_sec=0.0,
            audio_duration_sec=0.0,
            tags=[],
        )
        # New fields must have defaults — no FieldError
        assert req.source == {}
        assert req.generation == {}
        assert req.asset_meta == {}
        assert req.quality_meta == {}
        assert req.review_meta == {}
        assert req.job_run == {}
        assert req.schema_version == "1.0.5"

    def test_save_request_with_new_fields_succeeds(self, temp_records_dir):
        """A request with all V1.0.5 fields should be accepted."""
        from app.video_lab.schemas import StyleSampleSaveRequest

        req = StyleSampleSaveRequest(
            id="s_req_002",
            route_id="pillow",
            route_name="Pillow",
            style_name="测试",
            description="",
            status="approved",
            params={},
            output_type="mp4",
            output_path="out.mp4",
            poster_path="poster.jpg",
            audio_url="audio.mp3",
            srt_url="subs.srt",
            manifest_url="manifest.json",
            content_preview="",
            duration_sec=30.0,
            audio_duration_sec=28.0,
            tags=["workbench"],
            source={"source_type": "workbench", "experiment_id": "exp_001"},
            generation={"visual_route": "pillow", "aspect_ratio": "9:16"},
            asset_meta={"final_video_url": "/runtime/out.mp4", "artifact_count": 3},
            quality_meta={"structural_score": 80.0, "warnings": ["dim"]},
            review_meta={"review_status": "approved", "review_notes": "ok"},
            job_run={"runId": "run_001", "status": "succeeded"},
            schema_version="1.0.5",
        )
        assert req.source["source_type"] == "workbench"
        assert req.generation["aspect_ratio"] == "9:16"
        assert req.quality_meta["structural_score"] == 80.0


# ─── Resolve URLs Unchanged ─────────────────────────────────────────────────

class TestResolveUrlsUnchanged:
    """resolve_sample_urls must behave exactly as before V1.0.5."""

    def test_resolve_urls_still_works(self, temp_records_dir):
        """resolve_sample_urls should not be affected by new fields."""
        sample = make_base_sample("s_url_001")
        urls = sg_store.resolve_sample_urls(sample)
        assert urls["video_url"] == "/runtime/video_lab/experiments/abc/final.mp4"
        assert urls["poster_url"] == "/runtime/video_lab/experiments/abc/poster.jpg"
        assert urls["audio_url"] == "/runtime/video_lab/experiments/abc/audio.mp3"
        assert urls["srt_url"] == "/runtime/video_lab/experiments/abc/subs.srt"
        assert urls["manifest_url"] == "/runtime/video_lab/experiments/abc/manifest.json"
