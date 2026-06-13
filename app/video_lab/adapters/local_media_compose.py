"""
Adapter: local_media_compose
本地媒体素材合成 - MoviePy / FFmpeg
"""

from app.video_lab.models import VideoExperimentResult


def run_local_media_compose(
    experiment_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟本地媒体素材合成。
    使用 MoviePy / FFmpeg 对图片、音频、字幕、BGM 做合成。
    """
    logs = [
        "[1/6] 加载素材文件...",
        "[2/6] 分析音频波形与 BGM 节奏...",
        "[3/6] 同步字幕时间轴...",
        "[4/6] 执行视频片段拼接...",
        "[5/6] 压制字幕轨道...",
        "[6/6] 混音与最终导出",
    ]

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/local_media_compose.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "clipsCount": 5,
            "totalDurationSec": 45,
            "resolution": "1080x1920",
            "hasAudio": True,
            "hasSubtitle": True,
            "hasBgm": True,
            "format": "mp4",
        },
        logs=logs,
        provider="MoviePy + FFmpeg",
        adapter="local_media_compose",
        rawOutput={
            "method": "local_media_compose",
            "editor": "MoviePy",
            "synthesizer": "FFmpeg",
            "status": "mock_success",
        },
    )
