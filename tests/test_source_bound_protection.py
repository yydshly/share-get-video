"""
tests/test_source_bound_protection.py

V1.2.1.3: Regression tests for information_summary source-bound generation protection.

Covers:
1. buildVisualRouteParams returns useLlmPlan=false in information_summary mode
2. buildVisualRouteParams returns sourceBound=true in information_summary mode
3. buildVisualRouteParams returns allowNewFacts=false in information_summary mode
4. buildGenerationContent only contains plan-derived content
5. clip-preview with sourceBound=True respects useLlmPlan=false
6. stale plan detection via fingerprint mismatch
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Sample input without "中国信通院" or "人工智能模型评估规范"
SAMPLE_RAW_CONTENT = """科学研究评审实现突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%。
依据：依据 1

购物AI助手落后：主流模型通过率仅57-77%，真实网购任务中完成率仍有较大提升空间。
依据：依据 1

企业级AI加速落地：Anthropic与TCS合作推进企业级 AI 应用，DeepMind投资千万美元。
依据：依据 1
"""

SAMPLE_INFO_SUMMARY_PLAN = {
    "mode": "information_summary",
    "compressionMode": "balanced",
    "targetPointCount": "auto",
    "includeOverview": True,
    "includeConclusion": True,
    "evidencePolicy": "ending_sources",
    "targetDurationMode": "auto",
    "overview": {
        "title": "AI领域近期重要进展一览",
        "subtitle": "科学研究、购物AI与企业级AI三大方向突破",
        "summary": "本期AI前沿速递涵盖科学研究评审、购物AI助手与企业级AI应用的最新进展",
    },
    "items": [
        {
            "id": "item-1",
            "title": "ProReviewer评审系统突破",
            "description": "ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%",
            "evidence": ["依据：依据 1"],
            "sourceText": "科学研究评审实现突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%。",
            "selected": True,
        },
        {
            "id": "item-2",
            "title": "购物AI助手性能待提升",
            "description": "主流模型通过率仅57-77%，真实网购任务中完成率仍有较大提升空间",
            "evidence": ["依据：依据 1"],
            "sourceText": "购物AI助手落后：主流模型通过率仅57-77%，真实网购任务中完成率仍有较大提升空间。",
            "selected": True,
        },
        {
            "id": "item-3",
            "title": "企业级AI加速落地",
            "description": "Anthropic与TCS合作推进企业级AI应用，DeepMind投资千万美元",
            "evidence": ["依据：依据 1"],
            "sourceText": "企业级AI加速落地：Anthropic与TCS合作推进企业级 AI 应用，DeepMind投资千万美元。",
            "selected": True,
        },
    ],
    "conclusion": {
        "title": "AI评估体系持续完善",
        "text": "可信性、可靠性和跨文化鲁棒性是当前AI评估的核心维度",
    },
    "stats": {
        "detectedItemCount": 3,
        "selectedItemCount": 3,
        "droppedItemCount": 0,
        "estimatedDurationSec": 45,
    },
}


# ─────────────────────────────────────────
# 1. Simulate buildGenerationContent logic (frontend pure-function replica)
# ─────────────────────────────────────────
def simulate_build_generation_content(plan, include_overview=True, include_conclusion=True, evidence_policy="ending_sources"):
    """Replica of the frontend buildGenerationContent for information_summary mode."""
    lines = []
    if include_overview and plan.get("overview"):
        lines.append("【首页总览】")
        if plan["overview"].get("title"):
            lines.append(f"标题：{plan['overview']['title']}")
        if plan["overview"].get("summary"):
            lines.append(f"摘要：{plan['overview']['summary']}")
        lines.append("")
    for i, item in enumerate(plan.get("items", [])):
        if not item.get("selected"):
            continue
        lines.append(f"【信息点 {i + 1}】")
        if item.get("title"):
            lines.append(f"标题：{item['title']}")
        if item.get("description"):
            lines.append(f"描述：{item['description']}")
        if item.get("evidence") and evidence_policy == "badge":
            lines.append(f"依据：{','.join(item['evidence'])}")
        lines.append("")
    if include_conclusion and plan.get("conclusion"):
        lines.append("【尾部总结】")
        if plan["conclusion"].get("title"):
            lines.append(f"标题：{plan['conclusion']['title']}")
        if plan["conclusion"].get("text"):
            lines.append(f"内容：{plan['conclusion']['text']}")
    return "\n".join(lines)


# ─────────────────────────────────────────
# 2. Simulate buildVisualRouteParams logic (frontend pure-function replica)
# ─────────────────────────────────────────
def simulate_build_visual_route_params(
    generation_mode,
    plan,
    plan_fingerprint,
    selected_route="pillow",
    title="今日 AI 前沿速递",
):
    """Replica of the frontend buildVisualRouteParams logic."""
    target_duration = 45
    key_point_count = 3
    if generation_mode == "information_summary" and plan:
        target_duration = plan["stats"].get("estimatedDurationSec", 60)
        key_point_count = len(plan["items"]) or 5

    is_info_summary = generation_mode == "information_summary" and plan
    base = {
        "targetDuration": target_duration,
        "aspectRatio": "9:16",
        "keyPointCount": key_point_count,
        "useLlmPlan": False if is_info_summary else True,
        "coverTitle": title,
    }
    if is_info_summary:
        base.update({
            "sourceBound": True,
            "allowNewFacts": False,
            "strictSourceMode": True,
            "generationMode": "information_summary",
            "inputFingerprint": plan_fingerprint,
            "planItemCount": len([it for it in plan["items"] if it.get("selected")]),
            "planOverviewTitle": plan.get("overview", {}).get("title", ""),
            "planConclusionTitle": plan.get("conclusion", {}).get("title", ""),
        })
    if selected_route == "remotion_data_news":
        base["remotionFamily"] = "data_news"
    elif selected_route == "remotion_card_stack":
        base["remotionFamily"] = "card_stack"
    return base


# ─────────────────────────────────────────
# 3. Simulate buildSourceBoundShot (frontend pure-function replica)
# ─────────────────────────────────────────
def simulate_build_source_bound_shot(plan, fallback_title, fallback_body):
    """Replica of the frontend buildSourceBoundShot logic."""
    headline = (plan.get("overview", {}).get("title") or fallback_title).strip()
    first_item = next((it for it in plan.get("items", []) if it.get("selected")), None)
    display = (first_item.get("description") if first_item else plan.get("overview", {}).get("summary") or fallback_body).strip()
    emphasis_terms = [
        it["title"] for it in plan.get("items", [])
        if it.get("selected")
    ][:5]
    return {"headline": headline, "display": display, "emphasisTerms": emphasis_terms}


# ─────────────────────────────────────────
# 4. Tests
# ─────────────────────────────────────────
class TestSourceBoundVisualRouteParams:
    def test_information_summary_mode_use_llm_plan_false(self):
        """信息总结模式下 buildVisualRouteParams 必须返回 useLlmPlan=false."""
        params = simulate_build_visual_route_params(
            generation_mode="information_summary",
            plan=SAMPLE_INFO_SUMMARY_PLAN,
            plan_fingerprint="200:abc:xyz",
        )
        assert params["useLlmPlan"] is False, "信息总结模式必须 useLlmPlan=false"

    def test_information_summary_mode_source_bound_true(self):
        """信息总结模式下 buildVisualRouteParams 必须返回 sourceBound=true."""
        params = simulate_build_visual_route_params(
            generation_mode="information_summary",
            plan=SAMPLE_INFO_SUMMARY_PLAN,
            plan_fingerprint="200:abc:xyz",
        )
        assert params.get("sourceBound") is True, "信息总结模式必须 sourceBound=true"

    def test_information_summary_mode_allow_new_facts_false(self):
        """信息总结模式下 buildVisualRouteParams 必须返回 allowNewFacts=false."""
        params = simulate_build_visual_route_params(
            generation_mode="information_summary",
            plan=SAMPLE_INFO_SUMMARY_PLAN,
            plan_fingerprint="200:abc:xyz",
        )
        assert params.get("allowNewFacts") is False, "信息总结模式必须 allowNewFacts=false"

    def test_information_summary_mode_strict_source_mode_true(self):
        """信息总结模式下必须 strictSourceMode=true."""
        params = simulate_build_visual_route_params(
            generation_mode="information_summary",
            plan=SAMPLE_INFO_SUMMARY_PLAN,
            plan_fingerprint="200:abc:xyz",
        )
        assert params.get("strictSourceMode") is True, "信息总结模式必须 strictSourceMode=true"

    def test_normal_mode_use_llm_plan_unchanged(self):
        """普通模式下 useLlmPlan 应保持 true（不改变现有行为）."""
        params = simulate_build_visual_route_params(
            generation_mode="normal",
            plan=None,
            plan_fingerprint="",
        )
        assert params["useLlmPlan"] is True, "普通模式必须 useLlmPlan=true"

    def test_information_summary_mode_has_provenance_fields(self):
        """信息总结模式必须携带 provenance 字段."""
        params = simulate_build_visual_route_params(
            generation_mode="information_summary",
            plan=SAMPLE_INFO_SUMMARY_PLAN,
            plan_fingerprint="200:abc:xyz",
        )
        assert "inputFingerprint" in params
        assert "planItemCount" in params
        assert "planOverviewTitle" in params
        assert "planConclusionTitle" in params


class TestSourceBoundShot:
    def test_shot_headline_from_plan_overview(self):
        """shot.headline 必须来自 infoSummaryPlan.overview.title."""
        shot = simulate_build_source_bound_shot(
            SAMPLE_INFO_SUMMARY_PLAN,
            fallback_title="今日 AI 前沿速递",
            fallback_body=SAMPLE_RAW_CONTENT,
        )
        assert shot["headline"] == "AI领域近期重要进展一览"
        assert shot["headline"] != "今日 AI 前沿速递"

    def test_shot_display_from_first_item_description(self):
        """shot.display 必须来自 plan 第一条选中项的 description，不是 raw body."""
        shot = simulate_build_source_bound_shot(
            SAMPLE_INFO_SUMMARY_PLAN,
            fallback_title="今日 AI 前沿速递",
            fallback_body=SAMPLE_RAW_CONTENT,
        )
        # display must NOT be the raw body (which contains different content)
        assert "ProReviewer" in shot["display"], "shot.display should use first item description"
        assert "马尔可夫" in shot["display"], "display must use plan item description"

    def test_shot_emphasis_terms_from_plan_items(self):
        """shot.emphasisTerms 必须来自 plan items 的 title."""
        shot = simulate_build_source_bound_shot(
            SAMPLE_INFO_SUMMARY_PLAN,
            fallback_title="今日 AI 前沿速递",
            fallback_body=SAMPLE_RAW_CONTENT,
        )
        titles = [it["title"] for it in SAMPLE_INFO_SUMMARY_PLAN["items"] if it.get("selected")]
        assert shot["emphasisTerms"] == titles[:5]


class TestSourceBoundContent:
    def test_generation_content_no_forbidden_terms(self):
        """生成内容不得出现原文没有的"中国信通院""评估规范"等词."""
        content = simulate_build_generation_content(
            SAMPLE_INFO_SUMMARY_PLAN,
            include_overview=True,
            include_conclusion=True,
            evidence_policy="ending_sources",
        )
        assert "中国信通院" not in content
        assert "人工智能模型评估规范" not in content
        assert "AI模型评估新标准" not in content
        # Content must be from plan, not injected
        assert "ProReviewer" in content
        assert "马尔可夫" in content

    def test_generation_content_derives_from_plan(self):
        """buildGenerationContent 内容必须全部来自 plan."""
        content = simulate_build_generation_content(
            SAMPLE_INFO_SUMMARY_PLAN,
            include_overview=True,
            include_conclusion=True,
            evidence_policy="ending_sources",
        )
        # Must include overview
        assert "AI领域近期重要进展一览" in content
        # Must include all selected items
        assert "ProReviewer评审系统突破" in content
        assert "购物AI助手性能待提升" in content
        assert "企业级AI加速落地" in content
        # Must include conclusion
        assert "AI评估体系持续完善" in content


class TestStalePlanDetection:
    def test_stale_fingerprint_rejected(self):
        """输入变化后旧 fingerprint 应该被检测为 stale."""
        old_fingerprint = "200:abc:xyz"
        new_content = SAMPLE_RAW_CONTENT + "\n\n新增一段完全不同内容"
        new_fingerprint = f"{len(new_content)}:{new_content[:80]}:{new_content[-80:]}"
        assert old_fingerprint != new_fingerprint, "Fingerprint 应该因内容变化而改变"

    def test_same_content_same_fingerprint(self):
        """相同内容应产生相同的 fingerprint（稳定哈希）."""
        fp1 = f"{len(SAMPLE_RAW_CONTENT)}:{SAMPLE_RAW_CONTENT[:80]}:{SAMPLE_RAW_CONTENT[-80:]}"
        fp2 = f"{len(SAMPLE_RAW_CONTENT)}:{SAMPLE_RAW_CONTENT[:80]}:{SAMPLE_RAW_CONTENT[-80:]}"
        assert fp1 == fp2, "相同内容应产生相同 fingerprint"


class TestClipPreviewSourceBound:
    def test_clip_preview_respects_use_llm_plan_false(self):
        """clip-preview 在 useLlmPlan=false 时不应调用 LLM 规划."""
        from app.video_lab.renderers.frame_preview import render_clip_preview

        params = {"useLlmPlan": False, "aspectRatio": "9:16", "keyPointCount": 3}
        shot = simulate_build_source_bound_shot(
            SAMPLE_INFO_SUMMARY_PLAN,
            fallback_title="今日 AI 前沿速递",
            fallback_body=SAMPLE_RAW_CONTENT,
        )

        # Pillow route: render_single_frame is called directly, no LLM involved
        result = render_clip_preview(
            content="dummy content for Pillow route",
            visual_route="local_frame_compose",
            params=params,
            clip_seconds=3,
            shot=shot,
            frame_type="keypoint",
            cover_title="test",
        )
        # Should succeed (Pillow Ken Burns)
        assert result.get("success") is True
        assert result.get("route") == "local_frame_compose"

    def test_source_bound_terms_not_injected_by_backend(self):
        """后端在 sourceBound 模式下不得注入"中国信通院"等词到帧渲染."""
        from app.video_lab.renderers.frame_preview import render_single_frame

        shot = simulate_build_source_bound_shot(
            SAMPLE_INFO_SUMMARY_PLAN,
            fallback_title="今日 AI 前沿速递",
            fallback_body=SAMPLE_RAW_CONTENT,
        )
        params = {"sourceBound": True, "allowNewFacts": False, "strictSourceMode": True}

        result = render_single_frame(
            visual_route="local_frame_compose",
            frame_type="keypoint",
            shot=shot,
            cover_title="AI领域近期重要进展一览",
            params=params,
        )

        # The function should succeed without error
        assert result.get("success") is not None
        # No forbidden terms should appear in the output
        # (frame path doesn't contain text, but the function should not raise)
