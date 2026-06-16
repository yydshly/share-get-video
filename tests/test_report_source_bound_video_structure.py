import json
from pathlib import Path
from unittest.mock import MagicMock

from app.video_lab.adapters import tts_subtitle_compose as adapter
from app.video_lab.planners.source_bound_plan import build_source_bound_plan_from_information_summary
from app.video_lab.renderers.local_frame_renderer import generate_frames
from app.video_lab.renderers.visual.base import VisualRenderResult


def report_plan() -> dict:
    return {
        "inputProfile": "report_overview_items",
        "reportTitle": "今日 AI 前沿速递",
        "includeOverview": True,
        "includeConclusion": True,
        "evidencePolicy": "ending_sources",
        "overview": {
            "title": "内容概览",
            "summary": "今日AI前沿呈现多条并行进展线索，研究重心转向可信性、可靠性和跨文化鲁棒性。",
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
                "evidence": ["依据 2"],
                "selected": True,
            },
        ],
        "conclusion": {"title": "趋势总结", "text": "研究重心转向可信和可靠评估。"},
    }


def key_points_from_plan(plan: dict) -> dict:
    source_plan = build_source_bound_plan_from_information_summary(plan)
    kps = [
        {
            "index": i,
            "headline": shot["headline"],
            "display": shot["display"],
            "narration": shot["narration"],
            "title": shot["headline"],
            "body": shot["display"],
            "emphasisTerms": shot["emphasisTerms"],
            "metrics": [],
        }
        for i, shot in enumerate(source_plan["shots"], 1)
    ]
    return {
        "keyPoints": kps,
        "key_points": kps,
        "structureType": source_plan["structureType"],
        "overview": source_plan["overview"],
        "sourceRefs": source_plan["sourceRefs"],
        "reportTitle": source_plan["reportTitle"],
        "includeOverview": source_plan["includeOverview"],
        "includeConclusion": source_plan["includeConclusion"],
    }


def test_source_bound_plan_display_does_not_include_evidence():
    plan = build_source_bound_plan_from_information_summary(report_plan())
    assert "依据" not in plan["shots"][0]["display"]


def test_source_bound_plan_narration_does_not_include_evidence():
    plan = build_source_bound_plan_from_information_summary(report_plan())
    assert "依据" not in plan["shots"][0]["narration"]


def test_source_bound_plan_source_refs_keep_evidence():
    plan = build_source_bound_plan_from_information_summary(report_plan())
    assert plan["sourceRefs"] == [
        {"itemIndex": 1, "itemTitle": "ProReviewer主动调查评审", "evidence": ["依据 1"]},
        {"itemIndex": 2, "itemTitle": "RogueAI欺骗检测新范式", "evidence": ["依据 2"]},
    ]


def test_report_source_bound_structure_contains_overview_summary():
    plan = build_source_bound_plan_from_information_summary(report_plan())
    assert plan["structureType"] == "report_source_bound"
    assert "今日AI前沿呈现多条并行进展线索" in plan["overview"]["summary"]


def test_report_source_bound_keypoint_count_equals_selected_items():
    plan = build_source_bound_plan_from_information_summary(report_plan())
    assert len(plan["shots"]) == 2


def test_report_frame_sequence_uses_report_overview_not_old_keypoint_list(monkeypatch, tmp_path):
    monkeypatch.setattr("app.video_lab.renderers.file_store.get_frames_dir", lambda experiment_id: tmp_path)
    plan = report_plan()
    result = generate_frames(
        experiment_id="report-frames",
        structured={"lead": plan["overview"]["summary"], "items": [], "totalItems": 2},
        key_points=key_points_from_plan(plan),
        target_duration_sec=30,
        resolution=(540, 960),
        enable_transitions=False,
        include_overview=True,
        include_summary=True,
        style_params={
            "sourceBound": True,
            "generationMode": "information_summary",
            "inputProfile": "report_overview_items",
            "informationSummaryPlan": plan,
        },
    )
    frames = result["frames"]
    assert [frame["type"] for frame in frames] == ["cover", "overview", "keypoint", "keypoint", "conclusion", "sources"]
    overview = next(frame for frame in frames if frame["type"] == "overview")
    assert "今日AI前沿呈现多条并行进展线索" in overview["body"]
    assert "ProReviewer主动调查评审" not in overview["body"]
    assert all(frame.get("title") != "今日重点" for frame in frames)
    assert all("依据" not in frame.get("body", "") for frame in frames if frame["type"] in ("cover", "overview", "keypoint", "conclusion"))


def test_report_tts_voiceover_does_not_include_evidence(monkeypatch, tmp_path):
    result = run_adapter_with_mocks(monkeypatch, tmp_path)
    voiceover_artifact = next(
        artifact
        for step in result.productionSteps
        for artifact in step.artifacts
        if artifact.title == "Voiceover Plan"
    )
    assert "依据" not in voiceover_artifact.payload["voiceoverText"]


def test_report_raw_output_and_manifest_record_structure_type(monkeypatch, tmp_path):
    result = run_adapter_with_mocks(monkeypatch, tmp_path)
    assert result.rawOutput["structureType"] == "report_source_bound"
    manifest = json.loads((tmp_path / "exp-report" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["structureType"] == "report_source_bound"
    assert manifest["planDebug"]["sourceRefs"][0]["evidence"] == ["依据 1"]


def run_adapter_with_mocks(monkeypatch, tmp_path: Path):
    plan = report_plan()
    params = {
        "targetDuration": 30,
        "aspectRatio": "9:16",
        "keyPointCount": 2,
        "generationMode": "information_summary",
        "sourceBound": True,
        "allowNewFacts": False,
        "strictSourceMode": True,
        "inputProfile": "report_overview_items",
        "useLlmPlan": False,
        "inputFingerprint": "fingerprint:report",
        "planItemCount": 2,
        "informationSummaryPlan": plan,
    }

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
            return {"success": True, "audioPath": str(output_path), "durationSec": 8.0, "providerMessage": "ok"}

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
                frame_count=4,
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
        experiment_id="exp-report",
        test_case_id="test-report",
        input_payload={"content": "serialized report content"},
        params=params,
    )


def _write_test_manifest(exp_dir: Path, manifest: dict) -> Path:
    exp_dir.mkdir(parents=True, exist_ok=True)
    path = exp_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
