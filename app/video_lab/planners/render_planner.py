"""
Render Planner - 渲染计划生成
"""

from typing import Any


def generate_render_plan(
    script: dict[str, Any],
    storyboard: dict[str, Any],
    aspect_ratio: str,
    method_category: str,
) -> dict[str, Any]:
    """
    生成渲染参数计划。
    包括：帧率、分辨率、编码参数、输出格式。
    """
    resolution_map = {
        "9:16": "1080x1920",
        "16:9": "1920x1080",
    }

    resolution = resolution_map.get(aspect_ratio, "1080x1920")

    if method_category == "template_programmatic_render":
        return {
            "renderer": "Remotion",
            "resolution": resolution,
            "fps": 30,
            "codec": "h264",
            "format": "mp4",
            "durationFrames": storyboard.get("estimatedDurationSec", 45) * 30,
            "outputPath": "/tmp/renders/{experiment_id}/output.mp4",
            "steps": [
                "1. 注入模板参数 JSON",
                "2. 启动 Remotion 渲染",
                "3. 等待帧序列生成",
                "4. FFmpeg 编码为 MP4",
                "5. 返回输出路径",
            ],
        }
    elif method_category == "local_frame_compose":
        return {
            "renderer": "Pillow + FFmpeg",
            "resolution": resolution,
            "fps": 30,
            "codec": "libx264",
            "format": "mp4",
            "durationFrames": storyboard.get("estimatedDurationSec", 45) * 30,
            "outputPath": "/tmp/frames/{experiment_id}/output.mp4",
            "steps": [
                "1. Pillow 生成每帧 PNG",
                "2. FFmpeg concat 帧序列",
                "3. 编码输出 MP4",
            ],
        }
    elif method_category == "local_media_compose":
        return {
            "renderer": "MoviePy + FFmpeg",
            "resolution": resolution,
            "fps": 30,
            "codec": "libx264",
            "format": "mp4",
            "durationFrames": storyboard.get("estimatedDurationSec", 45) * 30,
            "outputPath": "/tmp/media/{experiment_id}/output.mp4",
            "steps": [
                "1. MoviePy 合成视频片段",
                "2. 压制字幕轨道",
                "3. 混音 BGM",
                "4. 输出 MP4",
            ],
        }
    else:
        return {
            "renderer": "Mock",
            "resolution": resolution,
            "fps": 30,
            "codec": "h264",
            "format": "mp4",
            "durationFrames": 0,
            "outputPath": "",
            "steps": ["mock"],
        }
