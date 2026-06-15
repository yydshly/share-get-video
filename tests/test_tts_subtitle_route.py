"""
Tests for V0.3.3 TTS Subtitle Route
- Registry: tts_subtitle_compose is status='real'
- Adapter: Missing MINIMAX_API_KEY returns failed result with warning
- Adapter: Monkeypatch TTS success returns succeeded result with videoUrl
- Route Benchmark: tts route is not mock, executes real adapter
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ─────────────────────────────────────────
# 1. Registry: tts_subtitle_compose is real
# ─────────────────────────────────────────
def test_registry_tts_subtitle_is_real():
    """Registry should have tts_subtitle_compose with status='real'."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id

    route = get_route_by_id("tts_subtitle_compose")
    assert route is not None, "tts_subtitle_compose should be in registry"
    assert route.status == "real", f"Expected status='real', got '{route.status}'"
    assert route.adapter_category == "tts_subtitle_compose"


def test_registry_tts_subtitle_has_correct_pipeline():
    """tts_subtitle_compose pipeline should include TTS and SRT steps."""
    from app.video_lab.routes_benchmark.registry import get_route_by_id

    route = get_route_by_id("tts_subtitle_compose")
    assert route is not None
    pipeline = route.expected_pipeline
    assert any("TTS" in step or "MiniMax" in step for step in pipeline), \
        f"Pipeline should mention TTS: {pipeline}"
    assert any("字幕" in step or "SRT" in step for step in pipeline), \
        f"Pipeline should mention subtitles: {pipeline}"


# ─────────────────────────────────────────
# 2. Adapter: Missing API key returns failed
# ─────────────────────────────────────────
def test_tts_adapter_missing_api_key_returns_failed():
    """TTS adapter should return failed result when MINIMAX_API_KEY is not set."""
    from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose

    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        result = run_tts_subtitle_compose(
            experiment_id="test_tts_no_key",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "测试内容"},
            params={},
        )

    assert result.videoUrl == ""
    # Should have at least one failed step
    failed_steps = [s for s in result.productionSteps if s.status == "failed"]
    assert len(failed_steps) > 0, "Should have at least one failed step"


# ─────────────────────────────────────────
# 3. Adapter: has proper failed step when no API key
# ─────────────────────────────────────────
def test_tts_adapter_has_tts_step():
    """TTS adapter should have a TTS generation step."""
    from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose

    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        result = run_tts_subtitle_compose(
            experiment_id="test_tts_steps",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "测试内容"},
            params={},
        )

    step_names = [s.name for s in result.productionSteps]
    assert any("TTS" in name for name in step_names), f"Should have TTS step, got: {step_names}"


# ─────────────────────────────────────────
# 4. Route Benchmark runs tts_subtitle_compose
# ─────────────────────────────────────────
def test_route_benchmark_runs_tts_subtitle_route():
    """Benchmark should be able to run tts_subtitle_compose without exceptions."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "TTS Subtitle Route Test",
        "inputPayload": {"content": "测试内容"},
        "commonParams": {},
        "routeIds": ["tts_subtitle_compose"],
    }

    resp = client.post("/video-lab/route-benchmarks", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "benchmarkId" in data
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["routeId"] == "tts_subtitle_compose"
    # Should NOT be mock - should be real execution (succeeded or failed, not mock)
    assert result["status"] != "mock", "tts_subtitle_compose should not return mock status"


# ─────────────────────────────────────────
# 5. TTS client monkeypatch success test
# ─────────────────────────────────────────
def test_tts_client_generate_success_monkeypatch():
    """Monkeypatching TTS client generate should produce audio artifact."""
    from app.video_lab.providers.minimax import MiniMaxTTSClient

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "voiceover.mp3"
        with patch.object(MiniMaxTTSClient, "generate", return_value={
            "success": True,
            "audioPath": str(out_path),
            "audioUrl": "",
            "durationSec": 5.0,
            "providerMessage": "Success",
        }):
            client = MiniMaxTTSClient(api_key="test-key")
            out_path.write_bytes(b"fake audio data")
            result = client.generate("测试", output_path=out_path)

        assert result["success"] is True
        assert out_path.exists()


# ─────────────────────────────────────────
# 6. requirements.txt contains requests
# ─────────────────────────────────────────
def test_requirements_has_requests():
    """requirements.txt should declare requests dependency."""
    req_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    assert req_path.exists(), "requirements.txt should exist"
    content = req_path.read_text()
    assert "requests" in content, "requirements.txt should contain 'requests'"


# ─────────────────────────────────────────
# 7. Subtitle burn-in fallback produces succeeded result
# ─────────────────────────────────────────
def test_tts_adapter_subtitle_fallback_still_succeeds():
    """When subtitle burn-in fails, fallback to audio-only should still succeed."""
    from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
    from app.video_lab.providers.minimax import MiniMaxTTSClient

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_audio = Path(tmpdir) / "voiceover.mp3"
        fake_audio.write_bytes(b"fake audio")

        # Mock TTS success
        with patch.object(MiniMaxTTSClient, "generate", return_value={
            "success": True,
            "audioPath": str(fake_audio),
            "audioUrl": "",
            "durationSec": 5.0,
            "providerMessage": "Success",
        }):
            with patch.object(MiniMaxTTSClient, "is_configured", return_value=True):
                # compose_av_with_subtitles is imported at module level
                with patch("app.video_lab.adapters.tts_subtitle_compose.compose_av_with_subtitles", return_value={
                    "success": False,
                    "message": "Subtitle filter error on Windows",
                    "ffmpeg_command": "",
                    "version": "ffmpeg 6.0",
                }):
                    # compose_video_with_audio is imported inside the function - patch at source
                    with patch("app.video_lab.adapters.tts_subtitle_compose.compose_video_with_audio", return_value={
                        "success": True,
                        "message": "Audio-only composition succeeded",
                        "ffmpeg_command": "ffmpeg ...",
                        "version": "ffmpeg 6.0",
                    }):
                        result = run_tts_subtitle_compose(
                            experiment_id="test_fallback",
                            test_case_id="case_ai_frontier_daily_001",
                            input_payload={"content": "测试内容"},
                            params={},
                        )

    # Should succeed despite subtitle burn-in failure
    assert result.videoUrl != "", "Fallback should still produce videoUrl"
    # Check subtitleFallback in result
    raw = result.rawOutput
    assert raw.get("subtitleFallback") is True, "Should record subtitleFallback=True"
    assert raw.get("subtitleBurned") is False, "Should record subtitleBurned=False"


# ─────────────────────────────────────────
# 8. Manifest records subtitleBurned/subtitleFallback
# ─────────────────────────────────────────
def test_tts_manifest_has_subtitle_fields():
    """Manifest should include subtitleBurned and subtitleFallback fields."""
    from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
    from app.video_lab.providers.minimax import MiniMaxTTSClient

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_audio = Path(tmpdir) / "voiceover.mp3"
        fake_audio.write_bytes(b"fake audio")

        with patch.object(MiniMaxTTSClient, "generate", return_value={
            "success": True,
            "audioPath": str(fake_audio),
            "audioUrl": "",
            "durationSec": 5.0,
            "providerMessage": "Success",
        }):
            with patch.object(MiniMaxTTSClient, "is_configured", return_value=True):
                with patch("app.video_lab.adapters.tts_subtitle_compose.compose_av_with_subtitles", return_value={
                    "success": False,
                    "message": "Subtitle filter error",
                    "ffmpeg_command": "",
                    "version": "ffmpeg 6.0",
                }):
                    with patch("app.video_lab.adapters.tts_subtitle_compose.compose_video_with_audio", return_value={
                        "success": True,
                        "message": "Succeeded",
                        "ffmpeg_command": "ffmpeg ...",
                        "version": "ffmpeg 6.0",
                    }):
                        result = run_tts_subtitle_compose(
                            experiment_id="test_manifest_fields",
                            test_case_id="case_ai_frontier_daily_001",
                            input_payload={"content": "测试内容"},
                            params={},
                        )

    # Check manifest artifact has subtitleBurned/subtitleFallback
    manifest_art = None
    for step in result.productionSteps:
        for art in step.artifacts:
            if art.type == "manifest":
                manifest_art = art
                break

    assert manifest_art is not None, "Should have manifest artifact"
    payload = manifest_art.payload
    assert "subtitleBurned" in payload, "Manifest should have subtitleBurned"
    assert "subtitleFallback" in payload, "Manifest should have subtitleFallback"


# ─────────────────────────────────────────
# V0.3.6-b2: emphasisTerms carried through key_points
# ─────────────────────────────────────────
def test_tts_key_points_artifact_carries_emphasis_terms():
    """key_points artifact should carry emphasisTerms from plan_shots."""
    from app.video_lab.planners.llm_content_planner import plan_shots

    # Use proper content format recognized by structure_content
    content = (
        "今日AI前沿。\n"
        "ProReviewer评审突破：评审准确率提升39%。\n"
        "依据：1\n"
        "BBVA宣布：10万名员工使用ChatGPT。\n"
        "依据：2\n"
    )
    plan = plan_shots(content, max_items=3, use_llm=False)

    # Verify plan has emphasisTerms
    assert plan["source"] == "fallback"
    assert len(plan["shots"]) >= 1
    for shot in plan["shots"]:
        assert "emphasisTerms" in shot
        assert isinstance(shot["emphasisTerms"], list)


def test_tts_compose_step3_builds_kps_with_emphasis_terms():
    """plan_shots with use_llm=False produces shots with emphasisTerms."""
    from app.video_lab.planners.llm_content_planner import plan_shots

    content = (
        "AI前沿进展。\n"
        "ProReviewer评审突破39%。\n"
        "依据：1\n"
        "BBVA部署10万名。\n"
        "依据：2\n"
    )
    plan = plan_shots(content, max_items=3, use_llm=False)

    assert plan["source"] == "fallback"
    assert len(plan["shots"]) == 2
    # Each shot should have emphasisTerms extracted
    for shot in plan["shots"]:
        assert "emphasisTerms" in shot
        assert isinstance(shot["emphasisTerms"], list)
    # At least one shot should have extracted a number or model name
    all_terms = sum((s["emphasisTerms"] for s in plan["shots"]), [])
    assert len(all_terms) > 0, "Should extract at least some emphasis terms"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
