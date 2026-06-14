"""
AiAssetVisualRenderer - AI 素材 + 程序化合成（route_id=ai_asset_then_compose）

方式：用大模型为每条要点生成一张背景图（AI 负责素材），代码把精确文字卡叠在上面
（代码负责控制），再用 FFmpeg 合成静默视频。文字/数字 100% 由代码渲染，信息精确可控。

环境：需 MINIMAX_API_KEY（图像生成）。单条图失败则该帧回退渐变背景，不影响整体。
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
from app.video_lab.providers.minimax import MiniMaxImageClient


_STYLE = "深蓝科技风格抽象背景，未来感，极简，无文字，无文本，电影质感，柔和景深"


class AiAssetVisualRenderer(VisualRenderer):
    route_id = "ai_asset_then_compose"
    display_name = "AI 素材 + 程序化合成"

    def is_available(self) -> tuple[bool, str]:
        if not check_ffmpeg_available():
            return False, "FFmpeg not available"
        if not MiniMaxImageClient().is_configured():
            return False, "MINIMAX_API_KEY not configured (image generation)"
        return True, "MiniMax image + FFmpeg available"

    def render(self, request: VisualRenderRequest) -> VisualRenderResult:
        logs: list[str] = []
        warnings: list[str] = []

        parsed = parse_local_frame_params(request.params or {})
        rp = parsed.params
        warnings.extend(parsed.warnings)

        if not check_ffmpeg_available():
            return VisualRenderResult(success=False, route_id=self.route_id,
                                      message="FFmpeg not available", logs=logs, warnings=warnings)

        img_client = MiniMaxImageClient()
        if not img_client.is_configured():
            return VisualRenderResult(success=False, route_id=self.route_id,
                                      message="MINIMAX_API_KEY not configured", logs=logs, warnings=warnings)

        exp_dir = get_experiment_dir(request.experiment_id)
        bg_dir = exp_dir / "ai_backgrounds"
        bg_dir.mkdir(parents=True, exist_ok=True)
        aspect = rp.aspect_ratio if rp.aspect_ratio in ("9:16", "16:9", "1:1") else "9:16"

        kps = request.key_points.get("keyPoints") or request.key_points.get("key_points") or []

        # 1) 生成背景图（封面 + 每条要点）
        backgrounds: dict = {}
        cover_topic = (request.structured.get("lead") or "AI 前沿").strip()
        cover_prompt = f"{cover_topic}；{_STYLE}"
        cover_path = bg_dir / "cover_bg.png"
        res = img_client.generate(cover_prompt, cover_path, aspect_ratio=aspect)
        if res.get("success"):
            backgrounds["cover"] = str(cover_path)
        else:
            warnings.append(f"cover image failed: {res.get('providerMessage')}")

        for i, kp in enumerate(kps, 1):
            topic = (kp.get("headline") or kp.get("title") or "").strip()
            prompt = f"{topic}；{_STYLE}"
            p = bg_dir / f"kp_{i}_bg.png"
            r = img_client.generate(prompt, p, aspect_ratio=aspect)
            if r.get("success"):
                backgrounds[i] = str(p)
            else:
                warnings.append(f"kp{i} image failed: {r.get('providerMessage')}")
        logs.append(f"[ai_asset] generated {len(backgrounds)} background images")

        # 2) 生成帧（复用卡片模板，叠精确文字）
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
            backgrounds=backgrounds,
        )
        warnings.extend(frame_result.get("warnings", []))

        # 3) FFmpeg 合成静默视频
        silent_video_path = exp_dir / "silent.mp4"
        frame_sequence = frame_result.get("frameSequence", [])
        duration_by_path = frame_result.get("durationByPath", {})
        if frame_sequence:
            ffmpeg_result = compose_video_from_frame_sequence(
                frame_sequence=frame_sequence, output_path=silent_video_path,
                duration_by_path=duration_by_path, fps=30, resolution=request.resolution, timeout=300,
            )
        else:
            ffmpeg_result = compose_video_from_frames(
                frames_dir=get_frames_dir(request.experiment_id), output_path=silent_video_path,
                duration_per_frame=frame_result.get("duration_per_frame", {}), fps=30,
                resolution=request.resolution, timeout=300,
            )

        if not ffmpeg_result.get("success"):
            return VisualRenderResult(success=False, route_id=self.route_id,
                                      message=ffmpeg_result.get("message", "FFmpeg silent compose failed"),
                                      logs=logs, warnings=warnings)

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
            extra={"backgroundsGenerated": len(backgrounds), "params": rp.to_dict()},
        )
