"""
Render Parameters - Parameterized template configuration for all visual routes
V0.3.7: Route-specific config — Pillow / Remotion / AI Asset each have own param set
"""

from dataclasses import dataclass, field
from typing import Any, Tuple


# Valid style presets
VALID_STYLE_PRESETS = {"ai_frontier_dark"}

# Valid highlight modes
VALID_HIGHLIGHT_MODES = {"auto", "numbers", "none"}

# Valid aspect ratios
VALID_ASPECT_RATIOS = {"9:16", "16:9", "1:1"}

# Valid motion intensity
VALID_MOTION_INTENSITIES = {"low", "medium", "high"}

# Valid cover styles
VALID_COVER_STYLES = {"editorial", "cinematic", "minimal"}

# Valid overview styles
VALID_OVERVIEW_STYLES = {"timeline", "grid", "clean"}

# Valid metric animations
VALID_METRIC_ANIMATIONS = {"countup_bar", "countup_number", "none"}

# Valid transition styles
VALID_TRANSITION_STYLES = {"slide_fade", "fade", "slide"}


@dataclass
class LocalFrameRenderParams:
    """Parameters for Pillow local_frame_compose template rendering.
    V0.3.7: Extended with route-specific appearance params."""

    # Style and appearance
    style_preset: str = "ai_frontier_dark"

    # Timing and duration
    target_duration: int = 45  # seconds, range 15-90

    # Layout
    aspect_ratio: str = "9:16"

    # Content control
    key_point_count: int = 6  # 1-10
    highlight_mode: str = "auto"  # auto / numbers / none

    # Transitions
    transition_enabled: bool = True
    transition_frames: int = 4  # 0-8

    # Content sections
    include_overview: bool = True
    include_summary: bool = True

    # V0.3.7: Route-specific appearance
    show_data_viz: bool = True
    title_color: str = "#f8fafc"
    body_color: str = "#94a3b8"
    highlight_color: str = "#f59e0b"
    content_align: str = "top"  # top / center
    theme_adaptive: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stylePreset": self.style_preset,
            "targetDuration": self.target_duration,
            "aspectRatio": self.aspect_ratio,
            "keyPointCount": self.key_point_count,
            "highlightMode": self.highlight_mode,
            "transitionEnabled": self.transition_enabled,
            "transitionFrames": self.transition_frames,
            "includeOverview": self.include_overview,
            "includeSummary": self.include_summary,
            "showDataViz": self.show_data_viz,
            "titleColor": self.title_color,
            "bodyColor": self.body_color,
            "highlightColor": self.highlight_color,
            "contentAlign": self.content_align,
            "themeAdaptive": self.theme_adaptive,
        }


@dataclass
class ParseResult:
    """Result of parameter parsing - either success or failure with error."""

    params: LocalFrameRenderParams | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.params is not None and self.error is None


def resolve_resolution(aspect_ratio: str) -> Tuple[int, int]:
    """
    Resolve aspect ratio string to (width, height) resolution tuple.

    Args:
        aspect_ratio: Aspect ratio string like "9:16", "16:9", "1:1"

    Returns:
        Tuple of (width, height) in pixels
    """
    if aspect_ratio == "9:16":
        return (1080, 1920)
    if aspect_ratio == "16:9":
        return (1920, 1080)
    if aspect_ratio == "1:1":
        return (1080, 1080)
    # Fallback to default
    return (1080, 1920)


def parse_local_frame_params(params: dict) -> ParseResult:
    """
    Parse and validate raw params dict into LocalFrameRenderParams.

    Applies defaults and fallbacks for missing/invalid values.
    Returns ParseResult with either valid params or error.

    Validation rules:
    - targetDuration: 15-90, default 45
    - keyPointCount: 1-10, default 6
    - transitionFrames: 0-8, default 4
    - highlightMode: auto/numbers/none, default auto
    - stylePreset: only ai_frontier_dark currently, default ai_frontier_dark
    - aspectRatio: 9:16/16:9/1:1, default 9:16, others emit warning

    Args:
        params: Raw parameter dictionary (camelCase keys)

    Returns:
        ParseResult with validated LocalFrameRenderParams or error
    """
    warnings = []

    if not params:
        # Return defaults for empty params
        return ParseResult(
            params=LocalFrameRenderParams(),
            warnings=["Empty params, using defaults"],
        )

    # --- targetDuration ---
    raw_target = params.get("targetDuration", 45)
    try:
        target_duration = int(raw_target)
    except (ValueError, TypeError):
        target_duration = 45
        warnings.append(f"Invalid targetDuration '{raw_target}', using 45")

    if target_duration < 15:
        target_duration = 15
        warnings.append("targetDuration below minimum 15, clamping to 15")
    elif target_duration > 90:
        target_duration = 90
        warnings.append("targetDuration above maximum 90, clamping to 90")

    # --- keyPointCount ---
    raw_kpc = params.get("keyPointCount", 6)
    try:
        key_point_count = int(raw_kpc)
    except (ValueError, TypeError):
        key_point_count = 6
        warnings.append(f"Invalid keyPointCount '{raw_kpc}', using 6")

    if key_point_count < 1:
        key_point_count = 1
        warnings.append("keyPointCount below minimum 1, clamping to 1")
    elif key_point_count > 10:
        key_point_count = 10
        warnings.append("keyPointCount above maximum 10, clamping to 10")

    # --- transitionFrames ---
    raw_tf = params.get("transitionFrames", 4)
    try:
        transition_frames = int(raw_tf)
    except (ValueError, TypeError):
        transition_frames = 4
        warnings.append(f"Invalid transitionFrames '{raw_tf}', using 4")

    if transition_frames < 0:
        transition_frames = 0
        warnings.append("transitionFrames below minimum 0, clamping to 0")
    elif transition_frames > 8:
        transition_frames = 8
        warnings.append("transitionFrames above maximum 8, clamping to 8")

    # --- highlightMode ---
    raw_highlight_mode = params.get("highlightMode", "auto")
    highlight_mode = raw_highlight_mode
    if highlight_mode not in VALID_HIGHLIGHT_MODES:
        warnings.append(f"Invalid highlightMode '{raw_highlight_mode}', using 'auto'")
        highlight_mode = "auto"

    # --- stylePreset ---
    raw_style_preset = params.get("stylePreset", "ai_frontier_dark")
    style_preset = raw_style_preset
    if style_preset not in VALID_STYLE_PRESETS:
        warnings.append(f"Invalid stylePreset '{raw_style_preset}', using 'ai_frontier_dark'")
        style_preset = "ai_frontier_dark"

    # --- aspectRatio ---
    aspect_ratio = params.get("aspectRatio", "9:16")
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        warnings.append(f"Non-standard aspectRatio '{aspect_ratio}', using as-is")

    # --- transitionEnabled ---
    transition_enabled = params.get("transitionEnabled", True)
    if not isinstance(transition_enabled, bool):
        # Handle string "true"/"false" or numeric
        if isinstance(transition_enabled, str):
            transition_enabled = transition_enabled.lower() in ("true", "1", "yes")
        else:
            transition_enabled = bool(transition_enabled)

    # If transition_frames is 0, treat as disabled
    if transition_frames == 0:
        transition_enabled = False

    # --- includeOverview ---
    include_overview = params.get("includeOverview", True)
    if not isinstance(include_overview, bool):
        if isinstance(include_overview, str):
            include_overview = include_overview.lower() in ("true", "1", "yes")
        else:
            include_overview = bool(include_overview)

    # --- includeSummary ---
    include_summary = params.get("includeSummary", True)
    if not isinstance(include_summary, bool):
        if isinstance(include_summary, str):
            include_summary = include_summary.lower() in ("true", "1", "yes")
        else:
            include_summary = bool(include_summary)

    # V0.3.7: Parse route-specific appearance params (all routes share same parser)
    show_data_viz = params.get("showDataViz", True) not in (False, "false", "False", 0)
    title_color = params.get("titleColor", "#f8fafc") or "#f8fafc"
    body_color = params.get("bodyColor", "#94a3b8") or "#94a3b8"
    highlight_color = params.get("highlightColor", "#f59e0b") or "#f59e0b"
    content_align = params.get("contentAlign", "top")
    if content_align not in ("top", "center"):
        content_align = "top"
    theme_adaptive = params.get("themeAdaptive", True) not in (False, "false", "False", 0)

    # V0.3.7: Remotion-specific params (read directly by props_builder)
    # accentColor, fontScale, showIcon, motionIntensity, coverStyle,
    # overviewStyle, metricAnimation, transitionStyle
    # No validation needed here; props_builder reads raw values with defaults.

    # V0.3.7: AI Asset-specific params
    # imageStyle, backgroundDarken, cardOpacity, cardBlur, kenBurns
    # No validation needed here; ai_asset_renderer reads raw values with defaults.

    return ParseResult(
        params=LocalFrameRenderParams(
            style_preset=style_preset,
            target_duration=target_duration,
            aspect_ratio=aspect_ratio,
            key_point_count=key_point_count,
            highlight_mode=highlight_mode,
            transition_enabled=transition_enabled,
            transition_frames=transition_frames,
            include_overview=include_overview,
            include_summary=include_summary,
            show_data_viz=show_data_viz,
            title_color=title_color,
            body_color=body_color,
            highlight_color=highlight_color,
            content_align=content_align,
            theme_adaptive=theme_adaptive,
        ),
        warnings=warnings,
    )
