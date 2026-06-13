"""
Adapter: local_frame_compose
本地图像帧合成 + FFmpeg
"""

from app.video_lab.models import VideoExperimentResult


def run_local_frame_compose(
    experiment_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟本地图像帧合成流程。
    使用 Pillow/Canvas/OpenCV 生成帧，FFmpeg 合成视频。
    """
    logs = [
        "[1/5] 初始化合成器...",
        "[2/5] 生成图像帧序列 (30fps)...",
        "[3/5] 应用动画参数:位移、缩放、淡入淡出...",
        "[4/5] 调用 FFmpeg 合成 MP4...",
        "[5/5] 输出视频完成",
    ]

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/local_frame_compose.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "frameCount": 900,
            "fps": 30,
            "resolution": "1080x1920",
            "format": "mp4",
            "codec": "libx264",
        },
        logs=logs,
        provider="Pillow + FFmpeg",
        adapter="local_frame_compose",
        rawOutput={
            "method": "local_frame_compose",
            "frameEngine": "Pillow",
            "synthesizer": "FFmpeg",
            "status": "mock_success",
        },
    )
