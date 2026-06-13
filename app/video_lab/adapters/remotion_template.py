"""
Adapter: template_programmatic_render
Remotion 程序化模板渲染
"""

from app.video_lab.models import VideoExperimentResult


def run_remotion_template(
    experiment_id: str,
    input_payload: dict,
    params: dict,
) -> VideoExperimentResult:
    """
    模拟 Remotion 程序化模板渲染流程。
    使用 React/CSS/SVG/Canvas 做模板化视频渲染。
    """
    logs = [
        "[1/6] 加载 Remotion 项目...",
        "[2/6] 解析模板参数 JSON...",
        "[3/6] 渲染 React 组件序列 (Canvas)...",
        "[4/6] 合成音频轨道 (TTS + BGM)...",
        "[5/6] 编码输出 MP4 (H.264)...",
        "[6/6] 渲染完成，生成预览链接",
    ]

    return VideoExperimentResult(
        experimentId=experiment_id,
        videoUrl=f"https://mock-cdn.example.com/videos/{experiment_id}/remotion_render.mp4",
        coverUrl=f"https://mock-cdn.example.com/covers/{experiment_id}/cover.jpg",
        assets={
            "compositionId": "InsightCardVideo",
            "frameCount": 1350,
            "fps": 30,
            "resolution": "1080x1920",
            "format": "mp4",
            "templateVersion": "1.0.0",
        },
        logs=logs,
        provider="Remotion",
        adapter="template_programmatic_render",
        rawOutput={
            "method": "template_programmatic_render",
            "renderer": "Remotion",
            "stack": ["React", "Canvas", "FFmpeg"],
            "status": "mock_success",
        },
    )
