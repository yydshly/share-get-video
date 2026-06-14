"""
PillowVisualRenderer - 本地帧合成视觉路线（route_id=local_frame_compose）

方式：Pillow 渲染信息卡片帧序列 → FFmpeg 合成静默 MP4。
参数（从 request.params 解析，复用 parse_local_frame_params）：
    transitionEnabled / transitionFrames / highlightMode / includeOverview / includeSummary
"""

from pathlib import Path

from app.video_lab.renderers.visual.base import (
    VisualRenderer,
    VisualRenderRequest,
    VisualRenderResult,
)
from app.video_lab.renderers.local_frame_renderer import generate_frames
from app.video_lab.renderers.ffmpeg_composer import (
    compose_video_from_frame_sequence,
    compose_video_from_frames,
    check_ffmpeg_available,
)
from app.video_lab.renderers.render_params import parse_local_frame_params
from app.video_lab.renderers.file_store import (
    get_experiment_dir,
    get_frames_dir,
    path_to_url,
)


class PillowVisualRenderer(VisualRenderer):
    route_id = "local_frame_compose"
    display_name = "本地帧合成 (Pillow)"

    def is_available(self) -> tuple[bool, str]:
        if not check_ffmpeg_available():
            return False, "FFmpeg not available"
        return True, "Pillow + FFmpeg available"

    def render(self, request: VisualRenderRequest) -> VisualRenderResult:
        logs: list[str] = []
        warnings: list[str] = []

        parsed = parse_local_frame_params(request.params or {})
        rp = parsed.params  # always present (defaults applied)
        warnings.extend(parsed.warnings)

        if not check_ffmpeg_available():
            return VisualRenderResult(
                success=False,
                route_id=self.route_id,
                message="FFmpeg not available",
                logs=logs,
                warnings=warnings,
            )

        # 1) 生成帧序列
        frame_result = generate_frames(
            experiment_id=request.experiment_id,
            structured=request.structured,
            key_points=request.key_points,
            target_duration_sec=int(request.target_duration_sec),
            resolution=request.resolution,
            enable_transitions=rp.transition_enabled,
            transition_frames=rp.transition_frames,
            highlight_mode=rp.highlight_mode,
            include_overview=rp.include_overview,
            include_summary=rp.include_summary,
            segment_durations=request.voiceover_segments or None,
        )
        warnings.extend(frame_result.get("warnings", []))
        logs.append(f"[pillow] frames={frame_result.get('total_frames', 0)}")

        # 2) FFmpeg 合成静默视频
        exp_dir = get_experiment_dir(request.experiment_id)
        silent_video_path = exp_dir / "silent.mp4"
        frame_sequence = frame_result.get("frameSequence", [])
        duration_by_path = frame_result.get("durationByPath", {})

        if frame_sequence:
            ffmpeg_result = compose_video_from_frame_sequence(
                frame_sequence=frame_sequence,
                output_path=silent_video_path,
                duration_by_path=duration_by_path,
                fps=30,
                resolution=request.resolution,
                timeout=300,
            )
        else:
            ffmpeg_result = compose_video_from_frames(
                frames_dir=get_frames_dir(request.experiment_id),
                output_path=silent_video_path,
                duration_per_frame=frame_result.get("duration_per_frame", {}),
                fps=30,
                resolution=request.resolution,
                timeout=300,
            )

        if not ffmpeg_result.get("success"):
            return VisualRenderResult(
                success=False,
                route_id=self.route_id,
                message=ffmpeg_result.get("message", "FFmpeg silent compose failed"),
                logs=logs,
                warnings=warnings,
            )

        cover = frame_result.get("cover") or ""
        return VisualRenderResult(
            success=True,
            route_id=self.route_id,
            silent_video_path=str(silent_video_path),
            silent_video_url=path_to_url(silent_video_path),
            cover_path=cover,
            cover_url=path_to_url(Path(cover)) if cover else "",
            total_duration_sec=float(frame_result.get("total_duration_sec", 0.0)),
            frame_count=int(frame_result.get("total_frames", 0)),
            logs=logs,
            warnings=warnings,
            extra={
                "visualPreset": frame_result.get("visualPreset"),
                "templateVersion": frame_result.get("templateVersion"),
                "transitionEnabled": frame_result.get("transitionEnabled"),
                "highlightMode": frame_result.get("highlightMode"),
                "params": rp.to_dict(),
            },
        )
