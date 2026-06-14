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
    ass_path: Path | str | None = None,
    resolution: tuple[int, int] = (1080, 1920),
    burn_in: bool = True,
    timeout: int = 300,
) -> dict:
    """
    Combine a silent video with a voiceover audio track and optional burned subtitles.

    V0.3.8.1: Prefer ASS subtitles for proper PlayResX/Y scaling. Falls back to SRT
    with `original_size` hint if ASS not provided. The `burn_in` flag can disable
    subtitle burning for visual comparison.

    Args:
        video_path: Path to the silent MP4 video
        audio_path: Path to the voiceover MP3 audio
        output_path: Path for the output MP4
        srt_path: Optional path to SRT subtitle file (legacy)
        ass_path: Optional path to ASS subtitle file (preferred, V0.3.8.1+)
        resolution: (width, height) of the video
        burn_in: If False, do not burn any subtitles (default True)
        timeout: Timeout in seconds

    Returns:
        dict with keys: success, message, ffmpeg_command, version,
        subtitle_renderer, subtitle_style
    """
    if not check_ffmpeg_available():
        return {
            "success": False,
            "message": "FFmpeg not found. Please install FFmpeg and ensure it is available in PATH.",
            "ffmpeg_command": "",
            "version": "not_found",
            "subtitle_renderer": "none",
            "subtitle_style": {},
        }

    video_path = Path(video_path).resolve()
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()

    ass_path_obj: Path | None = Path(ass_path).resolve() if ass_path else None
    srt_path_obj: Path | None = Path(srt_path).resolve() if srt_path else None

    # Pick subtitle source: ASS preferred, else SRT
    subtitle_path: Path | None = None
    subtitle_renderer = "none"
    subtitle_style: dict = {}
    if burn_in:
        if ass_path_obj and ass_path_obj.exists():
            subtitle_path = ass_path_obj
            subtitle_renderer = "ass"
        elif srt_path_obj and srt_path_obj.exists():
            subtitle_path = srt_path_obj
            subtitle_renderer = "srt_subtitles_filter"

    # Validate inputs exist
    if not video_path.exists():
        return {
            "success": False,
            "message": f"Video file not found: {video_path}",
            "ffmpeg_command": "",
            "version": get_ffmpeg_version(),
            "subtitle_renderer": subtitle_renderer,
            "subtitle_style": subtitle_style,
        }
    if not audio_path.exists():
        return {
            "success": False,
            "message": f"Audio file not found: {audio_path}",
            "ffmpeg_command": "",
            "version": get_ffmpeg_version(),
            "subtitle_renderer": subtitle_renderer,
            "subtitle_style": subtitle_style,
        }

    width, height = resolution

    # Build subtitle filter
    sub_for_filter = ""
    if subtitle_path is not None:
        sub_abs = subtitle_path.as_posix()
        # Escape colons and backslashes for FFmpeg filter graph
        sub_escaped = sub_abs.replace("\\", "\\\\").replace(":", "\\:")
        if subtitle_renderer == "ass":
            # ASS already has PlayResX/Y and Style set; just use file directly
            sub_for_filter = f",subtitles='{sub_escaped}'"
            subtitle_style = {
                "renderer": "ass",
                "playResX": width,
                "playResY": height,
            }
        else:  # srt_subtitles_filter
            # SRT needs original_size hint so libass scales correctly
            sub_for_filter = (
                f",subtitles='{sub_escaped}':"
                f"original_size={width}x{height}:"
                f"force_style='"
                f"Fontsize=24,"
                f"MarginV=240,"
                f"MarginH=40,"
                f"Alignment=2,"
                f"Outline=2,"
                f"Shadow=1,"
                f"PrimaryColour=&HFFFFFF&,"
                f"OutlineColour=&H000000&"
                f"'"
            )
            subtitle_style = {
                "renderer": "srt_subtitles_filter",
                "fontSize": 24,
                "marginV": 240,
                "marginH": 40,
                "outline": 2,
                "shadow": 1,
            }

    # Build filter complex
    if sub_for_filter:
        filter_complex = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2{sub_for_filter}[v]"
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
                "subtitle_renderer": subtitle_renderer,
                "subtitle_style": subtitle_style,
            }
        else:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"FFmpeg AV failed with return code {result.returncode}: {error_msg[:500]}",
                "ffmpeg_command": cmd_str,
                "version": get_ffmpeg_version(),
                "subtitle_renderer": subtitle_renderer,
                "subtitle_style": subtitle_style,
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": f"FFmpeg AV timed out after {timeout} seconds",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
            "subtitle_renderer": subtitle_renderer,
            "subtitle_style": subtitle_style,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"FFmpeg AV error: {str(e)}",
            "ffmpeg_command": cmd_str,
            "version": get_ffmpeg_version(),
            "subtitle_renderer": subtitle_renderer,
            "subtitle_style": subtitle_style,
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
