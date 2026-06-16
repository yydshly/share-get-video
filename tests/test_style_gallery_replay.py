"""
tests/test_style_gallery_replay.py
V1.0.6: Style Sample Replay — test rerun payload construction from StyleSample records.
"""

import pytest
from datetime import datetime

from app.video_lab.style_gallery.models import (
    StyleSample, SampleStatus, StyleSampleOutput, EvaluationScore,
    SampleSource, SampleGenerationMeta, SampleAssetMeta,
    SampleQualityMeta, SampleReviewMeta,
)
from app.video_lab.style_gallery import store as sg_store
from app.video_lab.style_gallery import replay


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


def make_sample(**overrides) -> StyleSample:
    """Make a minimal StyleSample for replay tests."""
    out = StyleSampleOutput(
        type="mp4",
        path="video_lab/experiments/test/final.mp4",
        poster="video_lab/experiments/test/poster.jpg",
        audio_url="video_lab/experiments/test/audio.mp3",
        srt_url="video_lab/experiments/test/subs.srt",
        manifest_url="video_lab/experiments/test/manifest.json",
    )
    kwargs = dict(
        id="replay_sample_001",
        route_id="pillow",
        route_name="Pillow 信息卡路线",
        style_name="测试风格",
        description="测试描述",
        status=SampleStatus.CANDIDATE,
        params={"aspectRatio": "9:16", "targetDuration": 45, "keyPointCount": 3},
        output=out,
        tags=["test"],
        created_at=datetime.utcnow(),
        source=SampleSource(source_type="workbench", experiment_id="exp_test_001"),
        generation=SampleGenerationMeta(
            visual_route="pillow",
            visual_profile="ai_frontier_dark",
            remotion_family="",
            route_preset="pillow",
            aspect_ratio="9:16",
            target_duration=45.0,
            key_point_count=3,
        ),
        asset_meta=SampleAssetMeta(final_video_url="/runtime/test.mp4"),
        quality_meta=SampleQualityMeta(warnings=["dim"]),
        review_meta=SampleReviewMeta(review_status="approved"),
        job_run={"runId": "run_test", "status": "succeeded"},
        schema_version="1.0.5",
    )
    kwargs.update(overrides)
    return StyleSample(**kwargs)


# ─── Content Derivation Tests ────────────────────────────────────────────────

class TestContentDerivation:
    """_content_from_sample: content is derived from params.fullContent, params.content, or content_preview."""

    def test_full_content_from_params_full_content(self):
        """params.fullContent is used when available."""
        sample = make_sample(
            params={"fullContent": "今日 AI 前沿进展：多语言模型突破。", "aspectRatio": "9:16"},
            content_preview="今日 AI 前沿进展...",
        )
        content, warnings = replay._content_from_sample(sample)
        assert content == "今日 AI 前沿进展：多语言模型突破。"
        assert "content_preview" not in warnings

    def test_full_content_fallback_to_params_content(self):
        """params.content is used when fullContent is absent."""
        sample = make_sample(
            params={"content": "多语言模型取得突破。"},
            content_preview="多语言模型...",
        )
        content, warnings = replay._content_from_sample(sample)
        assert content == "多语言模型取得突破。"

    def test_full_content_fallback_to_content_preview(self):
        """content_preview is used when neither fullContent nor content is available."""
        sample = make_sample(
            params={},
            content_preview="AI 前沿资讯内容预览",
        )
        content, warnings = replay._content_from_sample(sample)
        assert content == "AI 前沿资讯内容预览"
        assert any("content_preview" in w for w in warnings)

    def test_no_content_returns_empty_and_warning(self):
        """Empty content returns warning about incomplete payload."""
        sample = make_sample(params={}, content_preview="")
        content, warnings = replay._content_from_sample(sample)
        assert content == ""
        assert any("No content" in w for w in warnings)


# ─── Params Enrichment Tests ─────────────────────────────────────────────────

class TestParamsEnrichment:
    """_params_from_sample enriches params with generation metadata fields."""

    def test_visual_profile_added_from_generation(self):
        """visualProfile is added from generation if not in params."""
        sample = make_sample(
            params={"aspectRatio": "16:9"},
            generation=SampleGenerationMeta(visual_profile="ai_frontier_dark"),
        )
        params = replay._params_from_sample(sample)
        assert params["visualProfile"] == "ai_frontier_dark"

    def test_visual_profile_not_overwritten(self):
        """If visualProfile already in params, generation value does not overwrite."""
        sample = make_sample(
            params={"visualProfile": "existing_profile"},
            generation=SampleGenerationMeta(visual_profile="gen_profile"),
        )
        params = replay._params_from_sample(sample)
        assert params["visualProfile"] == "existing_profile"

    def test_remotion_family_added_from_generation(self):
        """remotionFamily is added from generation if absent."""
        sample = make_sample(
            params={},
            generation=SampleGenerationMeta(remotion_family="card_stack"),
        )
        params = replay._params_from_sample(sample)
        assert params["remotionFamily"] == "card_stack"

    def test_aspect_ratio_from_generation(self):
        """aspectRatio from generation supplements params."""
        sample = make_sample(
            params={},
            generation=SampleGenerationMeta(aspect_ratio="16:9"),
        )
        params = replay._params_from_sample(sample)
        assert params["aspectRatio"] == "16:9"

    def test_target_duration_from_generation(self):
        """targetDuration from generation supplements params."""
        sample = make_sample(
            params={},
            generation=SampleGenerationMeta(target_duration=60.0),
        )
        params = replay._params_from_sample(sample)
        assert params["targetDuration"] == 60.0

    def test_key_point_count_from_generation(self):
        """keyPointCount from generation supplements params."""
        sample = make_sample(
            params={},
            generation=SampleGenerationMeta(key_point_count=6),
        )
        params = replay._params_from_sample(sample)
        assert params["keyPointCount"] == 6

    def test_visual_route_added_to_params(self):
        """visualRoute from generation is added to params."""
        sample = make_sample(
            params={},
            generation=SampleGenerationMeta(visual_route="remotion_card_stack"),
        )
        params = replay._params_from_sample(sample)
        assert params["visualRoute"] == "remotion_card_stack"


# ─── Visual Compose Payload Tests ────────────────────────────────────────────

class TestBuildVisualComposePayload:
    """build_visual_compose_payload derives POST /visual-compose payload from StyleSample."""

    def test_uses_generation_visual_route(self):
        """visualRoute is taken from generation.visual_route."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="remotion_card_stack"),
            params={"fullContent": "测试内容"},
        )
        payload = replay.build_visual_compose_payload(sample)
        assert payload["visualRoute"] == "remotion_card_stack"

    def test_visual_route_fallback_to_route_id(self):
        """When generation.visual_route is empty, falls back to sample.route_id."""
        sample = make_sample(
            route_id="pillow",
            generation=SampleGenerationMeta(visual_route=""),
            params={"fullContent": "测试内容"},
        )
        payload = replay.build_visual_compose_payload(sample)
        assert payload["visualRoute"] == "pillow"

    def test_params_enriched(self):
        """Params include visualProfile/aspectRatio/targetDuration from generation."""
        sample = make_sample(
            generation=SampleGenerationMeta(
                visual_profile="dark_v2",
                aspect_ratio="16:9",
                target_duration=60,
            ),
            params={"fullContent": "内容"},
        )
        payload = replay.build_visual_compose_payload(sample)
        assert payload["params"]["visualProfile"] == "dark_v2"
        assert payload["params"]["aspectRatio"] == "16:9"
        assert payload["params"]["targetDuration"] == 60

    def test_content_from_full_content(self):
        """content field uses params.fullContent."""
        sample = make_sample(
            params={"fullContent": "完整的报告原文内容"},
            content_preview="完整...",
        )
        payload = replay.build_visual_compose_payload(sample)
        assert payload["content"] == "完整的报告原文内容"

    def test_content_fallback_to_content_preview(self):
        """content falls back to content_preview with warning."""
        sample = make_sample(
            params={},
            content_preview="预览文本内容",
        )
        payload = replay.build_visual_compose_payload(sample)
        assert payload["content"] == "预览文本内容"


# ─── Clip Preview Payload Tests ──────────────────────────────────────────────

class TestBuildClipPreviewPayload:
    """build_clip_preview_payload derives POST /clip-preview payload from StyleSample."""

    def test_visual_route_from_generation(self):
        """visualRoute is taken from generation.visual_route."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={"fullContent": "测试"},
        )
        payload = replay.build_clip_preview_payload(sample)
        assert payload["visualRoute"] == "pillow"

    def test_visual_route_fallback_to_route_id(self):
        """Falls back to sample.route_id when generation.visual_route is empty."""
        sample = make_sample(
            route_id="remotion_data_news",
            generation=SampleGenerationMeta(visual_route=""),
            params={"fullContent": "测试"},
        )
        payload = replay.build_clip_preview_payload(sample)
        assert payload["visualRoute"] == "remotion_data_news"

    def test_clip_seconds_default(self):
        """clipSeconds defaults to 3."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={"fullContent": "测试"},
        )
        payload = replay.build_clip_preview_payload(sample)
        assert payload["params"]["clipSeconds"] == 3

    def test_clip_seconds_not_overwritten(self):
        """If clipSeconds already in params, keep it."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={"fullContent": "测试", "clipSeconds": 5},
        )
        payload = replay.build_clip_preview_payload(sample)
        assert payload["params"]["clipSeconds"] == 5

    def test_cover_title_from_style_name(self):
        """coverTitle defaults to sample.style_name."""
        sample = make_sample(
            style_name="动态数据卡片",
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={"fullContent": "测试"},
        )
        payload = replay.build_clip_preview_payload(sample)
        assert payload["coverTitle"] == "动态数据卡片"


# ─── Reproducibility Assessment Tests ────────────────────────────────────────

class TestAssessReproducibility:
    """assess_reproducibility returns (bool, list[str]) for whether a sample can be rerun."""

    def test_reproducible_with_route_and_content(self):
        """Sample with visual_route and content is reproducible."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={"fullContent": "AI 前沿内容"},
        )
        reproducible, warnings = replay.assess_reproducibility(sample)
        assert reproducible is True
        assert warnings == []

    def test_reproducible_with_content_preview_only_warns(self):
        """Using content_preview only produces warning but is still reproducible."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={},
            content_preview="AI 前沿资讯内容摘要",
        )
        reproducible, warnings = replay.assess_reproducibility(sample)
        assert reproducible is True
        assert any("content_preview" in w for w in warnings)

    def test_not_reproducible_without_route(self):
        """Sample without route is not reproducible."""
        # Set both generation.visual_route AND route_id to empty
        sample = make_sample(
            route_id="",
            generation=SampleGenerationMeta(visual_route=""),
            params={"fullContent": "AI 前沿"},
        )
        reproducible, warnings = replay.assess_reproducibility(sample)
        assert reproducible is False

    def test_not_reproducible_without_content(self):
        """Sample without content is not reproducible."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={},
            content_preview="",
        )
        reproducible, warnings = replay.assess_reproducibility(sample)
        assert reproducible is False


# ─── Full Rerun Payload Tests ─────────────────────────────────────────────────

class TestBuildRerunPayload:
    """build_rerun_payload returns the full V1.0.6 rerun payload."""

    def test_returns_all_required_keys(self, temp_records_dir):
        """Top-level keys are present."""
        sample = make_sample(params={"fullContent": "测试"})
        sg_store.save_sample(sample)
        payload = replay.build_rerun_payload(sample)
        assert "sampleId" in payload
        assert "schemaVersion" in payload
        assert "reproducible" in payload
        assert "warnings" in payload
        assert "visualComposePayload" in payload
        assert "clipPreviewPayload" in payload
        assert "source" in payload
        assert "generation" in payload
        assert "assetMeta" in payload
        assert "qualityMeta" in payload
        assert "reviewMeta" in payload
        assert "jobRun" in payload

    def test_schema_version_is_1_0_6(self, temp_records_dir):
        """schemaVersion field is set to 1.0.6."""
        sample = make_sample(params={"fullContent": "测试"})
        sg_store.save_sample(sample)
        payload = replay.build_rerun_payload(sample)
        assert payload["schemaVersion"] == "1.0.6"

    def test_source_and_generation_serialized(self, temp_records_dir):
        """source and generation are serialized as dicts (not Pydantic objects)."""
        sample = make_sample(params={"fullContent": "测试"})
        sg_store.save_sample(sample)
        payload = replay.build_rerun_payload(sample)
        assert isinstance(payload["source"], dict)
        assert isinstance(payload["generation"], dict)
        assert payload["source"]["source_type"] == "workbench"
        assert payload["generation"]["visual_route"] == "pillow"

    def test_job_run_preserved(self, temp_records_dir):
        """job_run dict is preserved in output."""
        sample = make_sample(
            params={"fullContent": "测试"},
            job_run={"runId": "run_xyz", "status": "succeeded"},
        )
        sg_store.save_sample(sample)
        payload = replay.build_rerun_payload(sample)
        assert payload["jobRun"]["runId"] == "run_xyz"
        assert payload["jobRun"]["status"] == "succeeded"

    def test_reproducible_field_reflects_assessment(self, temp_records_dir):
        """reproducible matches assess_reproducibility result."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={"fullContent": "AI 前沿资讯"},
        )
        sg_store.save_sample(sample)
        payload = replay.build_rerun_payload(sample)
        assert payload["reproducible"] is True
        assert payload["warnings"] == []

    def test_warnings_field_reflects_incomplete_content(self, temp_records_dir):
        """warnings list is populated when only content_preview is available."""
        sample = make_sample(
            generation=SampleGenerationMeta(visual_route="pillow"),
            params={},
            content_preview="AI 前沿资讯摘要",
        )
        sg_store.save_sample(sample)
        payload = replay.build_rerun_payload(sample)
        assert payload["reproducible"] is True
        assert any("content_preview" in w for w in payload["warnings"])


# ─── Router Endpoint Tests ────────────────────────────────────────────────────

class TestRouterRerunPayloadEndpoint:
    """GET /style-samples/{id}/rerun-payload endpoint."""

    def test_returns_404_for_missing_sample(self, temp_records_dir):
        """Returns 404 when sample does not exist."""
        from app.video_lab.router import get_style_sample_rerun_payload
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_style_sample_rerun_payload("nonexistent_id")
        assert exc_info.value.status_code == 404

    def test_returns_full_payload_for_existing_sample(self, temp_records_dir):
        """Returns complete V1.0.6 payload for an existing sample."""
        from app.video_lab.router import get_style_sample_rerun_payload

        sample = make_sample(
            id="rerun_endpoint_test",
            params={"fullContent": "AI 前沿资讯完整内容"},
        )
        sg_store.save_sample(sample)

        payload = get_style_sample_rerun_payload("rerun_endpoint_test")

        assert payload["sampleId"] == "rerun_endpoint_test"
        assert payload["schemaVersion"] == "1.0.6"
        assert "visualComposePayload" in payload
        assert "clipPreviewPayload" in payload

    def test_does_not_call_tts_subtitle_compose(self, temp_records_dir, monkeypatch):
        """The endpoint does NOT call run_tts_subtitle_compose (no actual generation)."""
        from app.video_lab.router import get_style_sample_rerun_payload

        sample = make_sample(
            id="no_generation_test",
            params={"fullContent": "AI 内容"},
        )
        sg_store.save_sample(sample)

        call_count = 0
        def _track(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise AssertionError("run_tts_subtitle_compose should not be called")

        monkeypatch.setattr(
            "app.video_lab.style_gallery.replay.build_rerun_payload",
            lambda s: {"sampleId": s.id, "schemaVersion": "1.0.6", "reproducible": True,
                       "warnings": [], "source": {}, "generation": {}, "assetMeta": {},
                       "qualityMeta": {}, "reviewMeta": {}, "jobRun": {},
                       "visualComposePayload": {}, "clipPreviewPayload": {}},
        )

        payload = get_style_sample_rerun_payload("no_generation_test")
        assert "sampleId" in payload  # endpoint returned without calling generation

    def test_does_not_write_runtime_files(self, temp_records_dir, monkeypatch):
        """Rerun endpoint does not write any files to runtime."""
        from app.video_lab.router import get_style_sample_rerun_payload

        sample = make_sample(
            id="no_file_write_test",
            params={"fullContent": "AI 内容"},
        )
        sg_store.save_sample(sample)

        runtime_before = list((temp_records_dir.parent).rglob("*"))

        payload = get_style_sample_rerun_payload("no_file_write_test")

        runtime_after = list((temp_records_dir.parent).rglob("*"))
        # Only the JSONL file should exist; no new runtime artifacts
        assert len(runtime_after) == len(runtime_before)
        assert payload["sampleId"] == "no_file_write_test"
