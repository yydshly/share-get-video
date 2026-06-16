"""
Style Sweep Service — extracted from router.py V1.0.2.

Provides run_style_sweep_endpoint() which calls the existing style_sweep module.
"""

from typing import Any

from app.video_lab.style_sweep import run_style_sweep


def run_style_sweep_endpoint(
    request,
    render_fn,
) -> dict[str, Any]:
    """
    Style comparison: select one technical route → render each preset style
    of that route with the same content → return side-by-side results.

    Synchronous: each style runs the full pipeline (TTS/render/compose), N styles ≈ N× time.
    A single style failure does not interrupt other styles; the full batch is still returned.

    Calls the existing style_sweep module — this service only wires the render callback.

    Args:
        request: StyleSweepRequest object
        render_fn: _run_visual_compose wrapper (passed in by router for compatibility)

    Returns:
        Style sweep result dict from run_style_sweep().
    """
    return run_style_sweep(
        content=request.content,
        route_id=request.routeId,
        params=request.params,
        render_fn=render_fn,
    )
