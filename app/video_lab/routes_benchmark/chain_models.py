"""
Chain Benchmark - Data models for multi-chain benchmarking
V0.3.4.1: Complete video generation chain benchmarking
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ChainMetrics:
    """Metrics for a single chain result."""
    generation_time_ms: int = 0
    estimated_cost: str = "unknown"
    stability: str = "unknown"
    quality_ceiling: str = "unknown"


@dataclass
class ChainResultData:
    """Result from a single chain execution (mirrors ChainResult.to_dict)."""
    chain_id: str = ""
    chain_name: str = ""
    status: str = ""  # succeeded | failed | manual_required | incomplete | skipped
    final_video_url: str = ""
    html_url: str = ""
    has_visual: bool = False
    has_audio: bool = False
    has_readable_text: bool = False
    audio_url: str = ""
    srt_url: str = ""
    manifest_url: str = ""
    failed_step: str = ""
    failed_reason: str = ""
    visual_source: str = ""
    audio_source: str = ""
    subtitle_mode: str = ""
    logs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: int = 0
    created_at: str = ""

    @classmethod
    def from_chain_result(cls, result) -> "ChainResultData":
        d = result.to_dict()
        return cls(
            chain_id=d["chainId"],
            chain_name=d.get("chainName", ""),
            status=d["status"],
            final_video_url=d.get("finalVideoUrl", ""),
            html_url=d.get("htmlUrl", ""),
            has_visual=d.get("hasVisual", False),
            has_audio=d.get("hasAudio", False),
            has_readable_text=d.get("hasReadableText", False),
            audio_url=d.get("audioUrl", ""),
            srt_url=d.get("srtUrl", ""),
            manifest_url=d.get("manifestUrl", ""),
            failed_step=d.get("failedStep", ""),
            failed_reason=d.get("failedReason", ""),
            visual_source=d.get("visualSource", ""),
            audio_source=d.get("audioSource", ""),
            subtitle_mode=d.get("subtitleMode", ""),
            logs=d.get("logs", []),
            warnings=d.get("warnings", []),
            raw_output=d.get("rawOutput", {}),
            elapsed_ms=d.get("elapsedMs", 0),
            created_at=d.get("createdAt", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to camelCase dict for JSON serialization."""
        return {
            "chainId": self.chain_id,
            "chainName": self.chain_name,
            "status": self.status,
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
            "rawOutput": self.raw_output,
            "elapsedMs": self.elapsed_ms,
            "createdAt": self.created_at,
        }


@dataclass
class ChainBenchmark:
    """A benchmark run across multiple chains."""
    benchmark_id: str
    title: str
    test_case_id: str
    input_payload: dict[str, Any]
    common_params: dict[str, Any]
    chain_ids: list[str]
    status: str = "pending"  # "pending" | "running" | "completed" | "partial"
    results: list[ChainResultData] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    elapsed_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmarkId": self.benchmark_id,
            "title": self.title,
            "testCaseId": self.test_case_id,
            "inputPayload": self.input_payload,
            "commonParams": self.common_params,
            "chainIds": self.chain_ids,
            "status": self.status,
            "results": [r.to_dict() for r in self.results],
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "elapsedMs": self.elapsed_ms,
        }
