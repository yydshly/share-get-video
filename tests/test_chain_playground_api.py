"""
Tests for V0.3.4.1 Chain Playground API Endpoints
- GET /video-lab/chains returns all three chains
- POST /video-lab/chain-benchmarks creates and runs chain benchmark
- GET /video-lab/chain-benchmarks/{id} returns benchmark result
- Chain benchmark returns correct chain IDs
- Chain benchmark includes intermediate artifacts
- hyperframes_tts_video in benchmark is manual_required
"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ─────────────────────────────────────────
# 1. GET /chains returns all three chains
# ─────────────────────────────────────────
def test_list_chains_endpoint():
    """GET /video-lab/chains should return all three chains."""
    resp = client.get("/video-lab/chains")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    chains = resp.json()
    chain_ids = [c["chainId"] for c in chains]

    assert "local_frame_tts_video" in chain_ids
    assert "remotion_tts_video" in chain_ids
    assert "hyperframes_tts_video" in chain_ids


def test_list_chains_has_correct_metadata():
    """Each chain should have correct metadata fields."""
    resp = client.get("/video-lab/chains")
    assert resp.status_code == 200

    chains = resp.json()
    for chain in chains:
        assert "chainId" in chain
        assert "name" in chain
        assert "visualRoute" in chain
        assert "audioProvider" in chain
        assert "subtitleMode" in chain
        assert "generationMode" in chain
        assert "finalOutputRequired" in chain
        assert "requiresTts" in chain


# ─────────────────────────────────────────
# 2. POST /chain-benchmarks with unknown chain returns 400
# ─────────────────────────────────────────
def test_chain_benchmark_unknown_chain_returns_400():
    """POST /video-lab/chain-benchmarks with unknown chain ID should return 400."""
    resp = client.post("/video-lab/chain-benchmarks", json={
        "testCaseId": "case_ai_frontier_daily_001",
        "title": "Test benchmark",
        "inputPayload": {"content": "测试"},
        "commonParams": {"targetDuration": 45},
        "chainIds": ["unknown_chain"],
    })
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    assert "unknown_chain" in resp.json()["detail"]


# ─────────────────────────────────────────
# 3. POST /chain-benchmarks runs hyperframes_tts_video as manual_required
# ─────────────────────────────────────────
def test_chain_benchmark_hyperframes_is_manual_required():
    """hyperframes_tts_video in chain benchmark should be manual_required."""
    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        resp = client.post("/video-lab/chain-benchmarks", json={
            "testCaseId": "case_ai_frontier_daily_001",
            "title": "Test chain benchmark - hyperframes",
            "inputPayload": {"content": "测试内容用于生成HTML"},
            "commonParams": {"targetDuration": 45},
            "chainIds": ["hyperframes_tts_video"],
        })

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert "results" in data
    assert len(data["results"]) == 1
    result = data["results"][0]

    assert result["chainId"] == "hyperframes_tts_video"
    assert result["status"] == "manual_required", \
        f"Expected manual_required, got {result['status']}"
    assert result["htmlUrl"] != "", "Should have htmlUrl populated"
    assert result["finalVideoUrl"] == "", "Should NOT have finalVideoUrl"


# ─────────────────────────────────────────
# 4. Chain benchmark returns correct chain IDs in results
# ─────────────────────────────────────────
def test_chain_benchmark_returns_correct_chain_ids():
    """Chain benchmark results should contain the correct chain IDs."""
    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        resp = client.post("/video-lab/chain-benchmarks", json={
            "testCaseId": "case_ai_frontier_daily_001",
            "title": "Test chain benchmark",
            "inputPayload": {"content": "测试内容"},
            "commonParams": {"targetDuration": 45},
            "chainIds": ["local_frame_tts_video", "hyperframes_tts_video"],
        })

    assert resp.status_code == 200
    data = resp.json()

    result_ids = [r["chainId"] for r in data["results"]]
    assert "local_frame_tts_video" in result_ids
    assert "hyperframes_tts_video" in result_ids


# ─────────────────────────────────────────
# 5. local_frame_tts_video without API key fails at minimax_tts
# ─────────────────────────────────────────
def test_chain_benchmark_local_frame_no_api_key_fails():
    """local_frame_tts_video without API key should fail with failedStep=minimax_tts."""
    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        resp = client.post("/video-lab/chain-benchmarks", json={
            "testCaseId": "case_ai_frontier_daily_001",
            "title": "Test TTS chain no API",
            "inputPayload": {"content": "测试内容"},
            "commonParams": {"targetDuration": 45},
            "chainIds": ["local_frame_tts_video"],
        })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    result = data["results"][0]

    assert result["chainId"] == "local_frame_tts_video"
    assert result["status"] == "failed", f"Expected failed, got {result['status']}"
    assert result["failedStep"] == "minimax_tts", \
        f"Expected failedStep=minimax_tts, got {result.get('failedStep')}"


# ─────────────────────────────────────────
# 6. GET /chain-benchmarks/{id} returns stored benchmark
# ─────────────────────────────────────────
def test_get_chain_benchmark_returns_stored_benchmark():
    """GET /video-lab/chain-benchmarks/{id} should return the stored benchmark."""
    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        # Create benchmark
        create_resp = client.post("/video-lab/chain-benchmarks", json={
            "testCaseId": "case_ai_frontier_daily_001",
            "title": "Test get benchmark",
            "inputPayload": {"content": "测试"},
            "commonParams": {"targetDuration": 45},
            "chainIds": ["hyperframes_tts_video"],
        })

    assert create_resp.status_code == 200
    benchmark_id = create_resp.json()["benchmarkId"]

    # Retrieve benchmark
    get_resp = client.get(f"/video-lab/chain-benchmarks/{benchmark_id}")
    assert get_resp.status_code == 200, f"Expected 200, got {get_resp.status_code}"
    data = get_resp.json()
    assert data["benchmarkId"] == benchmark_id
    assert "results" in data


# ─────────────────────────────────────────
# 7. GET /chain-benchmarks/{id} returns 404 for unknown ID
# ─────────────────────────────────────────
def test_get_chain_benchmark_unknown_id_returns_404():
    """GET /video-lab/chain-benchmarks/unknown should return 404."""
    resp = client.get("/video-lab/chain-benchmarks/nonexistent_id")
    assert resp.status_code == 404


# ─────────────────────────────────────────
# 8. Chain benchmark response structure is correct
# ─────────────────────────────────────────
def test_chain_benchmark_response_structure():
    """Chain benchmark response should have correct top-level structure."""
    with patch.dict(os.environ, {"MINIMAX_API_KEY": ""}):
        resp = client.post("/video-lab/chain-benchmarks", json={
            "testCaseId": "case_ai_frontier_daily_001",
            "title": "Test structure",
            "inputPayload": {"content": "测试"},
            "commonParams": {"targetDuration": 45},
            "chainIds": ["hyperframes_tts_video"],
        })

    assert resp.status_code == 200
    data = resp.json()

    # Top-level fields
    assert "benchmarkId" in data
    assert "title" in data
    assert "testCaseId" in data
    assert "inputPayload" in data
    assert "commonParams" in data
    assert "chainIds" in data
    assert "status" in data
    assert "results" in data
    assert "createdAt" in data

    # Each result should have chain-level fields
    for result in data["results"]:
        assert "chainId" in result
        assert "chainName" in result
        assert "status" in result
        assert "finalVideoUrl" in result
        assert "htmlUrl" in result
        assert "hasVisual" in result
        assert "hasAudio" in result
        assert "hasReadableText" in result
        assert "audioUrl" in result
        assert "srtUrl" in result
        assert "failedStep" in result
        assert "failedReason" in result
        assert "visualSource" in result
        assert "audioSource" in result
        assert "subtitleMode" in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
