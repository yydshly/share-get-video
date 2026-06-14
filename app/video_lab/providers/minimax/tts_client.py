"""
MiniMax TTS Client
V0.3.3: Minimal MiniMax TTS client for AI news video voiceover

Reference: adapted from 20260508_个人感悟生成情绪mv/services/audio_service.py
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import requests


class MiniMaxTTSError(RuntimeError):
    """Raised when MiniMax TTS generation fails."""
    pass


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc)
    if "status_code" in msg and "1033" in msg:
        return True
    if isinstance(exc, requests.exceptions.Timeout):
        return True
    if isinstance(exc, requests.exceptions.ConnectionError):
        return True
    return False


class MiniMaxTTSClient:
    """
    Minimal MiniMax TTS client.

    Reads config from environment variables:
      MINIMAX_API_KEY      — required
      MINIMAX_TTS_MODEL    — default "speech-2.8-hd"
      MINIMAX_TTS_VOICE_ID — default "male-qn-qingse"
      MINIMAX_TTS_SPEED    — default 1.0
      MINIMAX_TTS_VOLUME   — default 1.0
      MINIMAX_TTS_PITCH    — default 0
      MINIMAX_TTS_BASE_URL — default "https://api.minimaxi.com"

    Usage:
        client = MiniMaxTTSClient()
        result = client.generate("今天有三个AI信号值得关注", output_path=Path("voiceover.mp3"))
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        voice_id: str | None = None,
        speed: float | None = None,
        volume: float | None = None,
        pitch: int | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.model = model or os.environ.get("MINIMAX_TTS_MODEL", "speech-2.8-hd")
        self.voice_id = voice_id or os.environ.get("MINIMAX_TTS_VOICE_ID", "male-qn-qingse")
        self.speed = speed if speed is not None else float(os.environ.get("MINIMAX_TTS_SPEED", "1.0"))
        self.volume = volume if volume is not None else float(os.environ.get("MINIMAX_TTS_VOLUME", "1.0"))
        self.pitch = pitch if pitch is not None else int(os.environ.get("MINIMAX_TTS_PITCH", "0"))
        self.base_url = base_url or os.environ.get("MINIMAX_TTS_BASE_URL", "https://api.minimaxi.com")

    def is_configured(self) -> bool:
        """Return True if API key is set."""
        return bool(self.api_key.strip())

    def generate(
        self,
        text: str,
        output_path: Path,
        voice_id: str | None = None,
        speed: float | None = None,
        volume: float | None = None,
        pitch: int | None = None,
        timeout: int = 180,
    ) -> dict:
        """
        Generate TTS audio for the given text.

        Args:
            text: Chinese text to convert to speech
            output_path: Where to save the MP3 file
            voice_id: Override default voice ID
            speed: Override default speed (1.0 = normal)
            volume: Override default volume (1.0 = normal)
            pitch: Override default pitch (0 = normal)
            timeout: Request timeout in seconds

        Returns:
            dict with keys: success, audioPath, audioUrl, durationSec, providerMessage
        """
        if not self.is_configured():
            return {
                "success": False,
                "audioPath": "",
                "audioUrl": "",
                "durationSec": 0,
                "providerMessage": "Missing MINIMAX_API_KEY environment variable",
            }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        vid = voice_id or self.voice_id
        spd = speed if speed is not None else self.speed
        vol = volume if volume is not None else self.volume
        ptc = pitch if pitch is not None else self.pitch

        url = f"{self.base_url.rstrip('/')}/v1/t2a_v2"
        payload = {
            "model": self.model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": vid,
                "speed": spd,
                "vol": vol,
                "pitch": ptc,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
            "subtitle_enable": False,
            "output_format": "hex",
            "aigc_watermark": False,
            "language_boost": "Chinese",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        max_retries = 2
        last_exc: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                if response.status_code >= 400:
                    return {
                        "success": False,
                        "audioPath": "",
                        "audioUrl": "",
                        "durationSec": 0,
                        "providerMessage": f"MiniMax TTS HTTP {response.status_code}: {response.text[:200]}",
                    }

                data = response.json()
                base_resp = data.get("base_resp", {})
                status_code = base_resp.get("status_code")
                if status_code not in (None, 0):
                    err_msg = f"MiniMax TTS status {status_code}: {data}"
                    return {
                        "success": False,
                        "audioPath": "",
                        "audioUrl": "",
                        "durationSec": 0,
                        "providerMessage": err_msg[:200],
                    }

                result_data = data.get("data") or {}
                audio_hex = result_data.get("audio")
                if not audio_hex:
                    return {
                        "success": False,
                        "audioPath": "",
                        "audioUrl": "",
                        "durationSec": 0,
                        "providerMessage": "MiniMax TTS response missing audio data",
                    }

                output_path.write_bytes(bytes.fromhex(audio_hex))
                duration = self._estimate_duration(len(audio_hex))
                return {
                    "success": True,
                    "audioPath": str(output_path),
                    "audioUrl": "",
                    "durationSec": duration,
                    "providerMessage": "Success",
                }

            except Exception as exc:
                last_exc = exc
                if attempt < max_retries and _is_retryable(exc):
                    time.sleep(2 ** attempt)
                    continue
                return {
                    "success": False,
                    "audioPath": "",
                    "audioUrl": "",
                    "durationSec": 0,
                    "providerMessage": f"MiniMax TTS request failed: {exc}",
                }

        return {
            "success": False,
            "audioPath": "",
            "audioUrl": "",
            "durationSec": 0,
            "providerMessage": f"MiniMax TTS failed after retries: {last_exc}",
        }

    @staticmethod
    def _estimate_duration(hex_length: int) -> float:
        """Rough estimate of audio duration from hex string length."""
        # ~32000 bitrate * 2 (hex encoding) / bytes per second
        bytes_count = hex_length // 2
        # At 128kbps = 16000 bytes/sec, with some overhead
        return max(1.0, bytes_count / 15000)
