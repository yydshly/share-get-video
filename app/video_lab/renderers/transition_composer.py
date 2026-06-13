"""
Transition Composer - Fade transitions between frames using Pillow
Generates intermediate frames for smooth visual transitions.
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from PIL import Image

from app.video_lab.renderers.visual_theme import (
    TRANSITION_FRAMES_DEFAULT,
    TRANSITION_TYPE,
    TEMPLATE_VERSION,
    VISUAL_PRESET,
)


def generate_fade_frames(
    frame_a_path: Path,
    frame_b_path: Path,
    frames_dir: Path,
    transition_frames: int = TRANSITION_FRAMES_DEFAULT,
    transition_prefix: str = "fade",
) -> Dict[str, Any]:
    """
    Generate fade transition frames between two frames.
    Returns dict with transition metadata.

    Args:
        frame_a_path: Path to the starting frame
        frame_b_path: Path to the ending frame
        frames_dir: Directory to save transition frames
        transition_frames: Number of intermediate frames (default 4)
        transition_prefix: Prefix for transition frame filenames

    Returns:
        Dict with:
        - frame_paths: List of transition frame paths
        - transition_count: Number of transition frames generated
        - transition_type: Type of transition ("fade")
    """
    frame_a = Image.open(frame_a_path).convert("RGB")
    frame_b = Image.open(frame_b_path).convert("RGB")

    # Ensure same size
    if frame_a.size != frame_b.size:
        frame_b = frame_b.resize(frame_a.size, Image.LANCZOS)

    frame_paths: List[Path] = []
    width, height = frame_a.size

    for i in range(1, transition_frames + 1):
        # Calculate blend ratio (0.0 = frame_a, 1.0 = frame_b)
        ratio = i / (transition_frames + 1)

        # Create blended frame
        blended = Image.new("RGB", (width, height))

        # Get pixel data
        pixels_a = frame_a.load()
        pixels_b = frame_b.load()
        pixels_blended = blended.load()

        for y in range(height):
            for x in range(width):
                r_a, g_a, b_a = pixels_a[x, y]
                r_b, g_b, b_b = pixels_b[x, y]

                # Blend: start with A, end with B
                r = int(r_a * (1 - ratio) + r_b * ratio)
                g = int(g_a * (1 - ratio) + g_b * ratio)
                b = int(b_a * (1 - ratio) + b_b * ratio)

                pixels_blended[x, y] = (r, g, b)

        # Save transition frame
        output_name = f"{transition_prefix}_{i:03d}.png"
        output_path = frames_dir / output_name
        blended.save(output_path, "PNG")
        frame_paths.append(output_path)

    return {
        "frame_paths": [str(p) for p in frame_paths],
        "transition_count": len(frame_paths),
        "transition_type": TRANSITION_TYPE,
        "transition_frames": transition_frames,
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
    }


def estimate_transition_duration(
    transition_frames: int,
    frame_duration_sec: float = 0.1,
) -> float:
    """
    Estimate the total duration of transition frames.

    Args:
        transition_frames: Number of transition frames
        frame_duration_sec: Duration per transition frame in seconds

    Returns:
        Total duration in seconds
    """
    return transition_frames * frame_duration_sec


def build_frame_sequence_with_transitions(
    frame_paths: List[Path],
    frames_dir: Path,
    transition_frames: int = TRANSITION_FRAMES_DEFAULT,
    enabled: bool = True,
) -> Dict[str, Any]:
    """
    Build a complete frame sequence with transitions between consecutive frames.
    Returns the sequence with transition metadata.

    Args:
        frame_paths: List of main frame paths in order
        frames_dir: Directory to save transition frames
        transition_frames: Number of intermediate frames per transition
        enabled: Whether to generate transitions

    Returns:
        Dict with:
        - sequence: Ordered list of all frames (main + transitions)
        - transition_count: Total number of transition frames
        - transition_type: Type of transition used
        - duration_per_frame: Dict mapping frame path to duration
    """
    sequence: List[Dict[str, Any]] = []
    duration_per_frame: Dict[str, float] = {}

    if not enabled or len(frame_paths) < 2:
        # No transitions, just return original frames
        for fp in frame_paths:
            sequence.append({"path": str(fp), "type": "main"})
            duration_per_frame[str(fp)] = 0.0  # Will be set by caller
        return {
            "sequence": sequence,
            "transition_count": 0,
            "transition_type": None if not enabled else TRANSITION_TYPE,
            "duration_per_frame": duration_per_frame,
            "transitionEnabled": enabled,
        }

    # Main frame duration (slightly shorter when transitions are present)
    main_duration = 0.1  # Will be adjusted by caller
    transition_duration = 0.08  # Shorter duration for transition frames

    for i, frame_path in enumerate(frame_paths):
        # Add main frame
        sequence.append({"path": str(frame_path), "type": "main", "index": i})
        duration_per_frame[str(frame_path)] = main_duration

        # Add transition frames after this frame (if not last)
        if i < len(frame_paths) - 1:
            trans_result = generate_fade_frames(
                frame_path,
                frame_paths[i + 1],
                frames_dir,
                transition_frames=transition_frames,
                transition_prefix=f"fade_{i:02d}",
            )

            for j, trans_path_str in enumerate(trans_result["frame_paths"]):
                trans_path = Path(trans_path_str)
                sequence.append({
                    "path": trans_path_str,
                    "type": "transition",
                    "index": i,
                    "transition_index": j,
                    "transition_of": str(frame_path),
                })
                duration_per_frame[trans_path_str] = transition_duration

    return {
        "sequence": sequence,
        "transition_count": sum(1 for f in sequence if f["type"] == "transition"),
        "transition_type": TRANSITION_TYPE,
        "transition_frames": transition_frames,
        "duration_per_frame": duration_per_frame,
        "transitionEnabled": True,
        "templateVersion": TEMPLATE_VERSION,
        "visualPreset": VISUAL_PRESET,
    }
