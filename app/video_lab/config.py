"""
Runtime configuration for Video Lab.

All runtime paths and URL prefixes are centralised here so that they can be
environment-variable overridden on a new machine without editing source code.

Environment variables
---------------------
VIDEO_LAB_RUNTIME_DIR        : Base runtime directory (default: "runtime")
VIDEO_LAB_EXPERIMENTS_DIR    : Experiment output directory
                              (default: "$VIDEO_LAB_RUNTIME_DIR/video_lab/experiments")
PUBLIC_RUNTIME_URL_PREFIX   : URL prefix for static file serving (default: "/runtime")
FFMPEG_BINARY               : Path to ffmpeg binary (default: "" = use PATH)
FFPROBE_BINARY              : Path to ffprobe binary (default: "" = use PATH)
"""

from pathlib import Path
import os

# Base runtime directory (the directory that gets mounted as a StaticFiles mount)
RUNTIME_DIR: Path = Path(os.getenv("VIDEO_LAB_RUNTIME_DIR", "runtime")).resolve()

# Experiment output directory — under RUNTIME_DIR so it is served statically
_VIDEO_LAB_EXPERIMENTS_DEFAULT = RUNTIME_DIR / "video_lab" / "experiments"
VIDEO_LAB_EXPERIMENTS_DIR: Path = Path(
    os.getenv("VIDEO_LAB_EXPERIMENTS_DIR", str(_VIDEO_LAB_EXPERIMENTS_DEFAULT))
).resolve()

# Public URL prefix used when converting a file path to a URL via path_to_url()
PUBLIC_RUNTIME_URL_PREFIX: str = os.getenv("PUBLIC_RUNTIME_URL_PREFIX", "/runtime")

# External binaries
FFMPEG_BINARY: str = os.getenv("FFMPEG_BINARY", "")
FFPROBE_BINARY: str = os.getenv("FFPROBE_BINARY", "")
