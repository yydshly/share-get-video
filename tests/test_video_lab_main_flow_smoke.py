"""
tests/test_video_lab_main_flow_smoke.py
V1.0.8: Video Lab Main Flow Smoke Test

验证主流程串起来：
StyleSample → rerun payload → comparing status → CompareBundle

不生成真实视频，不调用 MiniMax，不调用 Remotion。
"""

import pytest
from datetime import datetime

from app.video_lab.style_gallery.models import (
    StyleSample, SampleStatus, StyleSampleOutput, EvaluationScore,
    SampleSource, SampleGenerationMeta, SampleAssetMeta,
    SampleQualityMeta, SampleReviewMeta, VisualJudgement,
)
from app.video_lab.style_gallery import store as sg_store
from app.video_lab.style_gallery import compare_bundle as sg_bundle


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_sample_dir(monkeypatch, tmp_path):
    """Redirect sample store path to a temp directory."""
    runtime = tmp_path / "runtime" / "style_gallery"
    records_dir = runtime / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = records_dir / "style_samples.jsonl"

    monkeypatch.setattr(sg_store, "_RUNTIME", runtime)
    monkeypatch.setattr(sg_store, "_RECORDS_DIR", records_dir)
    monkeypatch.setattr(sg_store, "_JSONL_PATH", jsonl_path)
    return records_dir


@pytest.fixture
def temp_bundle_dir(monkeypatch, tmp_path):
    """Redirect bundle store path to a temp directory."""
    runtime = tmp_path / "runtime" / "style_gallery"
    records_dir = runtime / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = records_dir / "compare_bundles.jsonl"

    monkeypatch.setattr(sg_bundle, "_RUNTIME", runtime)
    monkeypatch.setattr(sg_bundle, "_RECORDS_DIR", records_dir)
    monkeypatch.setattr(sg_bundle, "_JSONL_PATH", jsonl_path)
    return records_dir


def make_full_sample(**overrides) -> StyleSample:
    """Create a StyleSample with complete V1.0.5 asset fields."""
    out = StyleSampleOutput(
        type="mp4",
        path="video_lab/experiments/smoke_test/final.mp4",
        poster="video_lab/experiments/smoke_test/poster.jpg",
        audio_url="video_lab/experiments/smoke_test/audio.mp3",
        srt_url="video_lab/experiments/smoke_test/subs.srt",
        manifest_url="video_lab/experiments/smoke_test/manifest.json",
    )
    kwargs = dict(
        id="smoke_sample_001",
        route_id="pillow",
        route_name="Pillow 信息卡路线",
        style_name="Smoke Test 风格",
        description="主流程冒烟测试样片",
        status=SampleStatus.CANDIDATE,
        params={"aspectRatio": "9:16", "targetDuration": 45, "keyPointCount": 3,
                "fullContent": "今日 AI 前沿进展：多语言模型在低资源方言取得突破，AI 评估体系向多维化演进。"},
        output=out,
        tags=["smoke-test", "workbench"],
        content_preview="今日 AI 前沿进展...",
        duration_sec=45.0,
        audio_duration_sec=42.5,
        created_at=datetime.utcnow(),
        visual_judgement=VisualJudgement(
            score=82.0,
            grade="good",
            summary="良好水准",
            strengths=["排版留白合理", "文字清晰可读"],
            weaknesses=["动效稍弱"],
            suggestions=["增强动效"],
            judged_at=datetime.utcnow().isoformat(),
            dimensions={"layout": 4.2, "readability": 4.5, "hierarchy": 4.0, "aesthetics": 3.8, "consistency": 4.1},
        ),
        source=SampleSource(
            source_type="workbench",
            source_page="/video-lab/workbench",
            source_run_id="run_smoke_001",
            experiment_id="exp_smoke_001",
            job_id="job_smoke_001",
            run_id="run_smoke_001",
            workbench_route="pillow",
            saved_from="workbench",
        ),
        generation=SampleGenerationMeta(
            visual_route="pillow",
            visual_profile="ai_frontier_dark",
            remotion_family="",
            route_preset="pillow",
            aspect_ratio="9:16",
            target_duration=45.0,
            key_point_count=3,
            content_hash="abc123def456",
        ),
        asset_meta=SampleAssetMeta(
            final_video_url="/runtime/video_lab/experiments/smoke_test/final.mp4",
            cover_url="/runtime/video_lab/experiments/smoke_test/poster.jpg",
            audio_url="/runtime/video_lab/experiments/smoke_test/audio.mp3",
            srt_url="/runtime/video_lab/experiments/smoke_test/subs.srt",
            manifest_url="/runtime/video_lab/experiments/smoke_test/manifest.json",
            runtime_prefix="/runtime",
            artifact_count=4,
        ),
        quality_meta=SampleQualityMeta(
            structural_score=0.85,
            visual_score=0.82,
            warnings=["dim"],
            steps=[
                {"step": "plan", "duration_ms": 1200},
                {"step": "render", "duration_ms": 3500},
            ],
        ),
        review_meta=SampleReviewMeta(
            review_status="approved",
            review_notes="通过 Smoke Test",
            problem_tags=[],
        ),
        job_run={
            "jobId": "job_smoke_001",
            "runId": "run_smoke_001",
            "experimentId": "exp_smoke_001",
            "routeId": "pillow",
            "status": "succeeded",
            "stage": "complete",
            "progress": 1.0,
            "stageLabel": "已完成",
        },
        schema_version="1.0.5",
    )
    kwargs.update(overrides)
    return StyleSample(**kwargs)


# ─── Main Flow Smoke Tests ───────────────────────────────────────────────────

class TestMainFlowSmoke:
    """End-to-end main flow: StyleSample → rerun payload → comparing → CompareBundle."""

    def test_full_asset_fields_preserved_in_sample(self, temp_sample_dir):
        """StyleSample with full V1.0.5 fields can be saved and retrieved."""
        sample = make_full_sample()
        sg_store.save_sample(sample)

        retrieved = sg_store.get_sample("smoke_sample_001")
        assert retrieved is not None
        assert retrieved.id == "smoke_sample_001"
        assert retrieved.route_id == "pillow"
        assert retrieved.status == SampleStatus.CANDIDATE
        # V1.0.5 asset fields
        assert retrieved.source.source_type == "workbench"
        assert retrieved.source.experiment_id == "exp_smoke_001"
        assert retrieved.generation.visual_profile == "ai_frontier_dark"
        assert retrieved.asset_meta.final_video_url == "/runtime/video_lab/experiments/smoke_test/final.mp4"
        assert retrieved.quality_meta.structural_score == 0.85
        assert retrieved.review_meta.review_status == "approved"
        assert retrieved.job_run["status"] == "succeeded"
        assert retrieved.schema_version == "1.0.5"
        # params with fullContent
        assert "fullContent" in retrieved.params
        assert "多语言模型" in retrieved.params["fullContent"]

    def test_rerun_payload_schema_version(self, temp_sample_dir):
        """Rerun payload has schemaVersion 1.0.6."""
        from app.video_lab.style_gallery import replay

        sample = make_full_sample()
        sg_store.save_sample(sample)

        payload = replay.build_rerun_payload(sample)
        assert payload["schemaVersion"] == "1.0.6"

    def test_rerun_payload_content_from_full_content(self, temp_sample_dir):
        """visualComposePayload.content comes from params.fullContent."""
        from app.video_lab.style_gallery import replay

        sample = make_full_sample()
        sg_store.save_sample(sample)

        payload = replay.build_rerun_payload(sample)
        content = payload["visualComposePayload"]["content"]
        assert "多语言模型" in content
        assert "低资源方言" in content

    def test_rerun_payload_clip_preview_content(self, temp_sample_dir):
        """clipPreviewPayload also uses content from params."""
        from app.video_lab.style_gallery import replay

        sample = make_full_sample()
        sg_store.save_sample(sample)

        payload = replay.build_rerun_payload(sample)
        content = payload["clipPreviewPayload"]["content"]
        assert "多语言模型" in content

    def test_mark_sample_comparing(self, temp_sample_dir):
        """Sample status can be updated to comparing."""
        sample = make_full_sample()
        sg_store.save_sample(sample)

        sample.status = SampleStatus.COMPARING
        sg_store.save_sample(sample)

        retrieved = sg_store.get_sample("smoke_sample_001")
        assert retrieved.status == SampleStatus.COMPARING

    def test_create_compare_bundle_from_sample(self, temp_sample_dir, temp_bundle_dir):
        """CompareBundle can be created from a comparing sample."""
        sample = make_full_sample()
        sample.status = SampleStatus.COMPARING
        sg_store.save_sample(sample)

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["smoke_sample_001"],
            title="Smoke Test Bundle",
            goal="验证主流程",
            tags=["smoke-test"],
        )
        saved = sg_bundle.save_compare_bundle(bundle)

        assert saved.id.startswith("bundle_")
        assert saved.title == "Smoke Test Bundle"
        assert saved.goal == "验证主流程"
        assert saved.schema_version == "1.0.7"
        assert saved.items[0].sample_id == "smoke_sample_001"
        assert saved.items[0].score == 82.0
        assert saved.decision.winner_sample_id == "smoke_sample_001"
        assert "82.0" in saved.decision.winner_reason

    def test_compare_bundle_winner_by_score(self, temp_sample_dir, temp_bundle_dir):
        """Winner is the sample with highest visual_judgement.score."""
        s1 = make_full_sample(
            id="high_score",
            visual_judgement=VisualJudgement(score=90.0, grade="excellent", summary="优秀"),
            params={"fullContent": "内容A"},
        )
        s2 = make_full_sample(
            id="low_score",
            visual_judgement=VisualJudgement(score=60.0, grade="ok", summary="一般"),
            params={"fullContent": "内容B"},
        )
        s1.status = SampleStatus.COMPARING
        s2.status = SampleStatus.COMPARING
        sg_store.save_sample(s1)
        sg_store.save_sample(s2)

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["high_score", "low_score"],
            title="Winner Test",
        )
        saved = sg_bundle.save_compare_bundle(bundle)

        assert saved.decision.winner_sample_id == "high_score"
        assert "90.0" in saved.decision.winner_reason
        assert "low_score" in saved.decision.rejected_sample_ids

    def test_compare_bundle_no_score_winner_empty(self, temp_sample_dir, temp_bundle_dir):
        """When no samples have scores, winner is empty with '暂无视觉评分'."""
        s1 = make_full_sample(
            id="no_score_1",
            visual_judgement=None,
            params={"fullContent": "内容A"},
        )
        s2 = make_full_sample(
            id="no_score_2",
            visual_judgement=None,
            params={"fullContent": "内容B"},
        )
        s1.status = SampleStatus.COMPARING
        s2.status = SampleStatus.COMPARING
        sg_store.save_sample(s1)
        sg_store.save_sample(s2)

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["no_score_1", "no_score_2"],
            title="No Score Test",
        )

        assert bundle.decision.winner_sample_id == ""
        assert bundle.decision.winner_reason == "暂无视觉评分，需人工判断"

    def test_delete_bundle_and_get_404(self, temp_sample_dir, temp_bundle_dir):
        """After deleting a bundle, GET returns 404."""
        sample = make_full_sample()
        sample.status = SampleStatus.COMPARING
        sg_store.save_sample(sample)

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["smoke_sample_001"],
            title="Delete Test",
        )
        saved = sg_bundle.save_compare_bundle(bundle)
        bundle_id = saved.id

        deleted = sg_bundle.delete_compare_bundle(bundle_id)
        assert deleted is True

        retrieved = sg_bundle.get_compare_bundle(bundle_id)
        assert retrieved is None

    def test_partial_invalid_sample_ids_skipped(self, temp_sample_dir, temp_bundle_dir):
        """Invalid sample_ids are skipped when building bundle."""
        sample = make_full_sample(id="valid_partial", params={"fullContent": "有效"})
        sg_store.save_sample(sample)

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["valid_partial", "nonexistent_id", "also_invalid"],
            title="Partial Test",
        )

        assert len(bundle.items) == 1
        assert bundle.items[0].sample_id == "valid_partial"
        assert "nonexistent_id" not in bundle.sample_ids

    def test_all_invalid_sample_ids_returns_empty_bundle(self, temp_sample_dir, temp_bundle_dir):
        """When all sample_ids are invalid, bundle is created with empty sample_ids."""
        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["invalid_a", "invalid_b"],
            title="All Invalid Test",
        )
        assert bundle.sample_ids == []
        assert len(bundle.items) == 0

    def test_full_flow_comparison(self, temp_sample_dir, temp_bundle_dir):
        """Complete flow: save sample → rerun payload → mark comparing → bundle → delete."""
        from app.video_lab.style_gallery import replay

        # 1. Create and save sample with full asset fields
        sample = make_full_sample(id="flow_sample", visual_judgement=None)
        sg_store.save_sample(sample)

        # 2. Verify rerun payload works
        payload = replay.build_rerun_payload(sample)
        assert payload["schemaVersion"] == "1.0.6"
        assert "visualComposePayload" in payload
        assert "clipPreviewPayload" in payload
        assert "多语言模型" in payload["visualComposePayload"]["content"]

        # 3. Mark as comparing
        sample.status = SampleStatus.COMPARING
        sg_store.save_sample(sample)
        assert sg_store.get_sample("flow_sample").status == SampleStatus.COMPARING

        # 4. Create compare bundle
        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["flow_sample"],
            title="Full Flow Test",
            goal="端到端验证",
            tags=["e2e", "smoke"],
        )
        saved = sg_bundle.save_compare_bundle(bundle)
        assert saved.schema_version == "1.0.7"
        assert len(saved.items) == 1
        assert saved.decision.winner_sample_id == ""  # no score

        # 5. List bundles
        bundles = sg_bundle.list_compare_bundles()
        assert len(bundles) >= 1
        assert any(b.id == saved.id for b in bundles)

        # 6. Delete bundle
        sg_bundle.delete_compare_bundle(saved.id)
        assert sg_bundle.get_compare_bundle(saved.id) is None
