"""
remotion_renderer.py - Execute Remotion render via subprocess
V0.3.1: Minimum verification
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import get_experiment_dir, path_to_url, write_manifest
from app.video_lab.config import REMOTION_DIR
# Paths passed to CLI are relative to cwd=REMOTION_DIR
REMOTION_ROOT_TSX = Path("src") / "Root.tsx"
REMOTION_PROPS_PATH = Path("src") / "props.json"
REMOTION_ENTRY = "AiNewsVideo"
# shell=True needed on Windows for npx.cmd
USE_SHELL = os.name == "nt"


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

    # Check npm
    npm_path = shutil.which("npm")
    if not npm_path:
        return False, "npm not found. Install Node.js/npm to use Remotion rendering."

    # Check npx - use shell=True on Windows since npx is npx.cmd
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=USE_SHELL,
        )
        if result.returncode != 0:
            return False, "npx not available. Check Node.js installation."
    except Exception as e:
        return False, f"npx check failed: {e}"

    # Check if remotion package is installed under the configured REMOTION_DIR
    remotion_pkg = REMOTION_DIR / "node_modules" / "remotion"
    if not remotion_pkg.exists():
        return (
            False,
            f"Remotion not installed at {REMOTION_DIR}. Run: cd {REMOTION_DIR} && npm install",
        )

    return True, "Remotion environment available"


def _find_mp4_in_dir(directory: Path) -> Path | None:
    """Search directory recursively for any .mp4 file (fallback when output path is unknown)."""
    if not directory.exists():
        return None
    for mp4 in directory.rglob("*.mp4"):
        # Skip common non-remotion files
        if mp4.name in ("final_with_audio.mp4", "voiceover.mp3", "clip.mp4", "output.mp4"):
            return mp4
    return None


def render_remotion_video(
    experiment_id: str,
    props: dict[str, Any],
    timeout: int = 300,
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

    # Build npx remotion render command
    # npx remotion render <entry> <compName> <output> --props=<propsPath> --codec=h264
    # Note: --props path must use ./ prefix for relative paths on Windows
    cmd = [
        "npx",
        "remotion",
        "render",
        "./" + str(REMOTION_ROOT_TSX),  # ./src/Root.tsx
        REMOTION_ENTRY,
        str(output_mp4_posix),
        "--props",
        "./" + str(REMOTION_PROPS_PATH),  # ./src/props.json
        "--codec",
        "h264",
    ]
    if frame_range:
        cmd += ["--frames", frame_range]
    logs.append(f"[Remotion] Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=USE_SHELL,  # Windows: shell needed for .cmd files like npx.cmd
        )
        stdout = result.stdout
        stderr = result.stderr
        logs.append(f"[Remotion] stdout: {stdout[:500]}")
        if stderr:
            logs.append(f"[Remotion] stderr: {stderr[:500]}")

        # Check for success: returncode 0 AND file exists
        found_mp4: Path | None = None
        if result.returncode == 0:
            if output_mp4.exists():
                found_mp4 = output_mp4
                logs.append(f"[Remotion] Output found at expected path: {output_mp4}")
            else:
                # Fallback: search for any MP4 in experiment directory
                fallback = _find_mp4_in_dir(exp_dir)
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
                "createdAt": subprocess.check_output(
                    ["python", "-c", "from datetime import datetime; print(datetime.utcnow().isoformat())"],
                    text=True,
                ).strip(),
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
            msg = f"Remotion render failed with code {rc}{decoded_msg}"
            if stderr:
                msg += f": {stderr[:200]}"
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
        msg = f"Remotion render exception: {e}"
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
