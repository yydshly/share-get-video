"""
errors.py - Unified error structures for Video Lab.

Provides ErrorEnvelope and error_response() for all Video Lab entry points,
ensuring consistent error shape across clip-preview, visual-compose, and
technique-probe.

All errors returned to FastAPI callers are dicts (not exceptions) so they
compose cleanly with existing HTTPException returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────
# Stage identifiers
# ─────────────────────────────────────────
STAGE_UNKNOWN = "unknown"
STAGE_CONTENT_STRUCTURE = "content_structure"
STAGE_KEY_POINT_EXTRACT = "key_point_extract"
STAGE_VOICEOVER_PLAN = "voiceover_plan"
STAGE_TTS = "tts"
STAGE_SUBTITLE_PLAN = "subtitle_plan"
STAGE_VISUAL_RENDER = "visual_render"
STAGE_FFMPEG_COMPOSE = "ffmpeg_compose"
STAGE_MANIFEST_WRITE = "manifest_write"


# ─────────────────────────────────────────
# ErrorEnvelope
# ─────────────────────────────────────────
@dataclass
class ErrorEnvelope:
    """Structured error envelope used in all Video Lab failed responses."""

    type: str  # e.g. "RenderError", "TTSError", "ConfigError"
    code: str  # e.g. "VIDEO_LAB_RENDER_FAILED"
    message: str  # human-readable summary
    stage: str = STAGE_UNKNOWN
    route: str = "unknown"
    recoverable: bool = True
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "code": self.code,
            "message": self.message,
            "stage": self.stage,
            "route": self.route,
            "recoverable": self.recoverable,
            "details": self.details,
        }


# ─────────────────────────────────────────
# Factory helpers
# ─────────────────────────────────────────
def make_error(
    message: str,
    *,
    type: str = "UnknownError",
    code: str = "VIDEO_LAB_UNKNOWN_ERROR",
    stage: str = STAGE_UNKNOWN,
    route: str = "unknown",
    recoverable: bool = True,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a structured error dict (no Exception raised)."""
    return ErrorEnvelope(
        type=type,
        code=code,
        message=message,
        stage=stage,
        route=route,
        recoverable=recoverable,
        details=details or {},
    ).to_dict()


def error_response(
    *,
    message: str,
    type: str = "UnknownError",
    code: str = "VIDEO_LAB_UNKNOWN_ERROR",
    stage: str = STAGE_UNKNOWN,
    route: str = "unknown",
    recoverable: bool = True,
    details: dict[str, Any] | None = None,
    run_id: str = "",
    experiment_id: str = "",
    mode: str = "",
    artifacts: dict[str, Any] | None = None,
    logs: list[str] | None = None,
    warnings: list[str] | None = None,
    raw_output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a complete failed API response dict.

    This is the canonical shape returned by all Video Lab endpoints on failure.
    All arguments match the contract fields defined in V1.0.
    """
    return {
        "success": False,
        "status": "failed",
        "runId": run_id,
        "experimentId": experiment_id,
        "mode": mode,
        "routeId": route,
        "artifacts": artifacts or {},
        "logs": logs or [],
        "warnings": warnings or [],
        "error": make_error(
            message,
            type=type,
            code=code,
            stage=stage,
            route=route,
            recoverable=recoverable,
            details=details or {},
        ),
        "rawOutput": raw_output or {},
    }


# ─────────────────────────────────────────
# Common pre-built error factories
# ─────────────────────────────────────────
def render_error(message: str, route: str = "unknown", details: dict | None = None) -> dict:
    return error_response(
        message=message,
        type="RenderError",
        code="VIDEO_LAB_RENDER_FAILED",
        stage=STAGE_VISUAL_RENDER,
        route=route,
        recoverable=True,
        details=details,
    )


def tts_error(message: str, route: str = "unknown", details: dict | None = None) -> dict:
    return error_response(
        message=message,
        type="TTSError",
        code="VIDEO_LAB_TTS_FAILED",
        stage=STAGE_TTS,
        route=route,
        recoverable=True,
        details=details,
    )


def config_error(message: str, stage: str = STAGE_UNKNOWN) -> dict:
    return error_response(
        message=message,
        type="ConfigError",
        code="VIDEO_LAB_CONFIG_ERROR",
        stage=stage,
        recoverable=False,
    )


def ffmpeg_error(message: str, route: str = "unknown", details: dict | None = None) -> dict:
    return error_response(
        message=message,
        type="FFmpegError",
        code="VIDEO_LAB_FFMPEG_FAILED",
        stage=STAGE_FFMPEG_COMPOSE,
        route=route,
        recoverable=True,
        details=details,
    )


def api_key_error(service: str, stage: str = STAGE_UNKNOWN) -> dict:
    return error_response(
        message=f"{service} API key not configured or invalid",
        type="APIKeyError",
        code=f"VIDEO_LAB_{service.upper()}_KEY_MISSING",
        stage=stage,
        recoverable=False,
    )
