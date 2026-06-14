"""
MiniMax Image Generation Client
文生图：为视频生成背景/配图素材（AI 负责素材，代码负责叠字）。

复用 MINIMAX_API_KEY，与 TTS/LLM 同一套凭证。
Endpoint: POST {base}/v1/image_generation  (model image-01)
"""

from __future__ import annotations

import os
from pathlib import Path

import requests


class MiniMaxImageClient:
    """Minimal MiniMax text-to-image client."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.model = model or os.environ.get("MINIMAX_IMAGE_MODEL", "image-01")
        self.base_url = base_url or os.environ.get(
            "MINIMAX_IMAGE_BASE_URL",
            os.environ.get("MINIMAX_TTS_BASE_URL", "https://api.minimaxi.com"),
        )

    def is_configured(self) -> bool:
        return bool(self.api_key.strip())

    def generate(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        timeout: int = 120,
    ) -> dict:
        """
        Generate one image for the prompt and download to output_path.

        Returns dict: {success, imagePath, providerMessage}
        """
        if not self.is_configured():
            return {"success": False, "imagePath": "", "providerMessage": "Missing MINIMAX_API_KEY"}

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        url = f"{self.base_url.rstrip('/')}/v1/image_generation"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "n": 1,
            "response_format": "url",
            "prompt_optimizer": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code >= 400:
                return {"success": False, "imagePath": "", "providerMessage": f"HTTP {resp.status_code}: {resp.text[:200]}"}
            data = resp.json()
            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code") not in (None, 0):
                return {"success": False, "imagePath": "", "providerMessage": f"status {base_resp.get('status_code')}: {base_resp.get('status_msg','')}"}
            urls = (data.get("data") or {}).get("image_urls") or []
            if not urls:
                return {"success": False, "imagePath": "", "providerMessage": "no image_urls in response"}
            img_resp = requests.get(urls[0], timeout=timeout)
            if img_resp.status_code >= 400:
                return {"success": False, "imagePath": "", "providerMessage": f"download HTTP {img_resp.status_code}"}
            output_path.write_bytes(img_resp.content)
            return {"success": True, "imagePath": str(output_path), "providerMessage": "Success"}
        except Exception as exc:
            return {"success": False, "imagePath": "", "providerMessage": f"request failed: {exc}"}
