"""
RemotionVisualRenderer - 程序化模板视觉路线（route_id=template_programmatic_render）

方式：用 structured + key_points 构建 Remotion props，调用 `npx remotion render`
直接产出静默 MP4。环境（Node.js + remotion）缺失时优雅返回 success=False。
"""

from pathlib import Path

from app.video_lab.renderers.visual.base import (
    VisualRenderer,
    VisualRenderRequest,
    VisualRenderResult,
)
from app.video_lab.renderers.remotion.props_builder import build_remotion_props
from app.video_lab.renderers.remotion.remotion_renderer import (
    render_remotion_video,
    check_remotion_available,
)


class RemotionVisualRenderer(VisualRenderer):
    route_id = "template_programmatic_render"
    display_name = "Remotion 程序化模板"

    def is_available(self) -> tuple[bool, str]:
        return check_remotion_available()

    def render(self, request: VisualRenderRequest) -> VisualRenderResult:
        logs: list[str] = []
        warnings: list[str] = []

        available, msg = check_remotion_available()
        if not available:
            return VisualRenderResult(
                success=False,
                route_id=self.route_id,
                message=msg,
                logs=[f"[remotion] {msg}"],
                warnings=[msg],
            )

        props = build_remotion_props(
            experiment_id=request.experiment_id,
            structured=request.structured,
            key_points=request.key_points,
            params=request.params or {},
            segment_durations=request.voiceover_segments or None,
        )

        render_result = render_remotion_video(
            experiment_id=request.experiment_id,
            props=props,
            timeout=int(request.params.get("remotionTimeout", 300)) if request.params else 300,
        )
        logs.extend(render_result.get("logs", []))
        warnings.extend(render_result.get("warnings", []))

        if not render_result.get("success"):
            return VisualRenderResult(
                success=False,
                route_id=self.route_id,
                message=render_result.get("message", "Remotion render failed"),
                logs=logs,
                warnings=warnings,
            )

        video_url = render_result.get("videoUrl", "")
        silent_path = self._url_to_path(video_url)

        return VisualRenderResult(
            success=True,
            route_id=self.route_id,
            silent_video_path=silent_path,
            silent_video_url=video_url,
            total_duration_sec=float(props.get("durationSec", request.target_duration_sec)),
            logs=logs,
            warnings=warnings,
            extra={
                "engine": "remotion",
                "stylePreset": props.get("stylePreset"),
                "durationSec": props.get("durationSec"),
            },
        )

    @staticmethod
    def _url_to_path(video_url: str) -> str:
        """Convert a runtime URL back to a filesystem path.

        用 config 的 RUNTIME_DIR / PUBLIC_RUNTIME_URL_PREFIX，与 path_to_url 保持一致；
        旧实现写死 "/runtime/" + 相对 Path("runtime")，在自定义/绝对 RUNTIME_DIR 或换目录时会算错。
        """
        if not video_url:
            return ""
        # 统一走 path_contract（单一真相），兼容自定义 RUNTIME_DIR / 历史前缀
        from app.video_lab.path_contract import runtime_url_to_path
        return str(runtime_url_to_path(video_url))
