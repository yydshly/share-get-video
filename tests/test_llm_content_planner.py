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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
