"""
Path contract — unified runtime path utilities for Video Lab.

Provides a single source of truth for all path ↔ URL conversions so that:
- All file writes go under RUNTIME_DIR
- All URLs are prefixed with PUBLIC_RUNTIME_URL_PREFIX
- All URL → path conversions use the same logic
- Custom RUNTIME_DIR and PUBLIC_RUNTIME_URL_PREFIX work consistently everywhere

Environment variables
--------------------
VIDEO_LAB_RUNTIME_DIR        : Base runtime directory (default: "runtime")
PUBLIC_RUNTIME_URL_PREFIX   : URL prefix (default: "/runtime")
"""

from pathlib import Path
from app.video_lab.config import RUNTIME_DIR, PUBLIC_RUNTIME_URL_PREFIX


def runtime_url_prefix() -> str:
    """Return the current PUBLIC_RUNTIME_URL_PREFIX (always without trailing slash)."""
    return PUBLIC_RUNTIME_URL_PREFIX.rstrip("/")


def path_to_runtime_url(file_path: Path | str) -> str:
    """
    Convert a filesystem path to a URL under PUBLIC_RUNTIME_URL_PREFIX.

    Strategy:
    1. Resolve the path and use relative_to(RUNTIME_DIR) so custom RUNTIME_DIR
       paths (e.g. D:/video-lab-runtime) always map cleanly to /runtime/...
    2. Fallback: strip any existing /runtime/ prefix and rebuild.

    Examples:
      path_to_runtime_url("runtime/video_lab/experiments/exp/final.mp4")
        → "/runtime/video_lab/experiments/exp/final.mp4"

      path_to_runtime_url("D:/custom-runtime/video_lab/experiments/exp/final.mp4")
        → "/runtime/video_lab/experiments/exp/final.mp4"
    """
    path = Path(file_path)
    prefix = runtime_url_prefix() or "/runtime"

    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    # 1. Inside RUNTIME_DIR → clean sub-path
    try:
        rel = resolved.relative_to(RUNTIME_DIR.resolve())
        return f"{prefix}/{rel.as_posix()}"
    except ValueError:
        pass

    # 2. Normalize and strip any existing /runtime/ marker
    normalized = resolved.as_posix().replace("\\", "/")
    marker = "/runtime/"
    if marker in normalized:
        return f"{prefix}/" + normalized.split(marker, 1)[1]

    # 3. Fallback: everything under the prefix
    return f"{prefix}/" + normalized.lstrip("/")


def runtime_url_to_path(url_or_path: str) -> Path:
    """
    Convert a runtime URL (or any stored path) to a local filesystem Path.

    Supports:
    - /runtime/video_lab/x.mp4          → RUNTIME_DIR/video_lab/x.mp4
    - /assets/video_lab/x.mp4           → RUNTIME_DIR/video_lab/x.mp4  (current prefix strip)
    - runtime/video_lab/x.mp4           → RUNTIME_DIR/video_lab/x.mp4
    - video_lab/x.mp4                   → RUNTIME_DIR/video_lab/x.mp4
    - http://host/runtime/video_lab/x   → RUNTIME_DIR/video_lab/x
    - http://host/assets/video_lab/x    → RUNTIME_DIR/video_lab/x
    - style_gallery/records/xxx.jsonl   → RUNTIME_DIR/style_gallery/records/xxx.jsonl
    - Historical /runtime/... stored URLs when current prefix is /assets

    Returns a Path. Existence is not guaranteed — caller should verify.
    """
    if not url_or_path:
        return Path()

    s = url_or_path.strip()

    # Strip scheme + host from full URLs
    import re
    m = re.match(r"^https?://[^/]+", s)
    if m:
        s = s[m.end():]

    prefix = runtime_url_prefix()
    prefix_with_slash = f"{prefix}/" if prefix else ""

    # 1. Strip current configured prefix
    if prefix_with_slash and s.startswith(prefix_with_slash):
        s = s[len(prefix_with_slash):]
    elif prefix and s == prefix:
        s = ""

    # 2. Historical fallback: strip /runtime/ even when current prefix is /assets
    #    This handles stored URLs from before the prefix migration
    elif s.startswith("/runtime/"):
        s = s[len("/runtime/"):]

    # 3. Default: missing prefix → prepend runtime/
    if s and not s.startswith("runtime/"):
        s = "runtime/" + s

    # 4. Strip stored runtime/ prefix to avoid double-nesting when RUNTIME_DIR is "runtime"
    if s.startswith("runtime/"):
        s = s[len("runtime/"):]

    # 5. Normalize: ensure s is a relative path before joining
    #    On Windows, RUNTIME_DIR / "/absolute/path" returns the absolute path, not under RUNTIME_DIR
    s = s.lstrip("/")

    # Always return path inside RUNTIME_DIR so custom VIDEO_LAB_RUNTIME_DIR is respected
    return RUNTIME_DIR / s


def strip_runtime_url_prefix(url: str) -> str:
    """
    Strip the PUBLIC_RUNTIME_URL_PREFIX from a URL to get the stored path.

    Handles both default /runtime/ and any custom prefix.

    Examples:
      "/runtime/video_lab/x.mp4"  → "video_lab/x.mp4"
      "/assets/video_lab/x.mp4"   → "video_lab/x.mp4"
      ""                          → ""

    Returns "" for empty/None input.
    """
    if not url:
        return ""
    s = url.strip()
    prefix = runtime_url_prefix()
    prefix_with_slash = f"{prefix}/"

    if s.startswith(prefix_with_slash):
        return s[len(prefix_with_slash):]
    if s.startswith(prefix + "/"):
        return s[len(prefix) + 1:]
    # Default fallback for bare /runtime/
    if s.startswith("/runtime/"):
        return s[len("/runtime/"):]
    return s.lstrip("/")
