"""
Voiceover Planner - 旁白计划生成器
V0.3.3: Generate voiceover script from structured content + key points

Does NOT call LLM — uses template-based generation for speed.
"""

from typing import Any


def generate_voiceover(
    structured: dict[str, Any],
    key_points: dict[str, Any],
    target_duration_sec: int = 45,
) -> dict[str, Any]:
    """
    Generate a voiceover script from structured content and key points.

    Args:
        structured: structured content with lead + items
        key_points: extracted key points with title/body/source
        target_duration_sec: target total audio duration

    Returns:
        {
            "voiceoverText": "...",
            "segments": [
                {
                    "index": 1,
                    "text": "...",
                    "startSec": 0,
                    "durationSec": 5
                }
            ],
            "estimatedDurationSec": 45
        }
    """
    lead = structured.get("lead", "").strip()
    if not lead:
        lead = "今天为大家带来AI领域的前沿动态。"

    kps_list = key_points.get("keyPoints", key_points.get("key_points", []))
    if not kps_list:
        # Fallback: use lead only
        segments = _make_segments_from_text([lead], target_duration_sec)
        return {
            "voiceoverText": lead,
            "segments": segments,
            "estimatedDurationSec": _total_duration(segments),
        }

    # Build opening from lead
    opening = _make_opening(lead)

    # Build body from key points
    body_parts: list[str] = []
    for i, kp in enumerate(kps_list, start=1):
        if isinstance(kp, dict):
            title = kp.get("title", "").strip()
            body = kp.get("body", "").strip()
            if title:
                sentence = _make_sentence(i, title, body)
                body_parts.append(sentence)
        elif isinstance(kp, str) and kp.strip():
            body_parts.append(f"第{i}点：{kp.strip()}。")

    # Build closing
    closing = "以上就是今天的主要内容，感谢观看。"

    all_parts = [opening] + body_parts + [closing]
    full_text = " ".join(filter(None, all_parts))

    # Distribute segments across key points + intro/outro
    num_segments = len(kps_list) + 2  # intro + kps + outro
    segment_duration = max(4, min(8, target_duration_sec / num_segments))
    segments = _distribute_segments(all_parts, segment_duration)

    return {
        "voiceoverText": full_text,
        "segments": segments,
        "estimatedDurationSec": _total_duration(segments),
    }


def _make_opening(lead: str) -> str:
    """Create opening sentence from lead."""
    if not lead:
        return "大家好，今天为大家带来AI领域的重要资讯。"
    # Trim to reasonable length for opening
    if len(lead) > 60:
        lead = lead[:60] + "..."
    return lead


def _make_sentence(index: int, title: str, body: str) -> str:
    """Create a natural sentence from a key point."""
    if body and len(body) > 10:
        # Use title + abbreviated body
        body_short = body[:40] + "..." if len(body) > 40 else body
        return f"第{index}点，{title}，{body_short}"
    return f"第{index}点，{title}。"


def _make_segments_from_text(parts: list[str], target_duration: int) -> list[dict]:
    """Distribute text parts into segments with approximate timing."""
    n = len(parts)
    duration = max(3, target_duration / max(1, n))
    segments = []
    current = 0.0
    for i, text in enumerate(parts, start=1):
        segments.append({
            "index": i,
            "text": text,
            "startSec": round(current, 1),
            "durationSec": round(duration, 1),
        })
        current += duration
    return segments


def _distribute_segments(parts: list[str], base_duration: float) -> list[dict]:
    """Distribute text parts into timed segments."""
    segments = []
    current = 0.0
    for i, text in enumerate(parts, start=1):
        # Longer text gets more time
        char_count = len(text)
        duration = max(3.0, min(10.0, base_duration * (char_count / 30)))
        segments.append({
            "index": i,
            "text": text,
            "startSec": round(current, 1),
            "durationSec": round(duration, 1),
        })
        current += duration
    return segments


def _total_duration(segments: list[dict]) -> int:
    """Calculate total duration from segments."""
    if not segments:
        return 0
    last = segments[-1]
    return int(round(last["startSec"] + last["durationSec"]))
