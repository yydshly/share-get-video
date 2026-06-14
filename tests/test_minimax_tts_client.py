"""
Tests for V0.3.3 MiniMax TTS Client
- MiniMaxTTSClient.is_configured() returns False when no API key
- generate() returns failed result without API key
- generate() returns failed result with bad API key (mock)
- No external network calls in tests
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.providers.minimax import MiniMaxTTSClient, MiniMaxTTSError


def test_client_not_configured_without_api_key():
    """Client should report not configured when no API key."""
    client = MiniMaxTTSClient(api_key="")
    assert client.is_configured() is False


def test_client_configured_with_api_key():
    """Client should report configured when API key is set."""
    client = MiniMaxTTSClient(api_key="test-key-123")
    assert client.is_configured() is True


def test_generate_returns_failed_without_api_key():
    """generate() should return failed result when no API key is set."""
    client = MiniMaxTTSClient(api_key="")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = client.generate("测试文字", output_path=Path(tmpdir) / "out.mp3")

    assert result["success"] is False
    assert result["audioPath"] == ""
    assert "MINIMAX_API_KEY" in result["providerMessage"]


def test_generate_does_not_call_network_without_api_key():
    """generate() should not make network requests when no API key."""
    client = MiniMaxTTSClient(api_key="")
    with patch("app.video_lab.providers.minimax.tts_client.requests.post") as mock_post:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.generate("测试文字", output_path=Path(tmpdir) / "out.mp3")
        mock_post.assert_not_called()


def test_generate_with_mock_response_failure():
    """generate() should return failed result on HTTP error."""
    client = MiniMaxTTSClient(api_key="fake-key")

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch("app.video_lab.providers.minimax.tts_client.requests.post", return_value=mock_response):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.generate("测试文字", output_path=Path(tmpdir) / "out.mp3")

    assert result["success"] is False
    assert "401" in result["providerMessage"]


def test_generate_with_mock_success_response():
    """generate() should call MiniMax API and parse response correctly."""
    client = MiniMaxTTSClient(api_key="fake-key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "base_resp": {"status_code": 0},
        "data": {
            "audio": "68656c6c6f20776f726c64"  # "hello world" in hex
        }
    }

    with patch("app.video_lab.providers.minimax.tts_client.requests.post", return_value=mock_response) as mock_post:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "voiceover.mp3"
            result = client.generate("测试文字", output_path=out_path)

    assert result["success"] is True
    assert result["audioPath"] != ""
    assert result["durationSec"] > 0
    # Verify the API was called with correct payload
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    payload = call_kwargs["json"]
    assert payload["model"] == "speech-2.8-hd"
    assert payload["text"] == "测试文字"
    assert payload["voice_setting"]["voice_id"] == "male-qn-qingse"


def test_generate_uses_environment_variables():
    """Client should read model/voice_id from environment variables."""
    with patch.dict(os.environ, {
        "MINIMAX_API_KEY": "test-key",
        "MINIMAX_TTS_MODEL": "speech-2-turbo",
        "MINIMAX_TTS_VOICE_ID": "female-qn-jingjing",
        "MINIMAX_TTS_SPEED": "1.2",
        "MINIMAX_TTS_BASE_URL": "https://custom.api.com",
    }):
        client = MiniMaxTTSClient()
        assert client.api_key == "test-key"
        assert client.model == "speech-2-turbo"
        assert client.voice_id == "female-qn-jingjing"
        assert client.speed == 1.2
        assert client.base_url == "https://custom.api.com"


def test_generate_respects_overrides():
    """generate() should respect per-call parameter overrides."""
    client = MiniMaxTTSClient(api_key="test-key", voice_id="default-voice")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "base_resp": {"status_code": 0},
        "data": {"audio": "MTIz"}
    }

    with patch("app.video_lab.providers.minimax.tts_client.requests.post", return_value=mock_response) as mock_post:
        with tempfile.TemporaryDirectory() as tmpdir:
            client.generate(
                "测试",
                output_path=Path(tmpdir) / "out.mp3",
                voice_id="custom-voice",
                speed=0.8,
            )

        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["voice_setting"]["voice_id"] == "custom-voice"
        assert payload["voice_setting"]["speed"] == 0.8


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
