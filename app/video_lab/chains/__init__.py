"""
Video Chain - V0.3.4.1
Complete video generation chain definitions.
"""

import json
from pathlib import Path
from typing import Any

from app.video_lab.chains.models import ChainDefinition, ChainStatus, ChainResult
from app.video_lab.chains.registry import (
    get_chain,
    list_chains,
    run_chain,
)
from app.video_lab.renderers.file_store import get_experiment_dir, path_to_url

__all__ = [
    "ChainDefinition",
    "ChainStatus",
    "ChainResult",
    "get_chain",
    "list_chains",
    "run_chain",
    "write_chain_manifest",
]


def write_chain_manifest(
    experiment_id: str,
    chain_id: str,
    status: str,
    final_video_url: str = "",
    silent_video_url: str = "",
    audio_url: str = "",
    srt_url: str = "",
    subtitle_burned: bool = True,
    audio_duration_sec: float = 0,
    visual_duration_sec: float = 0,
    extra: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Write a chain_manifest.json to the experiment directory.

    Returns (manifest_url, manifest_path).
    """
    manifest = {
        "chainId": chain_id,
        "status": status,
        "finalVideoUrl": final_video_url,
        "silentVideoUrl": silent_video_url,
        "audioUrl": audio_url,
        "srtUrl": srt_url,
        "hasVisual": bool(final_video_url or silent_video_url),
        "hasAudio": bool(audio_url),
        "hasReadableText": bool(srt_url),
        "subtitleBurned": subtitle_burned,
        "audioDurationSec": audio_duration_sec,
        "visualDurationSec": visual_duration_sec,
        "finalDurationPolicy": "audio_preserved" if audio_duration_sec else "visual_preserved",
    }
    if extra:
        manifest.update(extra)

    exp_dir = get_experiment_dir(experiment_id)
    manifest_path = exp_dir / "chain_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    manifest_url = path_to_url(manifest_path)
    return manifest_url, str(manifest_path)
