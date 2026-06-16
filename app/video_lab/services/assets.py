"""
Asset extraction helpers — extracted from router.py V1.0.2.

extract_style_sample_assets() and supporting utilities.
"""

from typing import Any

from app.video_lab.config import PUBLIC_RUNTIME_URL_PREFIX


def _safe_get(obj, name: str, default=None):
    """Access attribute or dict key, handling None gracefully."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _artifact_type_value(artifact) -> str:
    """Normalize artifact type: enum.value or string."""
    raw = _safe_get(artifact, "type", "")
    return getattr(raw, "value", raw) or ""


def _strip_runtime_url_prefix(url: str) -> str:
    """
    Strip the PUBLIC_RUNTIME_URL_PREFIX from a URL to get the stored path.

    Examples:
      "/runtime/video_lab/x.mp4" → "video_lab/x.mp4"
      "/assets/video_lab/x.mp4"  → "video_lab/x.mp4"
      ""                        → ""
    """
    if not url:
        return ""
    prefix = PUBLIC_RUNTIME_URL_PREFIX.rstrip("/")
    if prefix and url.startswith(prefix + "/"):
        return url[len(prefix) + 1:]
    if url.startswith("/runtime/"):
        return url[len("/runtime/"):]
    return url.lstrip("/")


def extract_style_sample_assets(result) -> dict[str, str]:
    """
    Extract URL assets from a VideoExperimentResult (or any object/dict with
    the same field layout).

    Returns dict with keys: final_video_url, cover_url, audio_url, srt_url,
    manifest_url, duration_sec, audio_duration_sec, failed, failed_reason.
    """
    raw = _safe_get(result, "rawOutput", {}) or {}
    assets = _safe_get(result, "assets", {}) or {}

    final_video_url = _safe_get(result, "videoUrl", "") or ""
    cover_url = _safe_get(result, "coverUrl", "") or ""
    audio_url = ""
    srt_url = ""
    manifest_url = ""

    duration_sec = float(assets.get("durationSec", 0) or 0)
    audio_duration_sec = float(assets.get("audioDurationSec", 0) or 0)

    steps = _safe_get(result, "productionSteps", []) or []

    for step in steps:
        artifacts = _safe_get(step, "artifacts", []) or []
        for art in artifacts:
            atype = _artifact_type_value(art)
            payload = _safe_get(art, "payload", {}) or {}
            url = _safe_get(payload, "url", "") if isinstance(payload, dict) else ""
            if not url:
                continue

            if atype == "video_output" and not final_video_url:
                final_video_url = url
            elif atype == "cover_image" and not cover_url:
                cover_url = url
            elif atype == "audio_output" and not audio_url:
                audio_url = url
            elif atype == "subtitle_file" and not srt_url:
                srt_url = url
            elif atype == "manifest" and not manifest_url:
                manifest_url = url

    status_ok = raw.get("status") == "succeeded"
    failed = not status_ok

    if status_ok and not final_video_url:
        failed = True
        failed_reason = raw.get("error") or "生成成功但无法提取 final_video_url，请检查 productionSteps 中 video_output artifact"
    else:
        failed_reason = raw.get("error") or ("生成失败" if failed else "")

    return {
        "final_video_url": final_video_url,
        "cover_url": cover_url,
        "audio_url": audio_url,
        "srt_url": srt_url,
        "manifest_url": manifest_url,
        "duration_sec": duration_sec,
        "audio_duration_sec": audio_duration_sec,
        "failed": failed,
        "failed_reason": failed_reason,
    }
