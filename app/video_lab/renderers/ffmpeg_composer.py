"""
FFmpeg Composer - 合成 PNG 帧序列为 MP4 视频
"""

import subprocess
import shlex
from pathlib import Path
from typing import Tuple, Dict, List, Any


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in PATH."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_ffmpeg_version() -> str:
    """Get FFmpeg version string."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            first_line = result.stdout.decode().split("\n")[0]
            return first_line.strip()
    except Exception:
        pass
    return "unknown"


def compose_video_from_frames(
    frames_dir: Path,
    output_path: Path,
    duration_per_frame: Dict[str, float],
    fps: int = 30,
    resolution: Tuple[int, int] = (1080, 1920),
    timeout: int = 300,
) -> Dict:
    """
    Compose PNG frames into an MP4 video using FFmpeg concat demuxer.

    Args:
        frames_dir: Directory containing PNG frames
        output_path: Path for output MP4 file
        duration_per_frame: Dict mapping frame filename to duration in seconds
        fps: Output framerate
        resolution: (width, height) tuple
        timeout: Timeout in seconds

    Returns:
        dict with keys: success (bool), message (str), ffmpeg_command (str)
    """
    if not check_ffmpeg_available():
        return {
            "success": False,
            "message": "FFmpeg not found. Please install FFmpeg and ensure it is available in PATH.",
            "ffmpeg_command": "",
            "version": "not_found",
        }

    # Build frames.txt for concat demuxer with absolute paths
    frames_txt = frames_dir / "frames.txt"
    with open(frames_txt, "w", encoding="utf-8") as ft:
        for frame_name, duration in duration_per_frame.items():
            frame_path = (frames_dir / frame_name).resolve().as_posix()
            ft.write(f"file '{frame_path}'\n")
            ft.write(f"duration {duration}\n")
        # Repeat last frame to avoid duration issues at end
        last_frame = list(duration_per_frame.keys())[-1]
        ft.write(f"file '{(frames_dir / last_frame).resolve().as_posix()}'\n")

    width, height = resolution

    # Use ABSOLUTE paths throughout — do NOT rely on cwd
    frames_txt_abs = frames_txt.resolve().as_posix()
    output_abs = output_path.resolve().as_posix()

    # Build FFmpeg command with absolute paths
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", frames_txt_abs,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-r", str(fps),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_abs,
    ]

    cmd_str = " ".join(shlex.quote(c) for c in cmd)

    try:
        # No cwd dependency — all paths are absolute
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Video composed successfully: {output_path.name}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
            }
        else:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"FFmpeg failed with return code {result.returncode}: {error_msg[:500]}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": f"FFmpeg timed out after {timeout} seconds",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"FFmpeg error: {str(e)}",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
        }


def build_concat_file_content(
    frame_sequence: List[Dict[str, Any]],
    duration_by_path: Dict[str, float],
) -> str:
    """
    Build FFmpeg concat demuxer file content from frame sequence.

    Args:
        frame_sequence: List of frame dicts with at least 'path' key
        duration_by_path: Dict mapping path (full or filename) to duration

    Returns:
        Content string for frames.txt concat file
    """
    lines: List[str] = []

    for frame in frame_sequence:
        path_str = frame["path"]
        file_name = Path(path_str).name

        # Try to find duration: full path first, then filename
        duration = (
            duration_by_path.get(path_str)
            or duration_by_path.get(file_name)
            or frame.get("duration")
            or 0.1
        )

        # Convert to absolute POSIX path for FFmpeg
        abs_path = Path(path_str).resolve().as_posix()
        lines.append(f"file '{abs_path}'")
        lines.append(f"duration {duration}")

    # Repeat last frame to avoid duration issues at end
    if frame_sequence:
        last_abs = Path(frame_sequence[-1]["path"]).resolve().as_posix()
        lines.append(f"file '{last_abs}'")

    return "\n".join(lines) + "\n"


def compose_video_from_frame_sequence(
    frame_sequence: List[Dict[str, Any]],
    output_path: Path,
    duration_by_path: Dict[str, float],
    fps: int = 30,
    resolution: Tuple[int, int] = (1080, 1920),
    timeout: int = 300,
) -> Dict[str, Any]:
    """
    Compose PNG frames into MP4 using a predefined frame sequence.

    Args:
        frame_sequence: Ordered list of frame dicts, each containing at least 'path'
        output_path: Path for output MP4 file
        duration_by_path: Dict mapping frame path (full or filename) to duration in seconds
        fps: Output framerate
        resolution: (width, height) tuple
        timeout: Timeout in seconds

    Returns:
        dict with keys: success (bool), message (str), ffmpeg_command (str), version (str)
    """
    if not check_ffmpeg_available():
        return {
            "success": False,
            "message": "FFmpeg not found. Please install FFmpeg and ensure it is available in PATH.",
            "ffmpeg_command": "",
            "version": "not_found",
        }

    # Build frames.txt using the sequence order
    frames_txt_content = build_concat_file_content(frame_sequence, duration_by_path)

    # Determine frames_dir from first frame or output_path
    if frame_sequence:
        first_frame_path = Path(frame_sequence[0]["path"])
        frames_dir = first_frame_path.parent
    else:
        frames_dir = output_path.parent

    # Write frames.txt with absolute path to frames_dir
    frames_txt = frames_dir / "frames.txt"
    with open(frames_txt, "w", encoding="utf-8") as ft:
        ft.write(frames_txt_content)

    width, height = resolution

    # Use ABSOLUTE paths throughout — do NOT rely on cwd
    frames_txt_abs = frames_txt.resolve().as_posix()
    output_abs = output_path.resolve().as_posix()

    # Build FFmpeg command with absolute paths
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", frames_txt_abs,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-r", str(fps),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_abs,
    ]

    cmd_str = " ".join(shlex.quote(c) for c in cmd)

    try:
        # No cwd dependency — all paths are absolute
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Video composed successfully: {output_path.name}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
            }
        else:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"FFmpeg failed with return code {result.returncode}: {error_msg[:500]}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": f"FFmpeg timed out after {timeout} seconds",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"FFmpeg error: {str(e)}",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
        }
