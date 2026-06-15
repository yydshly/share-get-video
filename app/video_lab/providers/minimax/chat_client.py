"""
MiniMax Chat (LLM) Client
用于内容规划：把原始报告处理成"适合视频展示"的结构。

复用 MINIMAX_API_KEY，与 TTS 同一套凭证。
Endpoint: POST {base}/v1/text/chatcompletion_v2
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import requests


class MiniMaxChatClient:
    """Minimal MiniMax LLM chat client (OpenAI-compatible style)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.model = model or os.environ.get("MINIMAX_LLM_MODEL", "MiniMax-Text-01")
        self.base_url = base_url or os.environ.get(
            "MINIMAX_LLM_BASE_URL",
            os.environ.get("MINIMAX_TTS_BASE_URL", "https://api.minimaxi.com"),
        )

    def is_configured(self) -> bool:
        return bool(self.api_key.strip())

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 120,
    ) -> dict:
        """
        Call chat completion.

        Returns dict: {success, content, providerMessage}
        """
        if not self.is_configured():
            return {"success": False, "content": "", "providerMessage": "Missing MINIMAX_API_KEY"}

        url = f"{self.base_url.rstrip('/')}/v1/text/chatcompletion_v2"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code >= 400:
                return {"success": False, "content": "", "providerMessage": f"HTTP {resp.status_code}: {resp.text[:200]}"}
            data = resp.json()
            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code") not in (None, 0):
                return {"success": False, "content": "", "providerMessage": f"status {base_resp.get('status_code')}: {base_resp.get('status_msg','')}"}
            choices = data.get("choices") or []
            if not choices:
                return {"success": False, "content": "", "providerMessage": "no choices in response"}
            content = choices[0].get("message", {}).get("content", "")
            return {"success": True, "content": content, "providerMessage": "Success"}
        except Exception as exc:
            return {"success": False, "content": "", "providerMessage": f"request failed: {exc}"}

    def chat_vision(
        self,
        text: str,
        image_paths: list[str],
        temperature: float = 0.2,
        max_tokens: int = 1500,
        timeout: int = 90,
    ) -> dict:
        """图像理解：文本 + 一张或多张本地图片 → 模型回复。MiniMax-Text-01 支持多模态。"""
        content: list[dict] = [{"type": "text", "text": text}]
        for p in image_paths:
            try:
                raw = Path(p).read_bytes()
            except Exception as e:
                return {"success": False, "content": "", "providerMessage": f"read image failed: {e}"}
            b64 = "data:image/png;base64," + base64.b64encode(raw).decode()
            content.append({"type": "image_url", "image_url": {"url": b64}})
        return self.chat(
            [{"role": "user", "content": content}],
            temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        )

    def chat_vision_json(self, text: str, image_paths: list[str], **kwargs) -> dict:
        """图像理解并解析为 JSON。"""
        result = self.chat_vision(text, image_paths, **kwargs)
        if not result["success"]:
            return result
        parsed = _extract_json(result["content"].strip())
        if parsed is None:
            return {"success": False, "content": result["content"], "providerMessage": "failed to parse JSON"}
        return {"success": True, "content": result["content"], "json": parsed, "providerMessage": "Success"}

    def chat_json(self, messages: list[dict], **kwargs) -> dict:
        """Call chat and parse the response as JSON (tolerant to ```json fences)."""
        result = self.chat(messages, **kwargs)
        if not result["success"]:
            return result
        text = result["content"].strip()
        parsed = _extract_json(text)
        if parsed is None:
            return {"success": False, "content": text, "providerMessage": "failed to parse JSON from response"}
        return {"success": True, "content": text, "json": parsed, "providerMessage": "Success"}


def _extract_json(text: str):
    """Extract a JSON object from text that may contain ```json fences or prose."""
    if not text:
        return None
    # strip code fences
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)
        t = t[1] if len(t) > 1 else text
        if t.startswith("json"):
            t = t[4:]
    t = t.strip()
    # try direct
    try:
        return json.loads(t)
    except Exception:
        pass
    # try to locate the outermost { ... }
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except Exception:
            return None
    return None
