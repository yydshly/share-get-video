import json
from pathlib import Path
from unittest.mock import MagicMock

from app.video_lab.adapters import tts_subtitle_compose as adapter
from app.video_lab.planners.source_bound_plan import (
    build_source_bound_plan_from_information_summary,
    build_structured_from_information_summary_plan,
)
from app.video_lab.renderers.visual.base import VisualRenderResult


def sample_info_plan() -> dict:
    return {
        "overview": {
            "title": "今日AI前沿",
            "summary": "可信性、可靠性和跨文化鲁棒性成为本期主线。",
        },
        "items": [
            {
                "title": "ProReviewer主动调查评审",
                "description": "ProReviewer将评审建模为马尔可夫决策过程，五个质量维度超越提示工程方法39%。",
                "evidence": ["依据 1"],
                "selected": True,
            },
            {
                "title": "RogueAI欺骗检测新范式",
                "description": "RogueAI将信任问题转化为审问游戏，用有限回合识别人机混合对话中的欺骗者。",
                "evidence": ["依据 1"],
                "selected": True,
            },
            {
                "title": "中国信通院人工智能模型评估规范",
                "description": "这条未选中内容不应进入视频计划。",
                "evidence": ["外部资料"],
                "selected": False,
            },
        ],
        "conclusion": {"title": "趋势总结", "text": "研究重心转向可信和可靠评估。"},
    }


def serialized_plan_text() -> str:
    return "\n".join(
        [
            "【首页总览】",
            "标题：今日AI前沿",
            "摘要：可信性、可靠性和跨文化鲁棒性成为本期主线。",
            "",
            "【信息点 1】",
            "标题：ProReviewer主动调查评审",
            "描述：ProReviewer将评审建模为马尔可夫决策过程。",
            "",
            "中国信通院人工智能模型评估规范",
        ]
    )


def source_bound_params(info_plan: dict) -> dict:
    selected_count = len([item for item in info_plan["items"] if item.get("selected")])
    return {
        "targetDuration": 45,
        "aspectRatio": "9:16",
        "keyPointCount": selected_count,
        "generationMode": "information_summary",
        "sourceBound": True,
        "allowNewFacts": False,
        "strictSourceMode": True,
        "useLlmPlan": False,
        "inputFingerprint": "fingerprint:test",
        "planItemCount": selected_count,
        "informationSummaryPlan": info_plan,
    }


def all_shot_text(plan: dict) -> str:
    return "\n".join(
        "\n".join(
            [
                shot.get("headline", ""),
                shot.get("display", ""),
                shot.get("narration", ""),
            ]
        )
        for shot in plan.get("shots", [])
    )


def test_build_source_bound_plan_shot_count_equals_selected_items():
    plan = build_source_bound_plan_from_information_summary(sample_info_plan())
    assert len(plan["shots"]) == 2


def test_shot_headline_display_narration_come_from_plan_item():
    plan = build_source_bound_plan_from_information_summary(sample_info_plan())
    first = plan["shots"][0]
    assert first["headline"] == "ProReviewer主动调查评审"
    assert "ProReviewer将评审建模" in first["display"]
    assert first["narration"] == "ProReviewer将评审建模为马尔可夫决策过程，五个质量维度超越提示工程方法39%。"


def test_unselected_item_does_not_enter_shots():
    plan = build_source_bound_plan_from_information_summary(sample_info_plan())
    text = all_shot_text(plan)
    assert "未选中内容" not in text


def test_placeholder_field_names_do_not_enter_generated_shots():
    plan = build_source_bound_plan_from_information_summary(sample_info_plan())
    text = all_shot_text(plan)
    assert "标题：" not in text
    assert "摘要：" not in text
    assert "【信息点 1】" not in text


def test_external_unselected_content_does_not_enter_generated_shots():
    plan = build_source_bound_plan_from_information_summary(sample_info_plan())
    text = all_shot_text(plan)
    assert "中国信通院" not in text
    assert "人工智能模型评估规范" not in text


def test_structured_artifact_uses_selected_plan_items_only():
    structured = build_structured_from_information_summary_plan(sample_info_plan())
    assert structured["source"] == "informationSummaryPlan"
    assert structured["totalItems"] == 2
    assert "中国信通院" not in json.dumps(structured, ensure_ascii=False)


def test_source_bound_run_skips_plan_shots_and_raw_structure_content(monkeypatch, tmp_path):
    result = run_adapter_with_mocks(monkeypatch, tmp_path)
    assert result.rawOutput["status"] == "succeeded"
    assert result.rawOutput["planSource"] == "informationSummaryPlan"


def test_source_bound_run_records_provenance_in_raw_output_and_manifest(monkeypatch, tmp_path):
    result = run_adapter_with_mocks(monkeypatch, tmp_path)
    assert result.rawOutput["generationMode"] == "information_summary"
    assert result.rawOutput["sourceBound"] is True
    assert result.rawOutput["allowNewFacts"] is False
    assert result.rawOutput["strictSourceMode"] is True
    assert result.rawOutput["planItemCount"] == 2
    assert result.rawOutput["inputFingerprint"] == "fingerprint:test"

    manifest = json.loads((tmp_path / "exp-native" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["planSource"] == "informationSummaryPlan"
    assert manifest["planItemCount"] == 2
    assert manifest["planDebug"]["shotCount"] == 2


def run_adapter_with_mocks(monkeypatch, tmp_path: Path):
    info_plan = sample_info_plan()
    params = source_bound_params(info_plan)

    def fail_structure_content(*args, **kwargs):
        raise AssertionError("structure_content must not parse serialized source-bound content")

    def fail_plan_shots(*args, **kwargs):
        raise AssertionError("plan_shots must not run in source-bound mode")

    monkeypatch.setattr(adapter, "structure_content", fail_structure_content)
    import app.video_lab.planners.llm_content_planner as llm_content_planner

    monkeypatch.setattr(llm_content_planner, "plan_shots", fail_plan_shots)
    monkeypatch.setattr(adapter, "ensure_runtime_exists", lambda: None)
    monkeypatch.setattr(adapter, "get_experiment_dir", lambda experiment_id: tmp_path / experiment_id)
    monkeypatch.setattr(adapter, "path_to_url", lambda path: f"/mock/{Path(path).name}")
    monkeypatch.setattr(
        adapter,
        "write_manifest",
        lambda experiment_id, manifest: _write_test_manifest(tmp_path / experiment_id, manifest),
    )
    monkeypatch.setattr(adapter, "check_ffmpeg_available", lambda: True)

    class FakeTTSClient:
        def is_configured(self):
            return True

        def generate(self, text, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake audio")
            return {
                "success": True,
                "audioPath": str(output_path),
                "durationSec": 8.0,
                "providerMessage": "ok",
            }

    class FakeRenderer:
        def render(self, request):
            video_path = tmp_path / request.experiment_id / "silent.mp4"
            video_path.parent.mkdir(parents=True, exist_ok=True)
            video_path.write_bytes(b"fake video")
            return VisualRenderResult(
                success=True,
                route_id="local_frame_compose",
                silent_video_path=str(video_path),
                cover_path=str(tmp_path / request.experiment_id / "cover.png"),
                total_duration_sec=8.0,
                frame_count=24,
            )

    monkeypatch.setattr(adapter, "MiniMaxTTSClient", FakeTTSClient)
    monkeypatch.setattr(adapter, "get_visual_renderer", lambda route: FakeRenderer())
    monkeypatch.setattr(
        adapter,
        "compose_av_with_subtitles",
        lambda **kwargs: {
            "success": True,
            "subtitle_renderer": "ass",
            "subtitle_style": {},
            "bgm_enabled": False,
            "bgm_mode": "none",
            "bgm_volume": 0.0,
        },
    )
    monkeypatch.setattr(adapter, "compose_video_with_audio", lambda **kwargs: {"success": True})

    fake_quality = MagicMock()
    fake_quality.to_dict.return_value = {
        "overallScore": 1.0,
        "dimensionScores": {},
        "counts": {},
        "checks": [],
        "needsHuman": [],
    }
    import app.video_lab.quality as quality

    monkeypatch.setattr(quality, "assess_quality", lambda *args, **kwargs: fake_quality)

    return adapter.run_tts_subtitle_compose(
        experiment_id="exp-native",
        test_case_id="test-native",
        input_payload={"content": serialized_plan_text()},
        params=params,
    )


def _write_test_manifest(exp_dir: Path, manifest: dict) -> Path:
    exp_dir.mkdir(parents=True, exist_ok=True)
    path = exp_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
