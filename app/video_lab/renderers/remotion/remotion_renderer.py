"""
remotion_renderer.py - Execute Remotion render via subprocess
V0.3.1: Minimum verification
"""

import json
import os
import shutil
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import get_experiment_dir, path_to_url, write_manifest
from app.video_lab.config import REMOTION_DIR, ffprobe_bin
# Paths passed to CLI are relative to cwd=REMOTION_DIR
REMOTION_ROOT_TSX = Path("src") / "Root.tsx"
REMOTION_PROPS_PATH = Path("src") / "props.json"
REMOTION_ENTRY = "AiNewsVideo"
REMOTION_CLI_JS = Path("node_modules") / "@remotion" / "cli" / "remotion-cli.js"


def default_remotion_timeout(props: dict[str, Any], *, minimum: int = 300, maximum: int = 900) -> int:
    """Return a render timeout scaled to the actual composition length."""
    try:
        duration_sec = float(props.get("durationSec", 0) or 0)
    except (TypeError, ValueError):
        duration_sec = 0.0
    if duration_sec <= 0:
        return minimum
    # 1080x1920 Remotion renders often take several multiples of the video
    # duration on local Windows machines. Keep a bounded ceiling so a broken
    # render still fails in finite time.
    return max(minimum, min(maximum, int(60 + duration_sec * 3)))


def _probe_mp4_duration(path: Path, timeout: int = 20) -> float:
    """Return video duration if ffprobe can read the MP4, otherwise 0."""
    if not path.exists() or path.stat().st_size <= 0:
        return 0.0
    ffprobe = ffprobe_bin()
    if not Path(ffprobe).exists() and not shutil.which(ffprobe):
        return 0.0
    if not ffprobe:
        return 0.0
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        if result.returncode != 0:
            return 0.0
        return float((result.stdout or "").strip() or 0)
    except Exception:
        return 0.0


def _run_command(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    """Run a command directly so the renderer process has no lingering shell."""
    cmd_strs = [str(x) for x in cmd]
    return subprocess.run(
        cmd_strs,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )


def check_remotion_available() -> tuple[bool, str]:
    """
    Check if node, npm, and npx remotion are available.

    Returns:
        (is_available, message)
    """
    # Check node
    node_path = shutil.which("node")
    if not node_path:
        return False, "Node.js not found. Install Node.js to use Remotion rendering."

    # The renderer invokes the local JS CLI directly, so npm/npx are not
    # runtime dependencies and cannot leave a wrapper shell hanging.
    remotion_cli = REMOTION_DIR / REMOTION_CLI_JS
    if not remotion_cli.exists():
        return (
            False,
            f"Remotion CLI not installed at {remotion_cli}. Run npm install in {REMOTION_DIR}",
        )

    return True, "Remotion environment available"


def _find_mp4_in_dir(directory: Path, preferred_name: str | None = None) -> Path | None:
    """Search directory for an .mp4 file.

    Args:
        directory: directory to search
        preferred_name: if provided, only return this exact filename; otherwise
                       return the first non-final_with_audio.mp4 .mp4 found.
                       final_with_audio.mp4 is never returned (audio post-process artifact).
    """
    if not directory.exists():
        return None

    if preferred_name:
        candidate = directory / preferred_name
        if candidate.exists():
            return candidate
        return None

    for mp4 in directory.rglob("*.mp4"):
        if mp4.name == "final_with_audio.mp4":
            continue
        return mp4
    return None


def render_remotion_video(
    experiment_id: str,
    props: dict[str, Any],
    timeout: int | None = None,
    frame_range: str | None = None,
    output_name: str = "output.mp4",
) -> dict[str, Any]:
    """
    Execute Remotion render for the AiNewsVideo template.

    Args:
        experiment_id: experiment identifier
        props: Remotion props (from props_builder)
        timeout: max seconds to wait for render
        frame_range: optional "0-90" 只渲染该帧范围（片段预览，远快于整片）
        output_name: output filename (default output.mp4; clip 用 clip.mp4)

    Returns:
        dict with keys: success (bool), videoUrl (str), manifestUrl (str),
                        message (str), logs (list[str]), warnings (list[str])
    """
    warnings: list[str] = []
    logs: list[str] = []
    exp_dir = get_experiment_dir(experiment_id)
    if timeout is None:
        timeout = default_remotion_timeout(props)

    # Check environment
    available, avail_msg = check_remotion_available()
    if not available:
        return {
            "success": False,
            "videoUrl": "",
            "manifestUrl": "",
            "message": avail_msg,
            "logs": [f"[Remotion] {avail_msg}"],
            "warnings": [avail_msg],
        }

    # Write props JSON to remotion workspace src/ (relative to cwd=remotion)
    remotion_props_path = REMOTION_DIR / REMOTION_PROPS_PATH  # = remotion/src/props.json on disk
    remotion_props_path.parent.mkdir(parents=True, exist_ok=True)
    with open(remotion_props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)
    logs.append(f"[Remotion] cwd: {REMOTION_DIR.resolve()}")
    logs.append(f"[Remotion] root: {REMOTION_ROOT_TSX}")
    logs.append(f"[Remotion] props: {REMOTION_PROPS_PATH} -> {remotion_props_path}")

    # Use absolute path with forward slashes for FFmpeg/Remotion compatibility on Windows
    output_mp4 = exp_dir.resolve() / output_name
    output_mp4_posix = Path(output_mp4.as_posix())  # ensures forward slashes
    logs.append(f"[Remotion] output: {output_mp4_posix}")

    # Invoke the local Remotion CLI with Node directly. On Windows, wrapping
    # this in `npx` + `shell=True` can leave cmd.exe alive after the MP4 is
    # complete, making Python wait until the timeout boundary.
    node_path = shutil.which("node") or "node"
    remotion_cli = REMOTION_DIR / REMOTION_CLI_JS
    # Note: --props path must use ./ prefix for relative paths on Windows
    cmd = [
        node_path,
        str(remotion_cli),
        "render",
        "./" + str(REMOTION_ROOT_TSX),  # ./src/Root.tsx
        REMOTION_ENTRY,
        str(output_mp4_posix),
        "--props",
        "./" + str(REMOTION_PROPS_PATH),  # ./src/props.json
        "--codec",
        "h264",
        "--x264-preset",
        str(props.get("x264Preset") or "veryfast"),
        "--crf",
        str(props.get("crf") or 26),
        "--concurrency",
        str(props.get("concurrency") or "75%"),
    ]
    if frame_range:
        cmd += ["--frames", frame_range]
    logs.append(f"[Remotion] Command: {' '.join(cmd)}")

    try:
        result = _run_command(cmd, REMOTION_DIR, timeout)
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        logs.append(f"[Remotion] returncode: {result.returncode}")
        logs.append(f"[Remotion] stdout: {stdout[:1000]}" if stdout else "[Remotion] stdout: <empty>")
        logs.append(f"[Remotion] stderr: {stderr[:1000]}" if stderr else "[Remotion] stderr: <empty>")

        # Check for success: returncode 0 AND file exists
        found_mp4: Path | None = None
        if result.returncode == 0:
            if output_mp4.exists():
                found_mp4 = output_mp4
                logs.append(f"[Remotion] Output found at expected path: {output_mp4}")
            else:
                # Fallback: search for any MP4 in experiment directory
                fallback = _find_mp4_in_dir(exp_dir, output_name)
                if fallback:
                    found_mp4 = fallback
                    logs.append(f"[Remotion] Output found via fallback search: {found_mp4}")
                    warnings.append(f"Remotion output not at expected path, used: {found_mp4.name}")
                else:
                    logs.append(f"[Remotion] returncode=0 but no MP4 found at {output_mp4} or subdirectories")

        if found_mp4:
            video_url = path_to_url(found_mp4)
            logs.append(f"[Remotion] Success: {found_mp4} -> {video_url}")

            # Write manifest with final manifestUrl
            manifest_path = get_experiment_dir(experiment_id) / "manifest.json"
            manifest_url = path_to_url(manifest_path)
            manifest = {
                "experimentId": experiment_id,
                "method": "template_programmatic_render",
                "engine": "remotion",
                "resolution": "1080x1920",
                "fps": 30,
                "durationSec": props.get("durationSec", 45),
                "stylePreset": props.get("stylePreset", "ai_frontier_dark"),
                "outputVideo": str(found_mp4),
                "outputVideoUrl": video_url,
                "manifestUrl": manifest_url,
                "props": props,
                # 直接用 datetime；旧实现 spawn `python` 在未把 python 加入 PATH 的
                # 新机器上会直接抛异常（被外层 except 吞成 render exception）。
                "createdAt": datetime.utcnow().isoformat(),
            }
            write_manifest(experiment_id, manifest)

            return {
                "success": True,
                "videoUrl": video_url,
                "manifestUrl": manifest_url,
                "message": "Remotion render completed successfully",
                "logs": logs,
                "warnings": warnings,
                "manifestPath": str(manifest_path),
            }
        else:
            # Decode Windows FFmpeg exit codes that look like large unsigned ints
            rc = result.returncode
            decoded_msg = ""
            if rc > 255 and os.name == "nt":
                # Windows FFmpeg may exit with signed int cast to unsigned 32-bit
                signed_rc = rc - (1 << 32)
                decoded_msg = f" (signed: {signed_rc})"

            # Fall back to stdout when stderr is empty
            combined_tail = (stderr or stdout or "").strip()
            if len(combined_tail) > 800:
                combined_tail = combined_tail[-800:]

            msg = f"Remotion render failed with code {rc}{decoded_msg}"
            if combined_tail:
                msg += f": {combined_tail}"

            logs.append(f"[Remotion] {msg}")
            warnings.append(msg)
            return {
                "success": False,
                "videoUrl": "",
                "manifestUrl": "",
                "message": msg,
                "logs": logs,
                "warnings": warnings,
            }

    except subprocess.TimeoutExpired:
        msg = f"Remotion render timed out after {timeout}s"
        found_mp4 = output_mp4 if output_mp4.exists() else _find_mp4_in_dir(exp_dir, output_name)
        if found_mp4:
            actual_duration = _probe_mp4_duration(found_mp4)
            expected_duration = float(props.get("durationSec", 0) or 0)
            if actual_duration > 0 and (expected_duration <= 0 or actual_duration >= expected_duration * 0.9):
                video_url = path_to_url(found_mp4)
                manifest_path = get_experiment_dir(experiment_id) / "manifest.json"
                manifest_url = path_to_url(manifest_path)
                warning = (
                    f"{msg}, but a valid MP4 was recovered "
                    f"({actual_duration:.1f}s / expected {expected_duration:.1f}s)"
                )
                warnings.append(warning)
                logs.append(f"[Remotion] {warning}")
                manifest = {
                    "experimentId": experiment_id,
                    "method": "template_programmatic_render",
                    "engine": "remotion",
                    "resolution": "1080x1920",
                    "fps": 30,
                    "durationSec": props.get("durationSec", actual_duration),
                    "stylePreset": props.get("stylePreset", "ai_frontier_dark"),
                    "outputVideo": str(found_mp4),
                    "outputVideoUrl": video_url,
                    "manifestUrl": manifest_url,
                    "props": props,
                    "recoveredAfterTimeout": True,
                    "recoveredDurationSec": actual_duration,
                    "createdAt": datetime.utcnow().isoformat(),
                }
                write_manifest(experiment_id, manifest)
                return {
                    "success": True,
                    "videoUrl": video_url,
                    "manifestUrl": manifest_url,
                    "message": "Remotion render completed at timeout boundary",
                    "logs": logs,
                    "warnings": warnings,
                    "manifestPath": str(manifest_path),
                }
        logs.append(f"[Remotion] {msg}")
        warnings.append(msg)
        return {
            "success": False,
            "videoUrl": "",
            "manifestUrl": "",
            "message": msg,
            "logs": logs,
            "warnings": warnings,
        }
    except Exception as e:
        msg = f"Remotion render exception: {type(e).__name__}: {e}"
        # 带上完整 traceback，避免异常被吞后无法定位（新机器/新目录排查关键）
        tb = traceback.format_exc()
        logs.append(f"[Remotion] {msg}")
        logs.append(f"[Remotion] traceback:\n{tb}")
        warnings.append(msg)
        return {
            "success": False,
            "videoUrl": "",
            "manifestUrl": "",
            "message": msg,
            "logs": logs,
            "warnings": warnings,
        }
