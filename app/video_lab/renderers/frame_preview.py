"""
Frame Preview - 单帧快速预览（调试台地基）

不跑 TTS、不合成视频，只渲染**一张帧**，用于在界面上快速调版式/参数/强调词。
- local_frame_compose (Pillow)：直接渲染单张卡，秒级
- ai_asset_then_compose：生成一张 AI 背景图后叠卡（慢在生图，但远快于整片）
- template_programmatic_render (Remotion)：动效路线，单帧意义有限，返回提示

供 POST /video-lab/frame-preview 调用。
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import get_frames_dir, path_to_url, ensure_runtime_exists
from app.video_lab.renderers.frame_templates import render_cover_template, render_keypoint_template
from app.video_lab.renderers.render_params import resolve_resolution
from app.video_lab.providers.minimax import MiniMaxImageClient


_BG_STYLE = "深蓝科技风格抽象背景，未来感，极简，无文字，电影质感，柔和景深"


def _parse_color(v) -> tuple | None:
    """把 '#RRGGBB' 或 [r,g,b] 解析为 RGB 元组；无效返回 None。"""
    if not v:
        return None
    if isinstance(v, (list, tuple)) and len(v) >= 3:
        return (int(v[0]), int(v[1]), int(v[2]))
    if isinstance(v, str) and v.startswith("#") and len(v) == 7:
        try:
            return (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16))
        except ValueError:
            return None
    return None


def render_single_frame(
    visual_route: str,
    frame_type: str,
    shot: dict[str, Any],
    cover_title: str = "",
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """渲染单帧并返回图片 URL。frame_type: 'cover' | 'keypoint'。"""
    t0 = time.time()
    params = params or {}
    aspect = params.get("aspectRatio", "9:16")
    resolution = resolve_resolution(aspect)
    ensure_runtime_exists()
    exp_id = f"preview_{uuid.uuid4().hex[:8]}"
    frames_dir = get_frames_dir(exp_id)
    warnings: list[str] = []

    headline = (shot.get("headline") or "").strip()
    display = (shot.get("display") or "").strip()
    emphasis = shot.get("emphasisTerms") or None

    # Remotion 是动效路线，单帧不能体现其特点
    if visual_route == "template_programmatic_render":
        return {
            "success": False,
            "route": visual_route,
            "message": "Remotion 的特点是动效（数字滚动/关键词弹出/数据条生长），单帧预览意义有限，请用完整对比查看其动态效果。",
            "elapsedMs": int((time.time() - t0) * 1000),
        }

    # AI 素材路线：先生成背景图（风格提示词可由 params.imageStyle 调）
    bg_path: str | None = None
    if visual_route == "ai_asset_then_compose":
        client = MiniMaxImageClient()
        if client.is_configured():
            topic = headline or cover_title or "AI 前沿"
            style = (params.get("imageStyle") or _BG_STYLE).strip()
            bg = frames_dir / "preview_bg.png"
            r = client.generate(f"{topic}；{style}", bg, aspect_ratio=aspect)
            if r.get("success"):
                bg_path = str(bg)
            else:
                warnings.append(f"AI 背景生成失败，回退渐变：{r.get('providerMessage', '')}")
        else:
            warnings.append("未配置 MINIMAX_API_KEY，AI 背景回退为渐变")

    if frame_type == "cover":
        result = render_cover_template(
            title=cover_title or headline or "AI 前沿资讯",
            subtitle=params.get("subtitle", "今日要点速览"),
            tags=[t for t in [headline] if t][:3] or ["要点一", "要点二", "要点三"],
            date_str=datetime.now().strftime("%Y年%m月%d日"),
            frames_dir=frames_dir,
            resolution=resolution,
            background_path=bg_path,
        )
    elif frame_type == "summary":
        # 总结页：列出回顾要点 + CTA（用于体检总结页排版）
        raw_c = params.get("conclusions")
        if isinstance(raw_c, str):
            conclusions = [ln.strip() for ln in raw_c.splitlines() if ln.strip()]
        elif isinstance(raw_c, list):
            conclusions = [str(c).strip() for c in raw_c if str(c).strip()]
        else:
            conclusions = []
        if not conclusions:
            # 兜底：用标题 + 正文分句
            parts = [headline] + [s.strip() for s in display.replace("。", "。\n").splitlines()]
            conclusions = [p for p in parts if p][:4] or ["要点一", "要点二", "要点三"]
        from app.video_lab.renderers.frame_templates import render_summary_template
        result = render_summary_template(
            conclusions=conclusions[:6],
            cta=params.get("cta") or "适合作为今日 AI 前沿分享模板",
            frames_dir=frames_dir,
            resolution=resolution,
        )
    else:
        # V0.5.0: 预览忠实还原真实出片 —— 应用 themeAdaptive(tone 配色/图标) + showDataViz(数据图)
        from app.video_lab.renderers.theme_presets import resolve_shot_tone, tone_to_style
        from app.video_lab.planners.llm_content_planner import _extract_metrics

        eff_highlight = _parse_color(params.get("highlightColor"))
        eff_icon = params.get("icon", "")
        theme_adaptive = params.get("themeAdaptive", True) not in (False, "false", "False", 0)
        if theme_adaptive:
            preset = tone_to_style(resolve_shot_tone(shot))
            if eff_highlight is None:
                eff_highlight = _parse_color(preset["highlight"])
            if not eff_icon:
                eff_icon = preset["icon"]

        show_data_viz = params.get("showDataViz", True) not in (False, "false", "False", 0)
        metrics = shot.get("metrics")
        if metrics is None and show_data_viz:
            metrics = _extract_metrics(f"{headline} {display}")
        if not show_data_viz:
            metrics = None

        result = render_keypoint_template(
            index=int(params.get("index", 1)),
            total=int(params.get("total", 6)),
            category=params.get("category", ""),
            title=headline,
            body=display,
            source="",
            frames_dir=frames_dir,
            resolution=resolution,
            background_path=bg_path,
            emphasis_terms=emphasis,
            title_color=_parse_color(params.get("titleColor")),
            body_color=_parse_color(params.get("bodyColor")),
            highlight_color=eff_highlight,
            content_align=params.get("contentAlign", "top"),
            icon=eff_icon,
            metrics=metrics,
        )

    warnings.extend(result.get("warnings", []))
    path = result.get("path", "")
    return {
        "success": bool(path),
        "route": visual_route,
        "frameType": frame_type,
        "imageUrl": path_to_url(Path(path)) if path else "",
        "imagePath": str(path) if path else "",
        "warnings": warnings,
        "elapsedMs": int((time.time() - t0) * 1000),
        "resolution": f"{resolution[0]}x{resolution[1]}",
    }


def _ken_burns_clip(image_path: str, out_path: Path, seconds: int, resolution: tuple[int, int], params: dict) -> dict:
    """用 FFmpeg zoompan 把一张静态卡做成 Ken Burns 缓慢缩放 + 淡入的短片。"""
    import subprocess
    w, h = resolution
    frames = max(30, int(seconds * 30))
    zoom_speed = float(params.get("zoomSpeed", 0.0007))
    zoom_max = float(params.get("zoomMax", 1.12))
    fade = max(0.0, float(params.get("fadeInSec", 0.4)))
    # 预放大 2x 再 zoompan，避免抖动；末尾淡入
    vf = (
        f"scale={w*2}:{h*2},"
        f"zoompan=z='min(zoom+{zoom_speed},{zoom_max})':d={frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30,"
        f"fade=t=in:st=0:d={fade},format=yuv420p"
    )
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", image_path,
        "-t", str(seconds), "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path.as_posix(),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not out_path.exists():
            return {"success": False, "message": f"FFmpeg Ken Burns failed: {r.stderr[-200:]}"}
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": f"FFmpeg exception: {e}"}


def render_clip_preview(
    content: str,
    visual_route: str,
    params: dict[str, Any] | None = None,
    clip_seconds: int = 3,
    shot: dict[str, Any] | None = None,
    frame_type: str = "keypoint",
    cover_title: str = "",
) -> dict[str, Any]:
    """渲染一小段（默认 3 秒）动效片段。

    - Remotion：渲染前 clip_seconds 秒的真实动画
    - Pillow / AI 素材：把静态卡做成 Ken Burns（缓慢缩放 + 淡入）动效
    """
    t0 = time.time()
    params = params or {}

    # Pillow / AI 素材：单帧 → Ken Burns 动效片段
    if visual_route in ("local_frame_compose", "ai_asset_then_compose"):
        frame = render_single_frame(visual_route, frame_type, shot or {}, cover_title, params)
        if not frame.get("success") or not frame.get("imagePath"):
            return {"success": False, "route": visual_route,
                    "message": "单帧渲染失败，无法生成动效片段", "elapsedMs": int((time.time() - t0) * 1000)}
        img_path = frame["imagePath"]
        out_path = Path(img_path).parent / "clip.mp4"
        from app.video_lab.renderers.render_params import resolve_resolution
        resolution = resolve_resolution(params.get("aspectRatio", "9:16"))
        kb = _ken_burns_clip(img_path, out_path, clip_seconds, resolution, params)
        if not kb.get("success"):
            return {"success": False, "route": visual_route, "message": kb.get("message", "Ken Burns 失败"),
                    "elapsedMs": int((time.time() - t0) * 1000)}
        return {
            "success": True, "route": visual_route,
            "clipUrl": path_to_url(out_path), "clipSeconds": clip_seconds,
            "effect": "ken_burns", "warnings": frame.get("warnings", []),
            "elapsedMs": int((time.time() - t0) * 1000),
        }

    if visual_route != "template_programmatic_render":
        return {
            "success": False,
            "route": visual_route,
            "message": "该路线暂不支持片段预览。",
            "elapsedMs": int((time.time() - t0) * 1000),
        }

    from app.video_lab.planners.content_structurer import structure_content
    from app.video_lab.planners.llm_content_planner import plan_shots
    from app.video_lab.renderers.remotion.props_builder import build_remotion_props
    from app.video_lab.renderers.remotion.remotion_renderer import render_remotion_video

    max_items = int(params.get("keyPointCount", 4))
    plan = plan_shots(content, max_items=max_items, use_llm=bool(params.get("useLlmPlan", True)))
    kps = []
    for i, s in enumerate(plan.get("shots", []), 1):
        kps.append({
            "index": i,
            "headline": s.get("headline", ""),
            "display": s.get("display", ""),
            "title": s.get("headline", ""),
            "body": s.get("display", ""),
            "emphasisTerms": s.get("emphasisTerms", []),
            "source": "",
            "category": "",
        })
    structured = {"lead": plan.get("coverTitle", "AI 前沿")}
    key_points = {"keyPoints": kps}

    exp_id = f"clip_{uuid.uuid4().hex[:8]}"
    props = build_remotion_props(exp_id, structured, key_points, params)
    fps = 30
    frames = max(30, int(clip_seconds * fps))
    res = render_remotion_video(
        exp_id, props, timeout=240,
        frame_range=f"0-{frames}", output_name="clip.mp4",
    )
    elapsed = int((time.time() - t0) * 1000)
    if res.get("success"):
        return {
            "success": True,
            "route": visual_route,
            "clipUrl": res.get("videoUrl", ""),
            "clipSeconds": clip_seconds,
            "elapsedMs": elapsed,
        }
    return {
        "success": False,
        "route": visual_route,
        "message": res.get("message", "Remotion clip render failed"),
        "warnings": res.get("warnings", []),
        "elapsedMs": elapsed,
    }
