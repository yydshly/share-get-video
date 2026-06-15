"""
Tests for the LLM content planner (deterministic fallback + normalization).
No network: tests use use_llm=False or exercise pure helpers.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.planners.llm_content_planner import (
    plan_shots,
    _normalize_plan,
    _find_shot_list,
    _extract_emphasis_terms,
    _shot_from_item,
)

REPORT = (
    "今日AI前沿三条要点。\n"
    "方言检测突破：阿尔及利亚方言谣言检测F1达0.84。\n"
    "依据： 依据 1\n"
    "评审升级：ProReviewer超越方法39%。\n"
    "依据： 依据 1\n"
    "购物短板：主流模型通过率57-77%。\n"
    "依据： 依据 1\n"
)


def test_fallback_plan_produces_shots():
    plan = plan_shots(REPORT, max_items=6, use_llm=False)
    assert plan["source"] == "fallback"
    assert len(plan["shots"]) == 3
    for s in plan["shots"]:
        assert s["headline"]
        assert "display" in s
        assert "narration" in s


def test_fallback_preserves_key_numbers_in_narration():
    plan = plan_shots(REPORT, max_items=6, use_llm=False)
    joined = " ".join(s["narration"] for s in plan["shots"])
    assert "0.84" in joined
    assert "39%" in joined
    assert "57-77%" in joined


def test_max_items_caps_shots():
    plan = plan_shots(REPORT, max_items=2, use_llm=False)
    assert len(plan["shots"]) == 2


def test_find_shot_list_handles_alternate_keys():
    # 模型可能用 subtitle 作为数组键
    raw = {"coverTitle": "T", "subtitle": [{"headline": "a", "display": "b", "narration": "c"}]}
    found = _find_shot_list(raw)
    assert len(found) == 1
    assert found[0]["headline"] == "a"


def test_normalize_plan_aligns_to_items_and_clamps():
    items = [{"title": "主体A：详情内容很多"}]
    raw = {
        "coverTitle": "标题",
        "opening": "开场",
        "shots": [{"headline": "h" * 50, "display": "d", "narration": "n"}],
        "closing": "收尾",
    }
    plan = _normalize_plan(raw, items, "总起")
    assert len(plan["shots"]) == 1  # 与源条目数一致
    assert len(plan["shots"][0]["headline"]) <= 18
    assert plan["opening"] == "开场"
    assert plan["closing"] == "收尾"


def test_normalize_plan_fills_missing_from_source():
    # LLM 只返回 1 条，但源有 2 条 → 必须补全到 2 条，不丢信息
    items = [{"title": "甲：内容甲"}, {"title": "乙：内容乙包含99%"}]
    raw = {"shots": [{"headline": "甲事", "display": "甲展示", "narration": "甲口播"}]}
    plan = _normalize_plan(raw, items, "总起")
    assert len(plan["shots"]) == 2
    # 第二条由源条目补全，保留信息
    assert "99%" in plan["shots"][1]["display"] or "内容乙" in plan["shots"][1]["display"]


def test_normalize_plan_empty_items():
    plan = _normalize_plan({"coverTitle": "x"}, [], "")
    assert plan["shots"] == []


# ─── V0.3.6-b1: emphasisTerms tests ────────────────────────────────────────

def test_extract_emphasis_terms_percentages():
    text = "错误拒绝率飙升至88.9%，从72%降至16%"
    terms = _extract_emphasis_terms(text)
    assert "88.9%" in terms
    assert "72%" in terms
    assert "16%" in terms


def test_extract_emphasis_terms_number_units():
    # Use ASCII-safe patterns: numbers with units
    text = "BBVA deploys ChatGPT to 10万 employees, Med-PaLM has 5620亿 params"
    terms = _extract_emphasis_terms(text)
    # Check our regex captures the Chinese-unit numbers
    unit_terms = [t for t in terms if "万" in t or "亿" in t]
    assert len(unit_terms) >= 2  # 10万 and 5620亿


def test_extract_emphasis_terms_model_names():
    text = "ProReviewer超越方法39%，OpenMedQ表现优异"
    terms = _extract_emphasis_terms(text)
    assert "ProReviewer" in terms
    assert "39%" in terms


def test_extract_emphasis_terms_deduplication():
    text = "88.9% 72% 88.9% 39%"
    terms = _extract_emphasis_terms(text)
    assert terms.count("88.9%") == 1
    assert len(terms) == 3


def test_extract_emphasis_terms_max_4():
    text = "1% 2% 3% 4% 5% 6%"
    terms = _extract_emphasis_terms(text)
    assert len(terms) <= 4


def test_extract_emphasis_terms_empty():
    assert _extract_emphasis_terms("") == []
    assert _extract_emphasis_terms("无数字无模型普通正文") == []


def test_fallback_shot_has_emphasis_terms():
    item = {"title": "ProReviewer评审系统突破39%"}  # no detail
    shot = _shot_from_item(item)
    assert "emphasisTerms" in shot
    assert isinstance(shot["emphasisTerms"], list)
    assert "ProReviewer" in shot["emphasisTerms"]
    assert "39%" in shot["emphasisTerms"]


def test_normalize_plan_retains_llm_emphasis_terms():
    items = [{"title": "ProReviewer评审系统突破39%"}]
    raw = {
        "coverTitle": "T",
        "opening": "开篇",
        "shots": [{
            "headline": "h",
            "display": "d",
            "narration": "n",
            "emphasisTerms": ["ProReviewer", "39%"],
        }],
        "closing": "收尾",
    }
    plan = _normalize_plan(raw, items, "")
    emp = plan["shots"][0]["emphasisTerms"]
    assert "ProReviewer" in emp
    assert "39%" in emp


def test_normalize_plan_auto_extracts_missing_emphasis_terms():
    items = [{"title": "BBVA宣布将ChatGPT部署至10万名员工"}]
    raw = {
        "shots": [{"headline": "h", "display": "d", "narration": "n"}],
        # no emphasisTerms
    }
    plan = _normalize_plan(raw, items, "")
    emp = plan["shots"][0]["emphasisTerms"]
    assert isinstance(emp, list)
    assert len(emp) <= 4


def test_normalize_plan_emphasis_terms_deduped():
    items = [{"title": "X"}]
    raw = {
        "shots": [{"headline": "h", "display": "d", "narration": "n",
                   "emphasisTerms": ["39%", "39%", "", "  "]}],
    }
    plan = _normalize_plan(raw, items, "")
    emp = plan["shots"][0]["emphasisTerms"]
    assert "" not in emp
    assert "  " not in emp
    assert emp.count("39%") == 1


def test_fallback_plan_has_emphasis_terms():
    plan = plan_shots(REPORT, max_items=6, use_llm=False)
    for s in plan["shots"]:
        assert "emphasisTerms" in s


# ─── V0.3.6-b1-fix tests ────────────────────────────────────────────────────

def test_normalize_plan_extracts_emphasis_after_fallback_fill():
    """When LLM returns empty headline/display and no emphasisTerms,
    normalize should fill from source AND extract emphasisTerms from filled text."""
    items = [{"title": "ProReviewer评审突破，错误拒绝率从88.9%降至16%"}]
    raw = {
        "shots": [{
            "headline": "",    # empty → will be filled from source
            "display": "",     # empty → will be filled from source
            "narration": "",
            # no emphasisTerms
        }],
    }
    plan = _normalize_plan(raw, items, "")
    shot = plan["shots"][0]
    # headline and display should be filled from source
    assert shot["headline"] != ""
    assert shot["display"] != ""
    # emphasisTerms should be extracted from filled content (not empty strings)
    emp = shot["emphasisTerms"]
    assert isinstance(emp, list)
    # Must extract either ProReviewer or 88.9% or 16%
    found = any(t in ["ProReviewer", "88.9%", "16%"] for t in emp)
    assert found, f"Expected ProReviewer or 88.9% or 16% in {emp}"


def test_default_opening_is_not_boring_template():
    """Default opening should not be the boring template phrase."""
    items = [{"title": "Test item"}]
    raw = {"shots": [{"headline": "h", "display": "d", "narration": "n"}]}
    plan = _normalize_plan(raw, items, "")
    opening = plan["opening"]
    assert opening != ""
    assert "今天为你梳理" not in opening
    assert "今天AI圈的重点，正在从能力走向落地。" in opening


# ─── V0.3.6-quality-p0: metrics extraction tests ───────────────────────────────

def test_extract_metrics_percentages():
    text = "ProReviewer错误拒绝率从88.9%降至16%，质量提升39%"
    metrics = _shot_from_item({"title": text})["metrics"]
    vals = [m["value"] for m in metrics]
    # Only first 2 metrics captured due to max_metrics=2 limit
    assert 88.9 in vals or 88 in vals
    assert 16.0 in vals or 16 in vals


def test_extract_metrics_range():
    text = "主流模型通过率57-77%"
    metrics = _shot_from_item({"title": text})["metrics"]
    assert len(metrics) >= 1
    m = metrics[0]
    assert m["unit"] == "%"
    assert m["min"] == 57
    assert m["max"] == 77


def test_extract_metrics_max_2():
    text = "准确率88.9%，F1分数0.84，召回率72%"
    metrics = _shot_from_item({"title": text})["metrics"]
    assert len(metrics) <= 2


def test_extract_metrics_units():
    text = "BBVA部署ChatGPT至10万员工，涉及5620亿参数"
    metrics = _shot_from_item({"title": text})["metrics"]
    assert len(metrics) >= 1
    units = [m["unit"] for m in metrics]
    # Should capture 万 or 亿
    assert any(u in ("万", "亿") for u in units)


def test_fallback_shot_has_metrics():
    item = {"title": "评审系统突破：错误率从88.9%降至16%"}
    shot = _shot_from_item(item)
    assert "metrics" in shot
    assert isinstance(shot["metrics"], list)
    assert len(shot["metrics"]) >= 1


def test_normalize_plan_retains_llm_metrics():
    items = [{"title": "ProReviewer评审突破"}]
    raw = {
        "coverTitle": "T",
        "opening": "开篇",
        "shots": [{
            "headline": "h",
            "display": "d",
            "narration": "n",
            "emphasisTerms": [],
            "metrics": [{"label": "质量提升", "value": 39, "unit": "%"}],
        }],
        "closing": "收尾",
    }
    plan = _normalize_plan(raw, items, "")
    m = plan["shots"][0]["metrics"]
    assert len(m) == 1
    assert m[0]["value"] == 39
    assert m[0]["unit"] == "%"


def test_fallback_plan_produces_shots_with_metrics():
    plan = plan_shots(REPORT, max_items=6, use_llm=False)
    assert plan["source"] == "fallback"
    assert len(plan["shots"]) == 3
    for s in plan["shots"]:
        assert "metrics" in s
        assert isinstance(s["metrics"], list)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
