"""
Tests for V0.2.5 API parameter passing for local_frame_compose
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ─────────────────────────────────────────────
# Params are saved in experiment.params
# ─────────────────────────────────────────
def test_create_experiment_saves_params():
    """experiment.params should保存传入的参数."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "Params Save Test",
        "inputPayload": {"content": "测试内容"},
        "params": {
            "targetDuration": 30,
            "keyPointCount": 4,
            "highlightMode": "auto",
            "transitionEnabled": True,
            "transitionFrames": 2,
            "stylePreset": "ai_frontier_dark",
        },
    }

    resp = client.post("/video-lab/experiments", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    # Verify params are saved in experiment
    exp_params = data["experiment"].get("params", {})
    assert exp_params.get("targetDuration") == 30
    assert exp_params.get("keyPointCount") == 4
    assert exp_params.get("highlightMode") == "auto"
    assert exp_params.get("transitionEnabled") is True
    assert exp_params.get("transitionFrames") == 2
    assert exp_params.get("stylePreset") == "ai_frontier_dark"


# ─────────────────────────────────────────────
# result.assets.renderParams exists
# ─────────────────────────────────────────
def test_result_assets_has_render_params():
    """result.assets should contain renderParams after local_frame_compose."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "RenderParams in Assets Test",
        "inputPayload": {"content": "测试内容"},
        "params": {
            "targetDuration": 35,
            "keyPointCount": 3,
            "highlightMode": "numbers",
            "transitionEnabled": False,
            "transitionFrames": 0,
            "stylePreset": "ai_frontier_dark",
        },
    }

    resp = client.post("/video-lab/experiments", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data.get("result", {})
    assets = result.get("assets", {})

    assert "renderParams" in assets, f"assets should have renderParams: {assets.keys()}"
    render_params = assets["renderParams"]
    assert render_params["targetDuration"] == 35
    assert render_params["keyPointCount"] == 3
    assert render_params["highlightMode"] == "numbers"
    assert render_params["transitionEnabled"] is False
    assert render_params["transitionFrames"] == 0


# ─────────────────────────────────────────────
# manifest contains renderParams
# ─────────────────────────────────────────
def test_manifest_contains_render_params():
    """manifest.json should contain renderParams."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "Manifest RenderParams Test",
        "inputPayload": {"content": "测试内容"},
        "params": {
            "targetDuration": 40,
            "keyPointCount": 5,
            "highlightMode": "auto",
            "transitionEnabled": True,
            "transitionFrames": 4,
            "stylePreset": "ai_frontier_dark",
        },
    }

    resp = client.post("/video-lab/experiments", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data.get("result", {})
    production_steps = result.get("productionSteps", [])

    # Find the conclusion step with manifest
    conclusion_steps = [s for s in production_steps if s.get("name") == "Generate Conclusion"]
    assert len(conclusion_steps) > 0

    artifacts = conclusion_steps[0].get("artifacts", [])
    manifest_artifacts = [a for a in artifacts if a.get("type") == "manifest"]
    assert len(manifest_artifacts) > 0

    manifest_payload = manifest_artifacts[0].get("payload", {})
    assert "renderParams" in manifest_payload, f"manifest should have renderParams: {manifest_payload.keys()}"

    rp = manifest_payload["renderParams"]
    assert rp["targetDuration"] == 40
    assert rp["keyPointCount"] == 5
    assert rp["highlightMode"] == "auto"
    assert rp["transitionEnabled"] is True
    assert rp["transitionFrames"] == 4


# ─────────────────────────────────────────────
# step 4 and 5 keyData contain renderParams
# ─────────────────────────────────────────
def test_step_4_and_5_key_data_contain_render_params():
    """Step 4 (strategy) and step 5 (method) keyData should contain renderParams."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "Step keyData RenderParams Test",
        "inputPayload": {"content": "测试内容"},
        "params": {
            "targetDuration": 25,
            "keyPointCount": 2,
            "highlightMode": "none",
            "transitionEnabled": False,
            "transitionFrames": 0,
            "stylePreset": "ai_frontier_dark",
        },
    }

    resp = client.post("/video-lab/experiments", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data.get("result", {})
    production_steps = result.get("productionSteps", [])

    step4 = next((s for s in production_steps if "strategy" in s.get("name", "").lower()), None)
    step5 = next((s for s in production_steps if "method" in s.get("name", "").lower()), None)

    assert step4 is not None, "Step 4 (strategy) not found"
    assert step5 is not None, "Step 5 (method) not found"

    assert "renderParams" in step4.get("keyData", {}), f"Step 4 should have renderParams: {step4.get('keyData', {}).keys()}"
    assert "renderParams" in step5.get("keyData", {}), f"Step 5 should have renderParams: {step5.get('keyData', {}).keys()}"

    step4_rp = step4["keyData"]["renderParams"]
    assert step4_rp["targetDuration"] == 25
    assert step4_rp["highlightMode"] == "none"


# ─────────────────────────────────────────────
# rawOutput contains renderParams
# ─────────────────────────────────────────
def test_raw_output_contains_render_params():
    """result.rawOutput should contain renderParams."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "RawOutput RenderParams Test",
        "inputPayload": {"content": "测试内容"},
        "params": {
            "targetDuration": 50,
            "keyPointCount": 7,
            "highlightMode": "auto",
            "transitionEnabled": True,
            "transitionFrames": 6,
            "stylePreset": "ai_frontier_dark",
        },
    }

    resp = client.post("/video-lab/experiments", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data.get("result", {})
    raw_output = result.get("rawOutput", {})

    assert "renderParams" in raw_output, f"rawOutput should have renderParams: {raw_output.keys()}"

    rp = raw_output["renderParams"]
    assert rp["targetDuration"] == 50
    assert rp["keyPointCount"] == 7
    assert rp["transitionFrames"] == 6


# ─────────────────────────────────────────────
# transitionEnabled=false sets transitionFrames=0
# ─────────────────────────────────────────
def test_transition_enabled_false_means_no_transition_frames():
    """When transitionEnabled=false, transitionFrames should effectively be 0 in rendering."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "No Transition Test",
        "inputPayload": {"content": "测试内容"},
        "params": {
            "targetDuration": 20,
            "keyPointCount": 2,
            "highlightMode": "auto",
            "transitionEnabled": False,
            "transitionFrames": 0,
            "stylePreset": "ai_frontier_dark",
        },
    }

    resp = client.post("/video-lab/experiments", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data.get("result", {})
    assets = result.get("assets", {})
    render_params = assets.get("renderParams", {})

    # When transitionEnabled=false and transitionFrames=0, no transition frames should be generated
    assert render_params.get("transitionEnabled") is False
    assert render_params.get("transitionFrames") == 0


# ─────────────────────────────────────────────
# Default params when empty object
# ─────────────────────────────────────────
def test_empty_params_uses_defaults():
    """Empty params {} should use defaults."""
    payload = {
        "testCaseId": "case_ai_frontier_daily_001",
        "methodId": "method_local_frame_compose",
        "title": "Default Params Test",
        "inputPayload": {"content": "测试内容"},
        "params": {},
    }

    resp = client.post("/video-lab/experiments", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    result = data.get("result", {})
    assets = result.get("assets", {})
    render_params = assets.get("renderParams", {})

    assert render_params.get("targetDuration") == 45
    assert render_params.get("keyPointCount") == 6
    assert render_params.get("highlightMode") == "auto"
    assert render_params.get("transitionEnabled") is True
    assert render_params.get("transitionFrames") == 4


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
