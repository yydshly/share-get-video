"""
Video Lab Services — extracted from router.py V1.0.2

Provides business-logic services that router.py delegates to.
Each service preserves existing API return structures unchanged.
"""

from app.video_lab.services.clip_preview_service import run_clip_preview_contract
from app.video_lab.services.visual_compose_service import (
    run_visual_compose_contract,
    run_visual_compose_endpoint,
)
from app.video_lab.services.style_family_service import run_style_family_compare, run_background_variant_matrix
from app.video_lab.services.probe_service import run_technique_probe_endpoint
from app.video_lab.services.style_sweep_service import run_style_sweep_endpoint
from app.video_lab.services.assets import extract_style_sample_assets

__all__ = [
    "run_clip_preview_contract",
    "run_visual_compose_contract",
    "run_visual_compose_endpoint",
    "run_style_family_compare",
    "run_technique_probe_endpoint",
    "run_style_sweep_endpoint",
    "extract_style_sample_assets",
]
