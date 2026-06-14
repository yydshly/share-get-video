"""
Chain - Data Models
V0.3.4.1: Complete video generation chain definitions
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChainStatus(str, Enum):
    """Status of a chain execution."""
    SUCCEEDED = "succeeded"       # Final MP4 generated with video and audio
    FAILED = "failed"             # Automatic chain failed
    MANUAL_REQUIRED = "manual_required"  # Needs manual step for final MP4
    INCOMPLETE = "incomplete"     # Has intermediate artifacts but no final MP4
    SKIPPED = "skipped"           # User did not select


@dataclass
class ChainDefinition:
    """Definition of a complete video generation chain."""
    chain_id: str
    name: str
    visual_route: str           # e.g. "local_frame_compose", "template_programmatic_render"
    audio_provider: str          # e.g. "minimax_tts", "none"
    subtitle_mode: str            # e.g. "srt", "none"
    generation_mode: str         # "auto" | "manual" | "semi_auto"
    final_output_required: bool  # Must produce final MP4 to be succeeded
    requires_tts: bool           # Uses MiniMax TTS (incurs API cost)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chainId": self.chain_id,
            "name": self.name,
            "visualRoute": self.visual_route,
            "audioProvider": self.audio_provider,
            "subtitleMode": self.subtitle_mode,
            "generationMode": self.generation_mode,
            "finalOutputRequired": self.final_output_required,
            "requiresTts": self.requires_tts,
        }


@dataclass
class ChainResult:
    """Result from a chain execution."""
    chain_id: str
    status: ChainStatus
    final_video_url: str = ""
    html_url: str = ""
    has_visual: bool = False
    has_audio: bool = False
    has_readable_text: bool = False
    # Intermediate artifacts (for debugging/display)
    audio_url: str = ""
    srt_url: str = ""
    manifest_url: str = ""
    # Failure info
    failed_step: str = ""
    failed_reason: str = ""
    # Chain metadata
    chain_name: str = ""
    visual_source: str = ""
    audio_source: str = ""
    subtitle_mode: str = ""
    # Execution info
    logs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chainId": self.chain_id,
            "chainName": self.chain_name,
            "status": self.status.value,
            "finalVideoUrl": self.final_video_url,
            "htmlUrl": self.html_url,
            "hasVisual": self.has_visual,
            "hasAudio": self.has_audio,
            "hasReadableText": self.has_readable_text,
            "audioUrl": self.audio_url,
            "srtUrl": self.srt_url,
            "manifestUrl": self.manifest_url,
            "failedStep": self.failed_step,
            "failedReason": self.failed_reason,
            "visualSource": self.visual_source,
            "audioSource": self.audio_source,
            "subtitleMode": self.subtitle_mode,
            "logs": self.logs,
            "warnings": self.warnings,
            "elapsedMs": self.elapsed_ms,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
