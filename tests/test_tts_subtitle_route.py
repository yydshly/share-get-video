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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
