"""
remotion_renderer.py - Execute Remotion render via subprocess
V0.3.1: Minimum verification
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import get_experiment_dir, path_to_url, write_manifest


# Path to the Remotion workspace (relative to project root)
REMOTION_DIR = Path("remotion")
REMOTION_SRC = REMOTION_DIR / "src"
REMOTION_ROOT_TSX = REMOTION_SRC / "Root.tsx"
REMOTION_ENTRY = "AiNewsVideo"


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

    # Check npx
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, "npx not available. Check Node.js installation."
    except Exception as e:
        return False, f"npx check failed: {e}"

    # Check if remotion package is installed
    remotion_pkg = REMOTION_DIR / "node_modules" / "remotion"
    if not remotion_pkg.exists():
        return (
            False,
            "Remotion not installed. Run: cd remotion && npm install",
        )

    return True, "Remotion environment available"


def render_remotion_video(
    experiment_id: str,
    props: dict[str, Any],
    timeout: int = 300,
) -> dict[str, Any]:
    """
    Execute Remotion render for the AiNewsVideo template.

    Args:
        experiment_id: experiment identifier
        props: Remotion props (from props_builder)
        timeout: max seconds to wait for render

    Returns:
        dict with keys: success (bool), videoUrl (str), manifestUrl (str),
                        message (str), logs (list[str]), warnings (list[str])
    """
    warnings: list[str] = []
    logs: list[str] = []
    exp_dir = get_experiment_dir(experiment_id)
    output_mp4 = exp_dir / "output.mp4"

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

    # Write props JSON to remotion workspace
    remotion_props_path = REMOTION_DIR / "src" / "props.json"
    remotion_props_path.parent.mkdir(parents=True, exist_ok=True)
    with open(remotion_props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)
    logs.append(f"[Remotion] Props written to {remotion_props_path}")

    # Build npx remotion render command
    # npx remotion render <entry> <compName> <output> --props=<propsPath> --codec=h264
    cmd = [
        "npx",
        "remotion",
        "render",
        str(REMOTION_ROOT_TSX),
        REMOTION_ENTRY,
        str(output_mp4),
        "--props",
        str(remotion_props_path),
        "--codec",
        "h264",
    ]
    logs.append(f"[Remotion] Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout
        stderr = result.stderr
        logs.append(f"[Remotion] stdout: {stdout[:500]}")
        if stderr:
            logs.append(f"[Remotion] stderr: {stderr[:500]}")

        if result.returncode == 0 and output_mp4.exists():
            video_url = path_to_url(output_mp4)
            logs.append(f"[Remotion] Success: {output_mp4} -> {video_url}")

            # Write manifest
            manifest = {
                "experimentId": experiment_id,
                "method": "template_programmatic_render",
                "engine": "remotion",
                "resolution": "1080x1920",
                "fps": 30,
                "durationSec": props.get("durationSec", 45),
                "stylePreset": props.get("stylePreset", "ai_frontier_dark"),
                "outputVideo": str(output_mp4),
                "outputVideoUrl": video_url,
                "props": props,
                "createdAt": subprocess.check_output(
                    ["python", "-c", "from datetime import datetime; print(datetime.utcnow().isoformat())"],
                    text=True,
                ).strip(),
            }
            manifest_path = write_manifest(experiment_id, manifest)
            manifest_url = path_to_url(manifest_path)

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
            msg = f"Remotion render failed with code {result.returncode}"
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
