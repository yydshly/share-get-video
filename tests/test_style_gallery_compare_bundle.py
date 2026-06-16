"""
tests/test_style_gallery_compare_bundle.py
V1.0.7: Style Sample Compare Bundle — test bundle model, build, store, and API endpoints.
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
def temp_records_dir(monkeypatch, tmp_path):
    """Redirect store path constants to a temp directory for samples."""
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
    """Redirect bundle path constants to a temp directory."""
    runtime = tmp_path / "runtime" / "style_gallery"
    records_dir = runtime / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = records_dir / "compare_bundles.jsonl"

    monkeypatch.setattr(sg_bundle, "_RUNTIME", runtime)
    monkeypatch.setattr(sg_bundle, "_RECORDS_DIR", records_dir)
    monkeypatch.setattr(sg_bundle, "_JSONL_PATH", jsonl_path)
    return records_dir


def make_sample(**overrides) -> StyleSample:
    """Make a minimal StyleSample."""
    out = StyleSampleOutput(
        type="mp4",
        path="video_lab/experiments/test/final.mp4",
        poster="video_lab/experiments/test/poster.jpg",
        audio_url="video_lab/experiments/test/audio.mp3",
        srt_url="video_lab/experiments/test/subs.srt",
        manifest_url="video_lab/experiments/test/manifest.json",
    )
    kwargs = dict(
        id="sample_001",
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


# ─── Model Tests ─────────────────────────────────────────────────────────────

class TestCompareBundleModel:
    """CompareBundle to_dict / from_dict roundtrip."""

    def test_to_dict_serializes_all_fields(self):
        """All fields are present in to_dict output."""
        now = datetime.utcnow()
        bundle = sg_bundle.CompareBundle(
            id="bundle_abc12345",
            title="测试对比包",
            goal="判断最佳路线",
            sample_ids=["s1", "s2"],
            items=[
                sg_bundle.CompareBundleItem(
                    sample_id="s1",
                    route_id="pillow",
                    route_name="Pillow",
                    style_name="风格A",
                    status="comparing",
                    score=82.5,
                    grade="good",
                    video_url="/runtime/a.mp4",
                    poster_url="/runtime/a.jpg",
                    manifest_url="/runtime/a.json",
                    rerun_payload_available=True,
                ),
            ],
            decision=sg_bundle.CompareBundleDecision(
                winner_sample_id="s1",
                winner_reason="视觉评分最高：82.5分（good）",
                rejected_sample_ids=["s2"],
                rejected_reasons={"s2": "对比中未胜出"},
                productization_notes="适合产品化",
            ),
            tags=["workbench", "route-selection"],
            created_at=now,
            updated_at=now,
            schema_version="1.0.7",
        )
        d = bundle.to_dict()
        assert d["id"] == "bundle_abc12345"
        assert d["title"] == "测试对比包"
        assert d["goal"] == "判断最佳路线"
        assert d["sample_ids"] == ["s1", "s2"]
        assert len(d["items"]) == 1
        assert d["items"][0]["sample_id"] == "s1"
        assert d["items"][0]["score"] == 82.5
        assert d["decision"]["winner_sample_id"] == "s1"
        assert d["decision"]["winner_reason"] == "视觉评分最高：82.5分（good）"
        assert d["tags"] == ["workbench", "route-selection"]
        assert d["schema_version"] == "1.0.7"
        assert "created_at" in d
        assert "updated_at" in d

    def test_from_dict_roundtrip(self):
        """from_dict(to_dict()) produces equivalent object."""
        now = datetime.utcnow()
        original = sg_bundle.CompareBundle(
            id="bundle_roundtrip",
            title="往返测试",
            goal="",
            sample_ids=["x"],
            items=[],
            decision=sg_bundle.CompareBundleDecision(),
            tags=[],
            created_at=now,
            updated_at=now,
            schema_version="1.0.7",
        )
        restored = sg_bundle.CompareBundle.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.schema_version == original.schema_version


# ─── Build Tests ─────────────────────────────────────────────────────────────

class TestBuildCompareBundle:
    """build_compare_bundle creates bundle from sample_ids."""

    def test_creates_bundle_from_sample_ids(self, temp_records_dir, temp_bundle_dir):
        """Bundle is created with correct sample_ids and items."""
        s1 = make_sample(id="build_s1", params={"fullContent": "内容A"})
        s2 = make_sample(id="build_s2", params={"fullContent": "内容B"})
        sg_store.save_sample(s1)
        sg_store.save_sample(s2)

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["build_s1", "build_s2"],
            title="自定义标题",
            goal="测试目标",
            tags=["test"],
        )

        assert bundle.id.startswith("bundle_")
        assert bundle.title == "自定义标题"
        assert bundle.goal == "测试目标"
        assert set(bundle.sample_ids) == {"build_s1", "build_s2"}
        assert len(bundle.items) == 2
        assert bundle.tags == ["test"]
        assert bundle.schema_version == "1.0.7"

    def test_highest_score_becomes_winner(self, temp_records_dir, temp_bundle_dir):
        """Sample with highest visual_judgement.score is set as winner."""
        s1 = make_sample(
            id="winner_s1",
            params={"fullContent": "内容A"},
            visual_judgement=VisualJudgement(score=75.0, grade="good", summary="良好"),
        )
        s2 = make_sample(
            id="winner_s2",
            params={"fullContent": "内容B"},
            visual_judgement=VisualJudgement(score=88.0, grade="excellent", summary="优秀"),
        )
        sg_store.save_sample(s1)
        sg_store.save_sample(s2)

        bundle = sg_bundle.build_compare_bundle(sample_ids=["winner_s1", "winner_s2"])

        assert bundle.decision.winner_sample_id == "winner_s2"
        assert bundle.decision.winner_reason == "视觉评分最高：88.0分（excellent）"

    def test_no_score_winner_empty_with_reason(self, temp_records_dir, temp_bundle_dir):
        """When no samples have scores, winner is empty with '暂无视觉评分' reason."""
        s1 = make_sample(id="no_score_s1", params={"fullContent": "内容A"})
        s2 = make_sample(id="no_score_s2", params={"fullContent": "内容B"})
        sg_store.save_sample(s1)
        sg_store.save_sample(s2)

        bundle = sg_bundle.build_compare_bundle(sample_ids=["no_score_s1", "no_score_s2"])

        assert bundle.decision.winner_sample_id == ""
        assert bundle.decision.winner_reason == "暂无视觉评分，需人工判断"

    def test_missing_sample_ids_skipped_without_crash(self, temp_records_dir, temp_bundle_dir):
        """Invalid sample_ids are skipped; valid ones are included."""
        s1 = make_sample(id="valid_s1", params={"fullContent": "内容A"})
        sg_store.save_sample(s1)

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["valid_s1", "nonexistent_id"],
        )

        assert len(bundle.items) == 1
        assert bundle.items[0].sample_id == "valid_s1"
        assert "nonexistent_id" not in bundle.sample_ids

    def test_all_invalid_sample_ids_creates_empty_bundle(self, temp_records_dir, temp_bundle_dir):
        """When no sample_ids are valid, bundle has empty sample_ids."""
        bundle = sg_bundle.build_compare_bundle(
            sample_ids=["invalid_a", "invalid_b"],
        )
        # bundle is created but sample_ids is empty (all invalid)
        assert bundle.sample_ids == []
        assert len(bundle.items) == 0

    def test_rerun_payload_available_flag(self, temp_records_dir, temp_bundle_dir):
        """rerun_payload_available is True when sample has fullContent."""
        s1 = make_sample(id="rerun_s1", params={"fullContent": "有内容"})
        s2 = make_sample(id="rerun_s2", params={}, content_preview="预览内容")
        sg_store.save_sample(s1)
        sg_store.save_sample(s2)

        bundle = sg_bundle.build_compare_bundle(sample_ids=["rerun_s1", "rerun_s2"])

        item1 = next(it for it in bundle.items if it.sample_id == "rerun_s1")
        item2 = next(it for it in bundle.items if it.sample_id == "rerun_s2")
        assert item1.rerun_payload_available is True
        assert item2.rerun_payload_available is True  # content_preview counts


# ─── Store Tests ─────────────────────────────────────────────────────────────

class TestCompareBundleStore:
    """JSONL storage for compare bundles."""

    def test_save_and_get_roundtrip(self, temp_records_dir, temp_bundle_dir):
        """save_compare_bundle -> get_compare_bundle returns identical bundle."""
        bundle = sg_bundle.CompareBundle(
            id="store_test_001",
            title="存储测试",
            goal="",
            sample_ids=["s1"],
            items=[],
            decision=sg_bundle.CompareBundleDecision(),
            tags=["test"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            schema_version="1.0.7",
        )
        sg_bundle.save_compare_bundle(bundle)

        retrieved = sg_bundle.get_compare_bundle("store_test_001")
        assert retrieved is not None
        assert retrieved.id == bundle.id
        assert retrieved.title == bundle.title
        assert retrieved.schema_version == bundle.schema_version

    def test_get_missing_returns_none(self, temp_records_dir, temp_bundle_dir):
        """get_compare_bundle returns None for nonexistent ID."""
        result = sg_bundle.get_compare_bundle("does_not_exist")
        assert result is None

    def test_list_bundles_sorted_by_updated_at(self, temp_records_dir, temp_bundle_dir):
        """list_compare_bundles returns bundles sorted by updated_at descending."""
        base = datetime.utcnow()
        for i in range(3):
            b = sg_bundle.CompareBundle(
                id=f"list_test_{i}",
                title=f"对比包{i}",
                goal="",
                sample_ids=[],
                items=[],
                decision=sg_bundle.CompareBundleDecision(),
                tags=[],
                created_at=base,
                updated_at=datetime.fromtimestamp(base.timestamp() + i),
                schema_version="1.0.7",
            )
            sg_bundle.save_compare_bundle(b)

        bundles = sg_bundle.list_compare_bundles()
        ids = [b.id for b in bundles]
        # list_test_2 has latest updated_at, list_test_0 has earliest
        assert ids.index("list_test_2") < ids.index("list_test_0")
        assert ids.index("list_test_1") < ids.index("list_test_0")

    def test_delete_bundle(self, temp_records_dir, temp_bundle_dir):
        """delete_compare_bundle removes bundle and returns True."""
        bundle = sg_bundle.CompareBundle(
            id="delete_test_001",
            title="删除测试",
            goal="",
            sample_ids=[],
            items=[],
            decision=sg_bundle.CompareBundleDecision(),
            tags=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            schema_version="1.0.7",
        )
        sg_bundle.save_compare_bundle(bundle)

        deleted = sg_bundle.delete_compare_bundle("delete_test_001")
        assert deleted is True
        assert sg_bundle.get_compare_bundle("delete_test_001") is None

    def test_delete_nonexistent_returns_false(self, temp_records_dir, temp_bundle_dir):
        """delete_compare_bundle returns False for nonexistent ID."""
        result = sg_bundle.delete_compare_bundle("never_existed")
        assert result is False


# ─── Router Endpoint Tests ───────────────────────────────────────────────────

class TestRouterCompareBundleEndpoints:
    """API endpoints for compare bundles."""

    def test_post_empty_sample_ids_returns_400(self, temp_records_dir, temp_bundle_dir):
        """POST /style-compare-bundles with empty sampleIds returns 400."""
        from app.video_lab.router import create_style_compare_bundle
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            create_style_compare_bundle({"sampleIds": []})
        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()

    def test_post_success_returns_bundle_with_schema_version(self, temp_records_dir, temp_bundle_dir):
        """POST /style-compare-bundles returns bundle with schemaVersion 1.0.7."""
        from app.video_lab.router import create_style_compare_bundle

        s1 = make_sample(id="post_test_s1", params={"fullContent": "内容"})
        sg_store.save_sample(s1)

        result = create_style_compare_bundle({
            "title": "API测试包",
            "goal": "测试目标",
            "sampleIds": ["post_test_s1"],
            "tags": ["api-test"],
        })

        assert result["id"].startswith("bundle_")
        assert result["title"] == "API测试包"
        assert result["goal"] == "测试目标"
        assert result["schema_version"] == "1.0.7"
        assert result["items"][0]["sample_id"] == "post_test_s1"

    def test_get_missing_bundle_returns_404(self, temp_records_dir, temp_bundle_dir):
        """GET /style-compare-bundles/{id} returns 404 for nonexistent bundle."""
        from app.video_lab.router import get_style_compare_bundle
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_style_compare_bundle("nonexistent_bundle_id")
        assert exc_info.value.status_code == 404

    def test_get_existing_bundle(self, temp_records_dir, temp_bundle_dir):
        """GET /style-compare-bundles/{id} returns the bundle."""
        from app.video_lab.router import create_style_compare_bundle, get_style_compare_bundle

        s1 = make_sample(id="get_test_s1", params={"fullContent": "内容"})
        sg_store.save_sample(s1)

        created = create_style_compare_bundle({
            "title": "获取测试",
            "sampleIds": ["get_test_s1"],
        })

        retrieved = get_style_compare_bundle(created["id"])
        assert retrieved["id"] == created["id"]
        assert retrieved["title"] == "获取测试"

    def test_delete_bundle_endpoint(self, temp_records_dir, temp_bundle_dir):
        """DELETE /style-compare-bundles/{id} returns deleted confirmation."""
        from app.video_lab.router import create_style_compare_bundle, delete_style_compare_bundle, get_style_compare_bundle
        from fastapi import HTTPException

        s1 = make_sample(id="del_test_s1", params={"fullContent": "内容"})
        sg_store.save_sample(s1)

        created = create_style_compare_bundle({
            "title": "删除测试",
            "sampleIds": ["del_test_s1"],
        })

        result = delete_style_compare_bundle(created["id"])
        assert result["deleted"] == created["id"]

        with pytest.raises(HTTPException) as exc_info:
            get_style_compare_bundle(created["id"])
        assert exc_info.value.status_code == 404

    def test_list_bundles_endpoint(self, temp_records_dir, temp_bundle_dir):
        """GET /style-compare-bundles returns list of bundles."""
        from app.video_lab.router import create_style_compare_bundle, list_style_compare_bundles

        for i in range(3):
            s = make_sample(id=f"list_ep_s{i}", params={"fullContent": f"内容{i}"})
            sg_store.save_sample(s)
            create_style_compare_bundle({
                "title": f"列表测试{i}",
                "sampleIds": [f"list_ep_s{i}"],
            })

        bundles = list_style_compare_bundles(limit=10)
        assert len(bundles) == 3
        titles = [b["title"] for b in bundles]
        assert "列表测试0" in titles
        assert "列表测试1" in titles
        assert "列表测试2" in titles
