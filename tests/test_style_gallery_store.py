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
