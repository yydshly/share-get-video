"""
Video Capability Lab - Tests
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.models import MethodCategory
from app.video_lab.seed_data import SEED_TEST_CASES, SEED_VIDEO_METHODS, get_test_case_by_id, get_method_by_id
from app.video_lab.advisor import getVideoMethodAdvice
from app.video_lab.method_registry import get_adapter_for_category, list_registered_categories
from app.video_lab.experiment_runner import get_runner


# ─────────────────────────────────────────────
# 1. 测试用例配置测试
# ─────────────────────────────────────────────
def test_seed_test_cases_exist():
    """验证内置 6 个测试用例存在"""
    expected_ids = [
        "case_ai_news_short",
        "case_article_to_video",
        "case_emotional_short",
        "case_product_intro",
        "case_image_motion",
        "case_knowledge_explainer",
    ]
    actual_ids = [tc.id for tc in SEED_TEST_CASES]
    for eid in expected_ids:
        assert eid in actual_ids, f"Missing test case: {eid}"
    assert len(SEED_TEST_CASES) == 6


def test_test_case_ai_news_short():
    tc = get_test_case_by_id("case_ai_news_short")
    assert tc is not None
    assert tc.name == "AI 资讯短视频"
    assert tc.targetDurationSec == 45
    assert tc.aspectRatio == "9:16"
    assert "信息表达清晰度" in tc.evaluationFocus


# ─────────────────────────────────────────────
# 2. 生成方案配置测试
# ─────────────────────────────────────────────
def test_seed_methods_exist():
    """验证内置 6 类生成方案存在"""
    expected_categories = [
        MethodCategory.LOCAL_FRAME_COMPOSE,
        MethodCategory.LOCAL_MEDIA_COMPOSE,
        MethodCategory.TEMPLATE_PROGRAMMATIC_RENDER,
        MethodCategory.AI_VIDEO_DIRECT,
        MethodCategory.AI_ASSET_THEN_COMPOSE,
        MethodCategory.HYBRID_PIPELINE,
    ]
    actual_categories = [m.category for m in SEED_VIDEO_METHODS]
    for cat in expected_categories:
        assert cat in actual_categories, f"Missing method category: {cat}"
    assert len(SEED_VIDEO_METHODS) == 6


def test_methods_have_required_fields():
    """验证每个 method 包含必需字段"""
    required_fields = [
        "id", "name", "category", "description",
        "suitableScenarios", "unsuitableScenarios",
        "inputRequirements", "outputType",
        "costLevel", "controlLevel", "stabilityLevel", "productizationLevel",
        "implementationStatus",
    ]
    for m in SEED_VIDEO_METHODS:
        for field in required_fields:
            assert hasattr(m, field), f"Method {m.id} missing field: {field}"


def test_all_categories_registered():
    """验证所有 method category 都已注册 adapter"""
    for cat in MethodCategory:
        assert get_adapter_for_category(cat) is not None, f"Adapter not registered: {cat.value}"
    assert len(list_registered_categories()) == 6


# ─────────────────────────────────────────────
# 3. Advisor 测试
# ─────────────────────────────────────────────
def test_advisor_ai_news_short():
    """AI 资讯短视频应推荐 template_programmatic_render"""
    advice = getVideoMethodAdvice("case_ai_news_short")
    assert advice is not None
    assert advice.recommendedMethodId == "method_template_programmatic_render"
    assert "method_ai_video_direct" in advice.notRecommendedMethodIds


def test_advisor_emotional_short():
    """情绪短片应推荐 ai_video_direct"""
    advice = getVideoMethodAdvice("case_emotional_short")
    assert advice is not None
    assert advice.recommendedMethodId == "method_ai_video_direct"
    assert "method_local_frame_compose" in advice.notRecommendedMethodIds


def test_advisor_product_intro():
    """产品介绍不推荐 ai_video_direct"""
    advice = getVideoMethodAdvice("case_product_intro")
    assert advice is not None
    assert "method_ai_video_direct" in advice.notRecommendedMethodIds


def test_advisor_knowledge_explainer():
    """知识讲解不推荐 ai_video_direct"""
    advice = getVideoMethodAdvice("case_knowledge_explainer")
    assert advice is not None
    assert advice.recommendedMethodId == "method_template_programmatic_render"
    assert "method_ai_video_direct" in advice.notRecommendedMethodIds


def test_advisor_image_motion():
    """图片动起来推荐 ai_video_direct"""
    advice = getVideoMethodAdvice("case_image_motion")
    assert advice is not None
    assert advice.recommendedMethodId == "method_ai_video_direct"


# ─────────────────────────────────────────────
# 4. Experiment Runner 测试
# ─────────────────────────────────────────────
def test_experiment_runs_different_adapters():
    """
    验证不同 method category 走不同 adapter 分支，
    不能所有 method 返回完全相同结果
    """
    runner = get_runner()

    # 创建实验，使用不同 method
    categories_results = {}

    method_ids = [m.id for m in SEED_VIDEO_METHODS]
    for method_id in method_ids:
        # 找一个 test case
        tc = SEED_TEST_CASES[0]
        exp = runner.create_experiment(
            test_case_id=tc.id,
            method_id=method_id,
            title=f"Test {method_id}",
            input_payload={"test": "data"},
            params={},
        )
        result = runner.run_experiment(exp.id)
        categories_results[method_id] = result.adapter

    # 验证不同 method 确实走了不同 adapter
    unique_adapters = set(categories_results.values())
    # 6 个 method 应该至少有 4 个不同的 adapter (因为 ai_video_direct 和一些是 mock 状态)
    assert len(unique_adapters) >= 4, f"Expected multiple adapters, got: {unique_adapters}"

    # 验证 adapter 名称与 method category 对应
    assert categories_results["method_local_frame_compose"] == "local_frame_compose"
    assert categories_results["method_local_media_compose"] == "local_media_compose"
    assert categories_results["method_template_programmatic_render"] == "template_programmatic_render"


def test_experiment_workflow():
    """验证实验创建→运行→结果获取的完整流程"""
    runner = get_runner()
    tc = SEED_TEST_CASES[0]
    method = SEED_VIDEO_METHODS[0]

    exp = runner.create_experiment(
        test_case_id=tc.id,
        method_id=method.id,
        title="流程测试实验",
        input_payload={"content": "test"},
        params={},
    )

    assert exp.status == "pending"
    assert exp.id.startswith("exp_")

    result = runner.run_experiment(exp.id)
    assert result.experimentId == exp.id
    assert len(result.logs) > 0

    # 再次获取状态
    exp2 = runner.get_experiment(exp.id)
    assert exp2.status == "succeeded"
    assert exp2.elapsedMs is not None


def test_unknown_method_fails():
    """使用不存在的 method 应该失败"""
    runner = get_runner()
    tc = SEED_TEST_CASES[0]

    exp = runner.create_experiment(
        test_case_id=tc.id,
        method_id="nonexistent_method",
        title="应该失败的实验",
        input_payload={},
        params={},
    )

    try:
        runner.run_experiment(exp.id)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Method not found" in str(e)


if __name__ == "__main__":
    # Run with pytest
    import pytest
    pytest.main([__file__, "-v"])
