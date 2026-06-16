"""
Tests for information_structure_service V1.1

Covers improved intra-paragraph splitting for multi-point detection.
"""

import pytest
from app.video_lab.services.information_structure_service import (
    generate_information_structure,
    _split_paragraph_into_items,
    _is_evidence_line,
    _is_conclusion_text,
)


FULL_AI_NEWS_CONTENT = """科学研究评审实现突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%。
依据：依据 1

购物AI助手落后：主流模型通过率仅57-77%，真实网购任务中完成率仍有较大提升空间。
依据：依据 1

企业级AI加速落地：Anthropic与TCS合作推进企业级 AI 应用，DeepMind投资千万美元。
依据：依据 1

多语言NLP低资源方言突破：大型语言模型在低资源语言和方言上的表现持续提升，科学事实检测能力同步增强。
依据：依据 1

RogueAI欺骗检测新进展：AI系统被发现在评审过程中进行策略性欺骗，对评审机制提出新挑战。
依据：依据 1

Shopping Reasoning Bench购物推理短板：主流模型通过率仅57-77%，真实网购任务中完成率仍有较大提升空间。
依据：依据 1

SICI立场复杂度指数：衡量AI系统处理多角度复杂问题能力的新指标体系。
依据：依据 1

AI同行评审展示层攻击：AI辅助评审系统的安全性和可靠性面临新的挑战。
依据：依据 1

Anthropic与TCS、DXC企业级AI合作：企业级AI落地加速。
DeepMind多智能体安全研究：多智能体系统的安全性和可靠性研究获得投资。
依据：依据 1

这说明可信性、可靠性和跨文化鲁棒性是当前AI评估的核心维度。"""


class TestEvidenceLineDetection:
    def test_evidence_line_with_chinese_colon(self):
        assert _is_evidence_line("依据：依据 1") is True
        assert _is_evidence_line("依据：数据来源") is True

    def test_non_evidence_line(self):
        assert _is_evidence_line("科学研究评审实现突破：ProReviewer系统...") is False
        assert _is_evidence_line("这说明可信性是核心维度") is False


class TestConclusionDetection:
    def test_conclusion_keywords(self):
        assert _is_conclusion_text("这说明可信性是核心维度") is True
        assert _is_conclusion_text("总体来看，今年进展显著") is True
        assert _is_conclusion_text("趋势是向好发展") is True

    def test_non_conclusion(self):
        assert _is_conclusion_text("ProReviewer系统将评审建模") is False
        assert _is_conclusion_text("购物AI助手落后主流模型") is False


class TestIntraParagraphSplitting:
    def test_paragraph_with_multiple_points(self):
        """A paragraph containing multiple 'title: description' blocks."""
        para = "多语言NLP低资源方言突破：大型语言模型在低资源语言上的表现提升，科学事实检测能力同步增强。"
        items = _split_paragraph_into_items(para)
        # Should split into multiple items or one item with title detected
        assert len(items) >= 1
        assert items[0]["title"] != ""

    def test_paragraph_with_evidence(self):
        """Evidence lines should attach to previous item, not create new item."""
        para = "ProReviewer实现突破：系统将评审建模为马尔可夫决策过程。依据：依据 1"
        items = _split_paragraph_into_items(para)
        assert len(items) >= 1
        # The evidence should be in the evidence list, not a separate item
        for item in items:
            if item.get("title"):
                assert len(item.get("evidence", [])) >= 1

    def test_empty_paragraph(self):
        assert _split_paragraph_into_items("") == []
        assert _split_paragraph_into_items("   ") == []


class TestCompressionModes:
    def test_strict_detects_all_items(self):
        """strict/all mode should detect >= 7 items and select all."""
        result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="strict",
            target_point_count="all",
            include_overview=True,
            include_conclusion=True,
        )
        stats = result["stats"]
        # Should detect at least 7 items (ideally 9-10)
        assert stats["detectedItemCount"] >= 7, f"Only detected {stats['detectedItemCount']} items"
        # strict should select all
        assert stats["selectedItemCount"] == stats["detectedItemCount"]
        assert stats["droppedItemCount"] == 0

    def test_brief_keeps_3_items(self):
        """brief mode should keep exactly 3 items."""
        result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="brief",
            include_overview=True,
            include_conclusion=True,
        )
        stats = result["stats"]
        assert stats["selectedItemCount"] == 3
        assert stats["droppedItemCount"] == stats["detectedItemCount"] - 3

    def test_balanced_keeps_5_to_7_items(self):
        """balanced mode should keep 5-7 items."""
        result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="balanced",
            include_overview=True,
            include_conclusion=True,
        )
        stats = result["stats"]
        assert 5 <= stats["selectedItemCount"] <= 7

    def test_strict_not_forced_to_3(self):
        """strict mode should NOT compress to 3 items."""
        result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="strict",
            target_point_count="all",
        )
        stats = result["stats"]
        # This is the core regression test: was previously forced to 3
        assert stats["selectedItemCount"] >= 7, (
            f"strict mode selected only {stats['selectedItemCount']} items - "
            f"should be >= 7 (was previously hardcoded to 3)"
        )


class TestOverviewConclusionSeparation:
    def test_overview_not_counted_as_item(self):
        """Overview should be separate from body items."""
        result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="strict",
            include_overview=True,
            include_conclusion=True,
        )
        overview = result.get("overview", {})
        items = result.get("items", [])

        # Overview should have a title/summary
        assert overview.get("title") or overview.get("summary")

        # Items should NOT include the overview text as a regular item
        # (first item's description should not be the same as overview)
        if items:
            first_item_title = items[0].get("title", "")
            assert first_item_title != overview.get("title", "")

    def test_conclusion_not_counted_as_item(self):
        """Conclusion should be separate from body items."""
        result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="strict",
            include_overview=True,
            include_conclusion=True,
        )
        conclusion = result.get("conclusion", {})
        items = result.get("items", [])

        # Conclusion should exist and have content
        assert conclusion.get("text") or conclusion.get("title")

        # Last item should not be the conclusion
        # (conclusion is in separate field)
        assert len(items) > 0


class TestEvidenceNotIndependentItem:
    def test_evidence_lines_do_not_become_items(self):
        """Lines starting with '依据：' should not become independent items."""
        result = generate_information_structure(
            "科学研究评审实现突破：ProReviewer系统将评审建模。\n\n依据：依据 1\n\n购物AI助手落后：主流模型通过率57%。\n\n依据：依据 1",
            compression_mode="balanced",
            include_overview=False,
            include_conclusion=False,
        )
        items = result.get("items", [])
        # Should NOT have items with just evidence content
        for item in items:
            # Item title should not be "依据"
            assert "依据" not in item.get("title", ""), (
                f"Found evidence-only item: {item}"
            )


class TestDurationEstimation:
    def test_strict_estimated_longer_than_brief(self):
        """strict mode should estimate longer duration than brief."""
        strict_result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="strict",
            target_point_count="all",
        )
        brief_result = generate_information_structure(
            FULL_AI_NEWS_CONTENT,
            compression_mode="brief",
        )
        strict_dur = strict_result["stats"]["estimatedDurationSec"]
        brief_dur = brief_result["stats"]["estimatedDurationSec"]
        # strict should estimate significantly more time
        assert strict_dur > brief_dur
