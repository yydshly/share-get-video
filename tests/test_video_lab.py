"""
Video Capability Lab - Tests
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.models import MethodCategory, ArtifactType
from app.video_lab.seed_data import SEED_TEST_CASES, SEED_VIDEO_METHODS, get_test_case_by_id, get_method_by_id, AI_INSIGHT_SUMMARY_DEFAULT
from app.video_lab.advisor import getVideoMethodAdvice
from app.video_lab.method_registry import get_adapter_for_category, list_registered_categories
from app.video_lab.experiment_runner import get_runner
from app.video_lab.planners.pipeline_builder import build_12step_pipeline


# ─────────────────────────────────────────────
# 1. 测试用例配置测试
# ─────────────────────────────────────────────
def test_seed_test_cases_exist():
    """验证内置 7 个测试用例存在"""
    expected_ids = [
        "case_ai_frontier_daily_001",
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
    assert len(SEED_TEST_CASES) == 7


def test_case_ai_frontier_daily_001_exists():
    """验证 AI 前沿日报测试用例存在"""
    tc = get_test_case_by_id("case_ai_frontier_daily_001")
    assert tc is not None
    assert tc.name == "今日 AI 前沿共享短视频"
    assert tc.targetDurationSec == 45
    assert tc.aspectRatio == "9:16"
    assert "信息准确性" in tc.evaluationFocus
    assert tc.recommendedPriority == 1


def test_case_ai_frontier_default_input():
    """验证 AI 前沿日报默认输入内容不为空"""
    assert AI_INSIGHT_SUMMARY_DEFAULT is not None
    assert len(AI_INSIGHT_SUMMARY_DEFAULT) > 100


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
def test_advisor_ai_frontier_daily_001():
    """AI 前沿日报应推荐 template_programmatic_render，不推荐 ai_video_direct"""
    advice = getVideoMethodAdvice("case_ai_frontier_daily_001")
    assert advice is not None
    assert advice.recommendedMethodId == "method_template_programmatic_render"
    assert "method_ai_video_direct" in advice.notRecommendedMethodIds
    assert "method_ai_asset_then_compose" in advice.backupMethodIds
    assert advice.productizationLevel.value == "high"


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
# 4. Production Steps 测试
# ─────────────────────────────────────────────
def test_12step_pipeline():
    """验证 12 步骤流水线"""
    steps = build_12step_pipeline(
        experiment_id="exp_test",
        test_case_id="case_ai_frontier_daily_001",
        method_category="template_programmatic_render",
        input_payload={"content": AI_INSIGHT_SUMMARY_DEFAULT},
        params={"targetDuration": 45, "aspectRatio": "9:16"},
    )

    assert len(steps) == 12

    # 验证步骤顺序
    expected_step_names = [
        "接收输入内容",
        "内容结构化",
        "提取视频关键信息点",
        "判断视频表达类型",
        "选择生成方案",
        "生成共享视频脚本",
        "生成分镜",
        "生成旁白与字幕计划",
        "生成素材计划",
        "生成渲染计划",
        "执行 mock 渲染",
        "生成总结建议",
    ]
    for i, (step, expected_name) in enumerate(zip(steps, expected_step_names)):
        assert step.name == expected_name, f"Step {i}: expected '{expected_name}', got '{step.name}'"
        assert step.status.value == "succeeded", f"Step {i} status is {step.status.value}"


def test_12step_pipeline_artifacts():
    """验证流水线产出的 artifacts"""
    steps = build_12step_pipeline(
        experiment_id="exp_test",
        test_case_id="case_ai_frontier_daily_001",
        method_category="template_programmatic_render",
        input_payload={"content": AI_INSIGHT_SUMMARY_DEFAULT},
        params={"targetDuration": 45, "aspectRatio": "9:16"},
    )

    # 收集所有 artifacts
    all_artifacts = []
    for step in steps:
        all_artifacts.extend(step.artifacts)

    artifact_types = [a.type for a in all_artifacts]
    artifact_type_values = [t.value for t in artifact_types]

    # 验证关键 artifact 类型存在
    assert "script" in artifact_type_values, "Missing script artifact"
    assert "storyboard" in artifact_type_values, "Missing storyboard artifact"
    assert "subtitle_plan" in artifact_type_values, "Missing subtitle_plan artifact"
    assert "voiceover_plan" in artifact_type_values, "Missing voiceover_plan artifact"
    assert "asset_plan" in artifact_type_values, "Missing asset_plan artifact"
    assert "render_plan" in artifact_type_values, "Missing render_plan artifact"
    assert "mock_video" in artifact_type_values, "Missing mock_video artifact"


# ─────────────────────────────────────────────
# 5. Experiment Runner 测试
# ─────────────────────────────────────────────
def test_experiment_runs_different_adapters():
    """验证不同 method category 走不同 adapter 分支"""
    runner = get_runner()

    categories_results = {}

    method_ids = [m.id for m in SEED_VIDEO_METHODS]
    for method_id in method_ids:
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

    unique_adapters = set(categories_results.values())
    assert len(unique_adapters) >= 4, f"Expected multiple adapters, got: {unique_adapters}"

    assert categories_results["method_local_frame_compose"] == "local_frame_compose"
    assert categories_results["method_local_media_compose"] == "local_media_compose"
    assert categories_results["method_template_programmatic_render"] == "template_programmatic_render"


def test_experiment_with_ai_frontier_and_template_renders_7_steps():
    """验证 AI 前沿 + template_programmatic_render 渲染出 7 步骤 (V0.3.1)"""
    from unittest.mock import patch, MagicMock

    # Mock Remotion environment to avoid real Node/Chrome dependency in tests
    with patch("app.video_lab.adapters.remotion_template.check_remotion_available") as mock_check, \
         patch("app.video_lab.adapters.remotion_template.render_remotion_video") as mock_render:
        mock_check.return_value = (True, "OK")
        mock_render.return_value = {
            "success": True,
            "videoUrl": "/runtime/video_lab/experiments/test/output.mp4",
            "manifestUrl": "/runtime/video_lab/experiments/test/manifest.json",
            "message": "Success",
            "logs": ["[Remotion] OK"],
            "warnings": [],
        }

        runner = get_runner()
        tc = get_test_case_by_id("case_ai_frontier_daily_001")
        method = get_method_by_id("method_template_programmatic_render")

        exp = runner.create_experiment(
            test_case_id=tc.id,
            method_id=method.id,
            title="AI前沿-Remotion方案",
            input_payload={"content": AI_INSIGHT_SUMMARY_DEFAULT},
            params={"targetDuration": 45, "aspectRatio": "9:16"},
        )

        result = runner.run_experiment(exp.id)

    assert len(result.productionSteps) == 7, f"Expected 7 steps (V0.3.1), got {len(result.productionSteps)}"

    # 验证有 artifacts
    all_artifacts = []
    for step in result.productionSteps:
        all_artifacts.extend(step.artifacts)
    assert len(all_artifacts) > 0, "No artifacts produced"


def test_ai_video_direct_returns_4_steps():
    """ai_video_direct 返回较短的步骤（reserved 状态）"""
    runner = get_runner()
    tc = SEED_TEST_CASES[0]
    method = get_method_by_id("method_ai_video_direct")

    exp = runner.create_experiment(
        test_case_id=tc.id,
        method_id=method.id,
        title="AI视频-direct测试",
        input_payload={"content": "test"},
        params={},
    )

    result = runner.run_experiment(exp.id)

    # ai_video_direct 返回 4 步骤而非 12
    assert len(result.productionSteps) == 4, f"Expected 4 steps, got {len(result.productionSteps)}"
    # 有风险评估 artifact
    all_artifacts = []
    for step in result.productionSteps:
        all_artifacts.extend(step.artifacts)
    assert len(all_artifacts) > 0


def test_different_methods_produce_different_steps():
    """验证不同 method 返回不同的步骤和日志"""
    from unittest.mock import patch, MagicMock

    # Mock Remotion environment for template_programmatic_render
    with patch("app.video_lab.adapters.remotion_template.check_remotion_available") as mock_check, \
         patch("app.video_lab.adapters.remotion_template.render_remotion_video") as mock_render:
        mock_check.return_value = (True, "OK")
        mock_render.return_value = {
            "success": True,
            "videoUrl": "/runtime/video_lab/experiments/test/output.mp4",
            "manifestUrl": "/runtime/video_lab/experiments/test/manifest.json",
            "message": "Success",
            "logs": ["[Remotion] OK"],
            "warnings": [],
        }

        runner = get_runner()
        tc = get_test_case_by_id("case_ai_frontier_daily_001")

        results = {}
        for method_id in ["method_template_programmatic_render", "method_local_media_compose", "method_ai_video_direct"]:
            method = get_method_by_id(method_id)
            exp = runner.create_experiment(
                test_case_id=tc.id,
                method_id=method.id,
                title=f"对比 {method_id}",
                input_payload={"content": AI_INSIGHT_SUMMARY_DEFAULT},
                params={"targetDuration": 45},
            )
            results[method_id] = runner.run_experiment(exp.id)

    # 步骤数量不同
    step_counts = [len(r.productionSteps) for r in results.values()]
    assert len(set(step_counts)) > 1, f"Expected different step counts, got: {step_counts}"

    # rawOutput.riskAssessment 不同
    assert results["method_template_programmatic_render"].rawOutput.get("productizationRecommendation") == "recommended"
    assert results["method_ai_video_direct"].rawOutput.get("productizationRecommendation") == "not_recommended"


def test_experiment_workflow():
    """验证实验创建→运行→结果获取的完整流程"""
    # Use a fresh runner to avoid state pollution from other tests
    from app.video_lab.experiment_runner import ExperimentRunner
    runner = ExperimentRunner()
    tc = SEED_TEST_CASES[0]
    method = SEED_VIDEO_METHODS[0]

    exp = runner.create_experiment(
        test_case_id=tc.id,
        method_id=method.id,
        title="流程测试实验",
        input_payload={"content": "test"},
        params={},
    )

    assert exp.status.value == "pending"
    assert exp.id.startswith("exp_")

    result = runner.run_experiment(exp.id)
    assert result.experimentId == exp.id
    assert len(result.logs) > 0

    exp2 = runner.get_experiment(exp.id)
    # status depends on FFmpeg availability; the key check is that the runner
    # correctly stores and returns the experiment after run
    assert exp2 is not None
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
    import pytest
    pytest.main([__file__, "-v"])
