"""
FFmpeg AV Composer - 音视频字幕合成器
V0.3.3: Combines silent video + audio + SRT subtitles into final MP4

Usage:
    result = compose_av_with_subtitles(
        video_path=Path("silent.mp4"),
        audio_path=Path("voiceover.mp3"),
        srt_path=Path("subtitles.srt"),
        output_path=Path("final_with_audio.mp4"),
        resolution=(1080, 1920),
    )
"""

from __future__ import annotations

import os
import subprocess
import shlex
from pathlib import Path

from app.video_lab.renderers.ffmpeg_composer import check_ffmpeg_available, get_ffmpeg_version


def compose_av_with_subtitles(
    video_path: Path | str,
    audio_path: Path | str,
    output_path: Path | str,
    srt_path: Path | str | None = None,
    resolution: tuple[int, int] = (1080, 1920),
    timeout: int = 300,
) -> dict:
    """
    Combine a silent video with a voiceover audio track and optional SRT subtitles.

    Args:
        video_path: Path to the silent MP4 video
        audio_path: Path to the voiceover MP3 audio
        output_path: Path for the output MP4
        srt_path: Optional path to SRT subtitle file
        resolution: (width, height) of the video
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

    video_path = Path(video_path).resolve()
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()
    srt_path_obj: Path | None = Path(srt_path).resolve() if srt_path else None

    # Validate inputs exist
    if not video_path.exists():
        return {
            "success": False,
            "message": f"Video file not found: {video_path}",
            "ffmpeg_command": "",
            "version": get_ffmpeg_version(),
        }
    if not audio_path.exists():
        return {
            "success": False,
            "message": f"Audio file not found: {audio_path}",
            "ffmpeg_command": "",
            "version": get_ffmpeg_version(),
        }

    width, height = resolution

    # Convert SRT path for FFmpeg (needs to be escaped for FFmpeg filter graph)
    srt_for_filter = ""
    if srt_path_obj and srt_path_obj.exists():
        # FFmpeg on Windows needs the SRT path in the filter with proper escaping
        srt_abs = srt_path_obj.as_posix()
        # Escape colons and backslashes for FFmpeg filter graph
        srt_escaped = srt_abs.replace("\\", "\\\\").replace(":", "\\:")
        # Safe area: Fontsize=40 (20% larger than default 24), MarginV=150 (bottom safe ~8% of 1080p),
        # Alignment=bottom (2), Outline=2, Shadow=1, PrimaryColour=white, OutlineColour=black
        # PrimaryColour white = &HFFFFFF; OutlineColour black = &H000000
        srt_for_filter = (
            f",subtitles='{srt_escaped}':"
            f"force_style='"
            f"Fontsize=40,"
            f"MarginV=150,"
            f"MarginH=10,"
            f"Alignment=2,"
            f"Outline=2,"
            f"Shadow=1,"
            f"PrimaryColour=&HFFFFFF&,"
            f"OutlineColour=&H000000&"
            f"'"
        )

    # Build filter complex
    if srt_for_filter:
        filter_complex = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2{srt_for_filter}[v]"
        )
    else:
        filter_complex = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2[v]"
        )

    video_abs = video_path.as_posix()
    audio_abs = audio_path.as_posix()
    output_abs = output_path.as_posix()

    cmd = [
        "ffmpeg", "-y",
        "-i", video_abs,
        "-i", audio_abs,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        output_abs,
    ]

    cmd_str = " ".join(shlex.quote(c) for c in cmd)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"AV composition succeeded: {output_path.name}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
            }
        else:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"FFmpeg AV failed with return code {result.returncode}: {error_msg[:500]}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": f"FFmpeg AV timed out after {timeout} seconds",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"FFmpeg AV error: {str(e)}",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
        }


def compose_video_with_audio(
    video_path: Path | str,
    audio_path: Path | str,
    output_path: Path | str,
    resolution: tuple[int, int] = (1080, 1920),
    timeout: int = 300,
) -> dict:
    """
    Combine a video with an audio track (no subtitles).

    Simpler version of compose_av_with_subtitles for when no SRT is available.
    """
    if not check_ffmpeg_available():
        return {
            "success": False,
            "message": "FFmpeg not found.",
            "ffmpeg_command": "",
            "version": "not_found",
        }

    video_path = Path(video_path).resolve()
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()

    if not video_path.exists():
        return {
            "success": False,
            "message": f"Video file not found: {video_path}",
            "ffmpeg_command": "",
            "version": get_ffmpeg_version(),
        }
    if not audio_path.exists():
        return {
            "success": False,
            "message": f"Audio file not found: {audio_path}",
            "ffmpeg_command": "",
            "version": get_ffmpeg_version(),
        }

    width, height = resolution
    video_abs = video_path.as_posix()
    audio_abs = audio_path.as_posix()
    output_abs = output_path.as_posix()

    cmd = [
        "ffmpeg", "-y",
        "-i", video_abs,
        "-i", audio_abs,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        output_abs,
    ]

    cmd_str = " ".join(shlex.quote(c) for c in cmd)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Video with audio succeeded: {output_path.name}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
            }
        else:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"FFmpeg audio/video failed: {error_msg[:500]}",
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
