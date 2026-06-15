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
REMOTION_DIR                : Path to remotion workspace (default: "<project_root>/remotion")
FRONTEND_DIR               : Path to frontend source (default: "<project_root>/frontend")
"""

from pathlib import Path
import os

# Project root — resolved once at import time, used for all relative paths
# config.py is at app/video_lab/config.py → parents[2] = project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Base runtime directory (the directory that gets mounted as a StaticFiles mount)
# 默认基于项目根的绝对路径，避免依赖 uvicorn 启动时的 CWD（换目录/新机器更稳）。
RUNTIME_DIR: Path = Path(
    os.getenv("VIDEO_LAB_RUNTIME_DIR", str(_PROJECT_ROOT / "runtime"))
).resolve()

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

# Workspace directories (absolute paths; env overrides default to project subdirs)
REMOTION_DIR: Path = Path(
    os.getenv("REMOTION_DIR", str(_PROJECT_ROOT / "remotion"))
).resolve()
FRONTEND_DIR: Path = Path(
    os.getenv("FRONTEND_DIR", str(_PROJECT_ROOT / "frontend"))
).resolve()

# Convenience alias
PROJECT_ROOT = _PROJECT_ROOT


def ffmpeg_bin() -> str:
    """ffmpeg 可执行路径：配置了 FFMPEG_BINARY 则用它，否则用 PATH 里的 'ffmpeg'。"""
    return FFMPEG_BINARY or "ffmpeg"


def ffprobe_bin() -> str:
    """ffprobe 可执行路径：配置了 FFPROBE_BINARY 则用它，否则用 PATH 里的 'ffprobe'。"""
    return FFPROBE_BINARY or "ffprobe"
