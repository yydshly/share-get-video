"""
Technique Probe Service — extracted from router.py V1.0.2.

Provides run_technique_probe_endpoint() which calls the existing technique_probe module
and provides _judge_probe_result() / _extract_video_frame() helpers.
"""

import logging
import subprocess
import uuid
from pathlib import Path
from typing import Any

from app.video_lab.config import ffmpeg_bin, ffprobe_bin
from app.video_lab.path_contract import runtime_url_to_path
from app.video_lab.quality.visual_judge import assess_visual_quality

logger = logging.getLogger(__name__)


def _extract_video_frame(video_path: str, fraction: float = 0.4) -> str | None:
    """
    Extract one frame from a video at the given fraction position.

    assess_visual_quality works with images/frames, not mp4 directly.
    Returns path to the extracted PNG frame, or None on failure.
    """
    vp = Path(video_path)
    if not vp.exists():
        return None
    # Get duration
    at_sec = 1.5
    try:
        probe = subprocess.run(
            [ffprobe_bin(), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", vp.as_posix()],
            capture_output=True, text=True, timeout=20,
        )
        dur = float((probe.stdout or "0").strip() or 0)
        if dur > 0:
            at_sec = max(0.0, dur * fraction)
    except Exception:
        pass
    out = vp.parent / f"_judge_frame_{uuid.uuid4().hex[:6]}.png"
    try:
        subprocess.run(
            [ffmpeg_bin(), "-y", "-ss", f"{at_sec:.2f}", "-i", vp.as_posix(),
             "-vframes", "1", out.as_posix()],
            capture_output=True, timeout=60,
        )
    except Exception:
        return None
    return str(out) if out.exists() else None


def _judge_probe_result(result: dict[str, Any]) -> dict[str, Any] | None:
    """
    Judge a single route's output for technique probe ranking.

    Extracts a frame from mp4 (or uses cover image) and runs visual quality assessment.
    Any failure returns None (route degrades to structural-score-only ranking, no interruption).
    """
    url = result.get("finalVideoUrl") or result.get("coverUrl") or ""
    if not url:
        return None
    # Use runtime_url_to_path for proper URL → local path conversion
    fs_path = runtime_url_to_path(url)

    if str(fs_path).endswith(".mp4"):
        # Multi-frame judging: cover / middle / end — gives visual model more discrimination signal
        frames = [f for f in (_extract_video_frame(str(fs_path), fr) for fr in (0.06, 0.45, 0.85)) if f]
    else:
        frames = [str(fs_path)]
    if not frames:
        return None
    j = assess_visual_quality(frames)
    if not j.get("success"):
        return None
    return {"visualScore": j.get("overall"), "visualDimensions": j.get("scores", {})}


def run_technique_probe_endpoint(
    request,
    compose_fn,
    judge_fn,
) -> dict[str, Any]:
    """
    Best technique probe: one content → all routes produce full video → unified quality ranking → recommended route.

    Synchronous: runs each route's full pipeline in sequence (TTS/render/compose may take minutes).
    A single route failure does not interrupt other routes; the overall ranking is still returned
    (failed routes are placed at the bottom).

    Calls the existing technique_probe module — this service only wires the compose/judge callbacks.

    Args:
        request: TechniqueProbeRequest object
        compose_fn: _run_visual_compose wrapper (passed in by router for compatibility)
        judge_fn: _judge_probe_result

    Returns:
        Probe result dict from run_technique_probe().
    """
    from app.video_lab.technique_probe import run_technique_probe

    return run_technique_probe(
        content=request.content,
        routes=request.routes or None,
        params=request.params,
        compose_fn=compose_fn,
        judge_fn=judge_fn,
    )
