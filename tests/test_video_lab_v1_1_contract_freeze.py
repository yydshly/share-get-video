"""
tests/test_video_lab_v1_1_contract_freeze.py
V1.1.0: Contract Freeze Tests — verify main flow documentation and stable contracts exist.
"""

import pytest
from pathlib import Path

# Project root is the parent of tests/
PROJECT_ROOT = Path(__file__).parent.parent


class TestDocumentationExists:
    """Documentation files required by V1.1.0 freeze must exist."""

    def test_main_flow_freeze_doc_exists(self):
        """V1.1.0 product main flow freeze document must exist."""
        doc_path = PROJECT_ROOT / "docs" / "video_lab" / "V1_1_0_PRODUCT_MAIN_FLOW_FREEZE.md"
        assert doc_path.exists(), f"Missing: {doc_path}"

    def test_smoke_test_doc_exists(self):
        """V1.0.8 main flow smoke test document must exist."""
        doc_path = PROJECT_ROOT / "docs" / "video_lab" / "V1_0_8_MAIN_FLOW_SMOKE_TEST.md"
        assert doc_path.exists(), f"Missing: {doc_path}"


class TestStyleSampleContract:
    """StyleSample contract fields are frozen in V1.1.0."""

    def test_style_sample_model_has_required_fields(self):
        """StyleSample model must have all V1.1.0 required fields."""
        from app.video_lab.style_gallery.models import StyleSample

        sample = StyleSample(
            id="test_001",
            route_id="pillow",
            route_name="Pillow 信息卡路线",
            style_name="测试风格",
            params={"fullContent": "测试内容"},
        )
        d = sample.to_dict()
        # Core fields
        assert "id" in d
        assert "route_id" in d
        assert "route_name" in d
        assert "style_name" in d
        assert "status" in d
        assert "params" in d
        assert "output" in d
        assert "tags" in d
        assert "content_preview" in d
        assert "created_at" in d
        # V1.0.5 asset fields
        assert "source" in d
        assert "generation" in d
        assert "asset_meta" in d
        assert "quality_meta" in d
        assert "review_meta" in d
        assert "job_run" in d
        assert "schema_version" in d

    def test_style_sample_from_dict_compat_old_record(self):
        """StyleSample.from_dict must handle records missing V1.0.5 fields."""
        from app.video_lab.style_gallery.models import StyleSample

        # Minimal old record without asset metadata
        old_record = {
            "id": "old_sample_001",
            "route_id": "pillow",
            "route_name": "Pillow",
            "style_name": "旧风格",
            "status": "candidate",
            "params": {"fullContent": "旧内容"},
            "output": {},
            "tags": [],
            "content_preview": "...",
            "created_at": "2024-01-01T00:00:00",
        }
        sample = StyleSample.from_dict(old_record)
        assert sample.id == "old_sample_001"
        assert sample.schema_version == "1.0.4"  # backward compat default
        # Defaults filled
        assert sample.source is not None
        assert sample.generation is not None
        assert sample.asset_meta is not None


class TestRerunPayloadContract:
    """Rerun payload contract is frozen at schemaVersion 1.0.6."""

    def test_rerun_payload_has_required_top_level_keys(self):
        """Rerun payload must have all required top-level keys."""
        from app.video_lab.style_gallery import replay
        from app.video_lab.style_gallery.models import StyleSample, SampleStatus

        sample = StyleSample(
            id="rerun_contract_test",
            route_id="pillow",
            route_name="Pillow",
            style_name="测试",
            status=SampleStatus.CANDIDATE,
            params={"fullContent": "测试内容"},
            output={},
        )
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

    def test_rerun_payload_schema_version_is_1_0_6(self):
        """Rerun payload schemaVersion must be 1.0.6."""
        from app.video_lab.style_gallery import replay
        from app.video_lab.style_gallery.models import StyleSample, SampleStatus

        sample = StyleSample(
            id="schema_ver_test",
            route_id="pillow",
            route_name="Pillow",
            style_name="测试",
            status=SampleStatus.CANDIDATE,
            params={"fullContent": "测试内容"},
            output={},
        )
        payload = replay.build_rerun_payload(sample)
        assert payload["schemaVersion"] == "1.0.6"

    def test_visual_compose_payload_uses_full_content(self):
        """visualComposePayload.content comes from params.fullContent."""
        from app.video_lab.style_gallery import replay
        from app.video_lab.style_gallery.models import StyleSample, SampleStatus

        sample = StyleSample(
            id="content_test",
            route_id="pillow",
            route_name="Pillow",
            style_name="测试",
            status=SampleStatus.CANDIDATE,
            params={"fullContent": "今日 AI 前沿进展重要内容"},
            output={},
        )
        payload = replay.build_rerun_payload(sample)
        assert "今日 AI 前沿进展重要内容" in payload["visualComposePayload"]["content"]


class TestCompareBundleContract:
    """Compare Bundle contract is frozen at schemaVersion 1.0.7."""

    def test_compare_bundle_schema_version_is_1_0_7(self):
        """CompareBundle schemaVersion must be 1.0.7."""
        from app.video_lab.style_gallery import compare_bundle as sg_bundle

        bundle = sg_bundle.CompareBundle(
            id="test_bundle",
            title="测试",
            goal="",
            sample_ids=[],
            items=[],
            decision=sg_bundle.CompareBundleDecision(),
            tags=[],
        )
        assert bundle.schema_version == "1.0.7"

    def test_compare_bundle_has_required_fields(self):
        """CompareBundle must have all V1.1.0 required fields."""
        from app.video_lab.style_gallery import compare_bundle as sg_bundle

        bundle = sg_bundle.CompareBundle(
            id="test_bundle",
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
                    score=82.0,
                    grade="good",
                ),
            ],
            decision=sg_bundle.CompareBundleDecision(
                winner_sample_id="s1",
                winner_reason="视觉评分最高：82.0分（good）",
                rejected_sample_ids=["s2"],
                rejected_reasons={"s2": "对比中未胜出"},
            ),
            tags=["workbench", "test"],
        )
        d = bundle.to_dict()
        assert "id" in d
        assert "title" in d
        assert "goal" in d
        assert "sample_ids" in d
        assert "items" in d
        assert "decision" in d
        assert "decision" in d
        assert "winner_sample_id" in d["decision"]
        assert "winner_reason" in d["decision"]
        assert "rejected_sample_ids" in d["decision"]
        assert "rejected_reasons" in d["decision"]
        assert "tags" in d
        assert "created_at" in d
        assert "updated_at" in d
        assert "schema_version" in d

    def test_build_compare_bundle_returns_valid_bundle(self):
        """build_compare_bundle creates a valid CompareBundle from sample_ids."""
        from app.video_lab.style_gallery import compare_bundle as sg_bundle
        from app.video_lab.style_gallery import store as sg_store

        bundle = sg_bundle.build_compare_bundle(
            sample_ids=[],
            title="空测试",
            goal="测试空情况",
        )
        assert bundle.schema_version == "1.0.7"
        assert bundle.title == "空测试"
        assert bundle.decision is not None
        assert bundle.decision.winner_reason == "暂无视觉评分，需人工判断"
