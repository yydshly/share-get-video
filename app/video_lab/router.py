"""
Video Capability Lab - FastAPI Router
"""

from typing import Any
from fastapi import APIRouter, HTTPException

from app.video_lab.models import VideoTestCase, VideoMethod, VideoExperimentResult, VideoExperimentEvaluation
from app.video_lab.seed_data import SEED_TEST_CASES, SEED_VIDEO_METHODS, get_test_case_by_id, get_method_by_id
from app.video_lab.advisor import getVideoMethodAdvice, get_all_advice
from app.video_lab.experiment_runner import get_runner
from app.video_lab.schemas import CreateExperimentRequest, SaveEvaluationRequest, CreateBenchmarkRequest, CreateChainBenchmarkRequest, VisualComposeRequest, FramePreviewRequest, ClipPreviewRequest, VisualJudgeRequest, StyleSampleGenerateRequest, StyleSampleSaveRequest, StyleFamilyCompareRequest, TechniqueProbeRequest, StyleSweepRequest
from app.video_lab.config import PUBLIC_RUNTIME_URL_PREFIX
from app.video_lab.path_contract import runtime_url_to_path


router = APIRouter(prefix="/video-lab", tags=["VideoLab"])


# ─────────────────────────────────────────────
# Shared helpers (also usable in tests)
# ─────────────────────────────────────────────
def _safe_get(obj, name: str, default=None):
    """Access attribute or dict key, handling None gracefully."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _artifact_type_value(artifact) -> str:
    """Normalize artifact type: enum.value or string."""
    raw = _safe_get(artifact, "type", "")
    return getattr(raw, "value", raw) or ""


def _strip_runtime_url_prefix(url: str) -> str:
    """
    Strip the PUBLIC_RUNTIME_URL_PREFIX from a URL to get the stored path.

    Examples:
      "/runtime/video_lab/x.mp4" → "video_lab/x.mp4"
      "/assets/video_lab/x.mp4"  → "video_lab/x.mp4"
      ""                        → ""
    """
    if not url:
        return ""
    prefix = PUBLIC_RUNTIME_URL_PREFIX.rstrip("/")
    if prefix and url.startswith(prefix + "/"):
        return url[len(prefix) + 1:]
    if url.startswith("/runtime/"):
        return url[len("/runtime/"):]
    return url.lstrip("/")


def extract_style_sample_assets(result) -> dict[str, str]:
    """
    Extract URL assets from a VideoExperimentResult (or any object/dict with
    the same field layout).

    Returns dict with keys: final_video_url, cover_url, audio_url, srt_url,
    manifest_url, duration_sec, audio_duration_sec, failed, failed_reason.
    """
    raw = _safe_get(result, "rawOutput", {}) or {}
    assets = _safe_get(result, "assets", {}) or {}

    final_video_url = _safe_get(result, "videoUrl", "") or ""
    cover_url = _safe_get(result, "coverUrl", "") or ""
    audio_url = ""
    srt_url = ""
    manifest_url = ""

    duration_sec = float(assets.get("durationSec", 0) or 0)
    audio_duration_sec = float(assets.get("audioDurationSec", 0) or 0)

    steps = _safe_get(result, "productionSteps", []) or []

    for step in steps:
        artifacts = _safe_get(step, "artifacts", []) or []
        for art in artifacts:
            atype = _artifact_type_value(art)
            payload = _safe_get(art, "payload", {}) or {}
            url = _safe_get(payload, "url", "") if isinstance(payload, dict) else ""
            if not url:
                continue

            if atype == "video_output" and not final_video_url:
                final_video_url = url
            elif atype == "cover_image" and not cover_url:
                cover_url = url
            elif atype == "audio_output" and not audio_url:
                audio_url = url
            elif atype == "subtitle_file" and not srt_url:
                srt_url = url
            elif atype == "manifest" and not manifest_url:
                manifest_url = url

    status_ok = raw.get("status") == "succeeded"
    failed = not status_ok

    if status_ok and not final_video_url:
        failed = True
        failed_reason = raw.get("error") or "生成成功但无法提取 final_video_url，请检查 productionSteps 中 video_output artifact"
    else:
        failed_reason = raw.get("error") or ("生成失败" if failed else "")

    return {
        "final_video_url": final_video_url,
        "cover_url": cover_url,
        "audio_url": audio_url,
        "srt_url": srt_url,
        "manifest_url": manifest_url,
        "duration_sec": duration_sec,
        "audio_duration_sec": audio_duration_sec,
        "failed": failed,
        "failed_reason": failed_reason,
    }


# ─────────────────────────────────────────────
# 测试用例
# ─────────────────────────────────────────────
@router.get("/test-cases")
def list_test_cases() -> list[dict[str, Any]]:
    return [tc.to_dict() for tc in SEED_TEST_CASES]


@router.get("/test-cases/{case_id}")
def get_test_case(case_id: str) -> dict[str, Any]:
    tc = get_test_case_by_id(case_id)
    if not tc:
        raise HTTPException(status_code=404, detail=f"Test case not found: {case_id}")
    return tc.to_dict()


# ─────────────────────────────────────────────
# 生成方案
# ─────────────────────────────────────────────
@router.get("/methods")
def list_methods() -> list[dict[str, Any]]:
    return [m.to_dict() for m in SEED_VIDEO_METHODS]


@router.get("/methods/{method_id}")
def get_method(method_id: str) -> dict[str, Any]:
    m = get_method_by_id(method_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Method not found: {method_id}")
    return m.to_dict()


# ─────────────────────────────────────────────
# 实验
# ─────────────────────────────────────────────
@router.post("/experiments")
def create_experiment(request: CreateExperimentRequest) -> dict[str, Any]:
    """
    Create and immediately run an experiment.

    Returns HTTP 200 with experiment+result on success (even if experiment.status == "failed").
    Returns HTTP 400 if testCaseId or methodId is unknown.
    Returns HTTP 422 if request body is malformed.
    Returns HTTP 500 on unexpected server errors.
    """
    runner = get_runner()

    # 验证 testCaseId
    tc = get_test_case_by_id(request.testCaseId)
    if not tc:
        raise HTTPException(status_code=400, detail=f"Unknown test case: {request.testCaseId}")

    # 验证 methodId
    m = get_method_by_id(request.methodId)
    if not m:
        raise HTTPException(status_code=400, detail=f"Unknown method: {request.methodId}")

    experiment = runner.create_experiment(
        test_case_id=request.testCaseId,
        method_id=request.methodId,
        title=request.title,
        input_payload=request.inputPayload,
        params=request.params,
    )

    try:
        result = runner.run_experiment(experiment.id)
        return {
            "experiment": experiment.to_dict(),
            "result": result.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments")
def list_experiments() -> list[dict[str, Any]]:
    runner = get_runner()
    return [e.to_dict() for e in runner.list_experiments()]


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict[str, Any]:
    runner = get_runner()
    exp = runner.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")

    result = runner.get_result(experiment_id)
    resp = {"experiment": exp.to_dict()}
    if result:
        resp["result"] = result.to_dict()
    return resp


@router.get("/experiments-by-test-case/{test_case_id}")
def get_experiments_by_test_case(test_case_id: str) -> dict[str, Any]:
    """按测试用例分组展示实验结果"""
    runner = get_runner()
    experiments = runner.get_experiments_by_test_case(test_case_id)

    tc = get_test_case_by_id(test_case_id)
    results = []
    for e in experiments:
        r = runner.get_result(e.id)
        results.append({
            "experiment": e.to_dict(),
            "result": r.to_dict() if r else None,
        })

    return {
        "testCase": tc.to_dict() if tc else None,
        "experiments": results,
    }


# ─────────────────────────────────────────────
# 人工评分
# ─────────────────────────────────────────────
@router.post("/experiments/{experiment_id}/evaluation")
def save_evaluation(experiment_id: str, request: SaveEvaluationRequest) -> dict[str, Any]:
    """
    Save a human evaluation for an experiment.
    Returns HTTP 404 if the experiment does not exist.
    """
    runner = get_runner()
    exp = runner.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")

    evaluation = VideoExperimentEvaluation(
        experimentId=experiment_id,
        informationAccuracy=request.informationAccuracy,
        readability=request.readability,
        visualQuality=request.visualQuality,
        pacing=request.pacing,
        shareability=request.shareability,
        stability=request.stability,
        productizationValue=request.productizationValue,
        notes=request.notes,
    )
    runner.save_evaluation(evaluation)
    return evaluation.to_dict()


@router.get("/experiments/{experiment_id}/evaluation")
def get_evaluation(experiment_id: str) -> dict[str, Any]:
    """
    Get the human evaluation for an experiment.
    Returns HTTP 404 if no evaluation has been saved.
    """
    runner = get_runner()
    evaluation = runner.get_evaluation(experiment_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"No evaluation found for experiment: {experiment_id}")
    return evaluation.to_dict()


# ─────────────────────────────────────────────
# 总结建议
# ─────────────────────────────────────────────
@router.get("/advice/{test_case_id}")
def get_advice(test_case_id: str) -> dict[str, Any]:
    advice = getVideoMethodAdvice(test_case_id)
    if not advice:
        raise HTTPException(status_code=404, detail=f"No advice for test case: {test_case_id}")
    return advice.to_dict()


@router.get("/advice")
def list_all_advice() -> list[dict[str, Any]]:
    return [a.to_dict() for a in get_all_advice()]


# ─────────────────────────────────────────────
# Route Benchmark
# ─────────────────────────────────────────────
@router.get("/routes")
def list_routes() -> list[dict[str, Any]]:
    """List all available benchmark routes."""
    from app.video_lab.routes_benchmark.registry import list_routes as _list_routes
    return _list_routes()


@router.post("/route-benchmarks")
def create_benchmark(request: CreateBenchmarkRequest) -> dict[str, Any]:
    """
    Create and run a multi-route benchmark.

    Returns benchmark results for all specified routes.
    """
    from app.video_lab.routes_benchmark.registry import get_route_by_id
    from app.video_lab.routes_benchmark.runner import get_runner

    # Validate all route IDs
    invalid_routes = []
    for rid in request.routeIds:
        if get_route_by_id(rid) is None:
            invalid_routes.append(rid)

    if invalid_routes:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown route IDs: {invalid_routes}",
        )

    runner = get_runner()

    # Create and run benchmark
    benchmark = runner.create_benchmark(
        test_case_id=request.testCaseId,
        title=request.title,
        input_payload=request.inputPayload,
        common_params=request.commonParams,
        route_ids=request.routeIds,
    )

    # Execute
    result = runner.run_benchmark(benchmark.benchmark_id)

    return result.to_dict()


@router.get("/route-benchmarks/{benchmark_id}")
def get_benchmark(benchmark_id: str) -> dict[str, Any]:
    """Get a benchmark result by ID."""
    from app.video_lab.routes_benchmark.runner import get_runner

    runner = get_runner()
    benchmark = runner.get_benchmark(benchmark_id)

    if not benchmark:
        raise HTTPException(
            status_code=404,
            detail=f"Benchmark not found: {benchmark_id}",
        )

    return benchmark.to_dict()


# ─────────────────────────────────────────────
# Visual Routes (pluggable visual renderers)
# ─────────────────────────────────────────────
@router.get("/visual-routes")
def list_visual_routes() -> list[dict[str, Any]]:
    """List all pluggable visual rendering routes and their availability.

    A chain can switch its visual layer by passing params.visualRoute = routeId.
    """
    from app.video_lab.renderers.visual import list_visual_renderers
    return list_visual_renderers()


@router.post("/frame-preview")
def frame_preview(request: FramePreviewRequest) -> dict[str, Any]:
    """单帧快速预览（调试台）：渲染一张帧，秒级返回，用于调版式/参数/强调词。

    不跑 TTS、不合成视频。Remotion 路线返回提示（动效路线单帧无意义）。
    """
    from app.video_lab.renderers.frame_preview import render_single_frame
    try:
        return render_single_frame(
            visual_route=request.visualRoute,
            frame_type=request.frameType,
            shot=request.shot,
            cover_title=request.coverTitle,
            params=request.params,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual-judge")
def visual_judge(request: VisualJudgeRequest) -> dict[str, Any]:
    """视觉模型感知评分：把画面交给多模态大模型，评 排版/可读性/层级/美观 + 改进建议。

    支持图片；若传入视频(.mp4)则自动抽取中间一帧再评。
    """
    import subprocess
    import uuid
    from pathlib import Path
    from app.video_lab.quality.visual_judge import assess_visual_quality

    url = request.imageUrl
    local = runtime_url_to_path(url)
    if not local.exists():
        raise HTTPException(status_code=404, detail=f"file not found: {local}")

    # 视频：均匀抽多帧，综合评整片（封面/关键点/结尾）
    judge_paths: list[str] = [str(local)]
    if local.suffix.lower() in (".mp4", ".webm", ".mov"):
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", local.as_posix()],
                capture_output=True, text=True, timeout=30,
            )
            duration = float((probe.stdout or "0").strip() or 0)
        except Exception:
            duration = 0.0
        fractions = [0.08, 0.35, 0.62, 0.88]
        tag = uuid.uuid4().hex[:6]
        judge_paths = []
        for i, fr in enumerate(fractions):
            t = max(0.0, duration * fr) if duration > 0 else i * 1.5
            fp = local.parent / f"judge_{tag}_{i}.png"
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", local.as_posix(),
                     "-vframes", "1", fp.as_posix()],
                    capture_output=True, timeout=60,
                )
            except Exception:
                continue
            if fp.exists():
                judge_paths.append(str(fp))
        if not judge_paths:
            raise HTTPException(status_code=500, detail="failed to extract frames from video")

    result = assess_visual_quality(judge_paths)

    # 感知层评分留痕（仅当提供 route 且评分成功）
    if request.route and result.get("success"):
        try:
            from app.video_lab.quality.quality_log import append_record
            append_record({
                "kind": "perceptual",
                "route": request.route,
                "overall": result.get("overall"),
                "dimensions": result.get("scores", {}),
                "imageUrl": request.imageUrl,
            })
        except Exception:
            pass

    return result


@router.get("/quality-history")
def quality_history(route: str = "", kind: str = "", limit: int = 300) -> list[dict[str, Any]]:
    """读取质量评分历史（可按 route / kind 过滤）。"""
    from app.video_lab.quality.quality_log import read_records
    return read_records(route=route or None, kind=kind or None, limit=limit)


@router.get("/quality-summary")
def quality_summary() -> dict[str, Any]:
    """按路线聚合：每条路线各类评分的最新值 + 趋势（delta）。"""
    from app.video_lab.quality.quality_log import summarize_by_route
    return summarize_by_route()


@router.post("/clip-preview")
def clip_preview(request: ClipPreviewRequest) -> dict[str, Any]:
    """渲染一小段（~3s）动效片段。

    - Remotion：渲染前几秒真实动画
    - Pillow / AI 素材：Ken Burns（缓慢缩放 + 淡入）
    """
    from app.video_lab.renderers.frame_preview import render_clip_preview
    try:
        return render_clip_preview(
            content=request.content,
            visual_route=request.visualRoute,
            params=request.params,
            clip_seconds=int((request.params or {}).get("clipSeconds", 3)),
            shot=request.shot,
            frame_type=request.frameType,
            cover_title=request.coverTitle,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/style-family/compare")
def style_family_compare(request: StyleFamilyCompareRequest) -> dict[str, Any]:
    """对比 Data News vs Card Stack 两种 Remotion 表现范式的实际效果。

    V0.6.4: 让用户在 UI 中直接看到两者的实际 preview 视频或抽帧。
    不做数据库，不做历史记录，只返回当前渲染结果。
    """
    from app.video_lab.renderers.frame_preview import render_clip_preview
    import time
    t0 = time.time()

    default_content = (
        "科学研究评审实现突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%。\n"
        "依据：依据 1\n"
        "购物AI助手落后：主流模型通过率仅57-77%。\n"
        "依据：依据 1\n"
        "企业级AI加速落地：Anthropic与TCS合作，DeepMind投资千万美元。\n"
        "依据：依据 1"
    )
    content = request.content.strip() or default_content
    params = dict(request.params or {})
    params["visualRoute"] = "template_programmatic_render"
    clip_seconds = int(params.get("clipSeconds", 3))
    key_point_count = int(params.get("keyPointCount", 3))

    # Render Data News
    dn_params = {**params, "remotionFamily": "data_news", "keyPointCount": key_point_count}
    dn_result = render_clip_preview(
        content=content,
        visual_route="template_programmatic_render",
        params=dn_params,
        clip_seconds=clip_seconds,
    )

    # Render Card Stack
    cs_params = {**params, "remotionFamily": "card_stack", "keyPointCount": key_point_count}
    cs_result = render_clip_preview(
        content=content,
        visual_route="template_programmatic_render",
        params=cs_params,
        clip_seconds=clip_seconds,
    )

    elapsed = int((time.time() - t0) * 1000)

    def parse_result(r: dict) -> dict:
        return {
            "experimentId": r.get("experimentId", ""),
            "success": r.get("success", False),
            "videoUrl": r.get("clipUrl", ""),
            "clipSeconds": r.get("clipSeconds", clip_seconds),
            "elapsedMs": r.get("elapsedMs", 0),
            "message": r.get("message", ""),
            "warnings": r.get("warnings", []),
        }

    return {
        "dataNews": parse_result(dn_result),
        "cardStack": parse_result(cs_result),
        "totalElapsedMs": elapsed,
    }


def _run_visual_compose(content: str, visual_route: str, params_in: dict | None) -> dict[str, Any]:
    """Run ONE visual route end-to-end (LLM plan + TTS + 字幕 + 合成) and return a
    UI-ready result dict (finalVideoUrl + coverUrl + quality + steps).

    复用方：POST /visual-compose（单路线）与 POST /technique-probe（多路线探测）。
    Business failures 不抛异常，以 status='failed' + failedReason 返回。
    """
    import uuid
    from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose

    exp_id = f"web_{visual_route}_{uuid.uuid4().hex[:8]}"
    params = dict(params_in or {})
    params["visualRoute"] = visual_route

    result = run_tts_subtitle_compose(
        experiment_id=exp_id,
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": content},
        params=params,
    )

    raw = getattr(result, "rawOutput", {}) or {}
    assets = getattr(result, "assets", {}) or {}
    status = raw.get("status", "unknown")
    failed_reason = ""
    if status != "succeeded":
        for step in getattr(result, "productionSteps", []):
            if getattr(step, "status", None) and step.status.value == "failed":
                failed_reason = step.outputSummary or step.name
                break
        failed_reason = failed_reason or raw.get("error", "")

    audio_url = srt_url = manifest_url = ""
    steps_summary = []
    for step in getattr(result, "productionSteps", []):
        steps_summary.append({
            "name": step.name,
            "status": step.status.value if getattr(step, "status", None) else "",
            "output": step.outputSummary or "",
        })
        for art in getattr(step, "artifacts", []):
            payload = art.payload if hasattr(art, "payload") else {}
            if art.type.value == "manifest":
                audio_url = audio_url or payload.get("audioUrl", "")
                srt_url = srt_url or payload.get("srtUrl", "")
                manifest_url = manifest_url or payload.get("manifestUrl", "")

    try:
        from app.video_lab.quality.quality_log import append_record
        _q = raw.get("quality", {}) or {}
        append_record({
            "kind": "structural",
            "route": visual_route,
            "experimentId": exp_id,
            "status": status,
            "overall": _q.get("overallScore"),
            "dimensions": _q.get("dimensionScores", {}),
            "durationSec": assets.get("audioDurationSec", 0),
            "subtitleCount": assets.get("subtitleCount", 0),
            "contentChars": len(content),
            "params": params,
        })
    except Exception:
        pass

    return {
        "experimentId": exp_id,
        "visualRoute": visual_route,
        "status": status,
        "params": params,
        "finalVideoUrl": getattr(result, "videoUrl", "") or "",
        "coverUrl": getattr(result, "coverUrl", "") or "",
        "audioUrl": audio_url,
        "srtUrl": srt_url,
        "manifestUrl": manifest_url,
        "audioDurationSec": assets.get("audioDurationSec", 0),
        "subtitleCount": assets.get("subtitleCount", 0),
        "quality": raw.get("quality", {}),
        "failedReason": failed_reason,
        "warnings": raw.get("warnings", []),
        "steps": steps_summary,
        "logs": getattr(result, "logs", []) or [],
    }


@router.post("/visual-compose")
def visual_compose(request: VisualComposeRequest) -> dict[str, Any]:
    """Run ONE visual route end-to-end (LLM plan + TTS + 字幕 + 合成) and return
    the final video URL + auto quality report. Frontend calls this per route.

    Synchronous: returns after the video is produced (TTS/render may take minutes).
    Business failures return HTTP 200 with status='failed' + failedReason.
    """
    try:
        return _run_visual_compose(request.content, request.visualRoute, request.params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/technique-probe")
def technique_probe(request: TechniqueProbeRequest) -> dict[str, Any]:
    """最佳技术探测：一份内容 → 多路线各出整片 → 统一质量分排名 → 推荐路线。

    同步执行：会依次跑每条路线的完整出片(TTS/渲染/合成)，可能数分钟。
    单条路线失败不影响其它路线，整体仍返回排名（失败项排末尾）。
    """
    from app.video_lab.technique_probe import run_technique_probe

    try:
        return run_technique_probe(
            content=request.content,
            routes=request.routes or None,
            params=request.params,
            compose_fn=_run_visual_compose,
            judge_fn=_judge_probe_result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/style-sweep")
def style_sweep(request: StyleSweepRequest) -> dict[str, Any]:
    """样式对比：选一条技术路线 → 用同一内容把它的每个预置样式各出一片 → 并排返回。

    同步执行：每个样式都跑完整出片(TTS/渲染/合成)，N 个样式约 N 倍耗时。
    单样式失败不影响其它样式，整批仍返回。
    """
    from app.video_lab.style_sweep import run_style_sweep

    try:
        return run_style_sweep(
            content=request.content,
            route_id=request.routeId,
            params=request.params,
            render_fn=_run_visual_compose,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _judge_probe_result(result: dict[str, Any]) -> dict[str, Any] | None:
    """对一条路线的成片抽帧做视觉感知评分，供探测综合排名用。

    成片是 mp4 → 先抽一帧再评分（assess_visual_quality 接受图片帧）。
    任何失败返回 None（该路线退化为纯结构分排名，不中断探测）。
    """
    from app.video_lab.quality.visual_judge import assess_visual_quality

    url = result.get("finalVideoUrl") or result.get("coverUrl") or ""
    if not url:
        return None
    # Use runtime_url_to_path for proper URL → local path conversion
    fs_path = runtime_url_to_path(url)

    if str(fs_path).endswith(".mp4"):
        # 多帧送评：封面/中段/结尾各抽一帧，给视觉模型更多区分信号（并触发 consistency 维度）
        frames = [f for f in (_extract_video_frame(str(fs_path), fr) for fr in (0.06, 0.45, 0.85)) if f]
    else:
        frames = [str(fs_path)]
    if not frames:
        return None
    j = assess_visual_quality(frames)
    if not j.get("success"):
        return None
    return {"visualScore": j.get("overall"), "visualDimensions": j.get("scores", {})}


# ─────────────────────────────────────────────
# Chain Benchmarks
# ─────────────────────────────────────────────
@router.get("/chains")
def list_chains() -> list[dict[str, Any]]:
    """List all available complete video generation chains."""
    from app.video_lab.chains.registry import list_chains as _list_chains
    return [c.to_dict() for c in _list_chains()]


@router.post("/chain-benchmarks")
def create_chain_benchmark(request: CreateChainBenchmarkRequest) -> dict[str, Any]:
    """
    Create and run a multi-chain benchmark.

    Returns benchmark results for all specified chains.
    Each chain produces a finalVideoUrl or manual_required status.
    """
    from app.video_lab.chains.registry import get_chain

    # Validate all chain IDs
    invalid_chains = []
    for cid in request.chainIds:
        if get_chain(cid) is None:
            invalid_chains.append(cid)

    if invalid_chains:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown chain IDs: {invalid_chains}",
        )

    from app.video_lab.routes_benchmark.chain_runner import get_chain_runner as _get_chain_runner
    runner = _get_chain_runner()

    # Create and run benchmark
    benchmark = runner.create_benchmark(
        test_case_id=request.testCaseId,
        title=request.title,
        input_payload=request.inputPayload,
        common_params=request.commonParams,
        chain_ids=request.chainIds,
    )

    # Execute
    result = runner.run_benchmark(benchmark.benchmark_id)

    return result.to_dict()


@router.get("/chain-benchmarks/{benchmark_id}")
def get_chain_benchmark(benchmark_id: str) -> dict[str, Any]:
    """Get a chain benchmark result by ID."""
    from app.video_lab.routes_benchmark.chain_runner import get_chain_runner as _get_chain_runner
    runner = _get_chain_runner()
    benchmark = runner.get_benchmark(benchmark_id)

    if not benchmark:
        raise HTTPException(
            status_code=404,
            detail=f"Chain benchmark not found: {benchmark_id}",
        )

    return benchmark.to_dict()


# ─────────────────────────────────────────────
# Style Sample Gallery
# V0.3.7: 风格样片库 — 无数据库，JSONL 存储
# ─────────────────────────────────────────────

@router.get("/style-samples")
def list_style_samples(
    route_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    列出风格样片。

    Query params:
    - route_id: 按路线过滤（如 local_frame_compose）
    - status: 按状态过滤（candidate / approved / rejected / comparing）
    - limit: 返回数量上限，默认 50
    """
    from app.video_lab.style_gallery import store as sg_store
    samples = sg_store.list_samples(route_id=route_id, status=status, limit=limit)
    out = []
    for s in samples:
        d = s.to_dict()
        urls = sg_store.resolve_sample_urls(s)
        d["urls"] = urls
        out.append(d)
    return out


@router.post("/style-samples/generate")
def generate_style_sample(request: StyleSampleGenerateRequest) -> dict[str, Any]:
    """
    生成一条风格样片。

    调用现有的 visual-compose 链路，用指定的路线和参数生成视频，
    返回生成的样片信息（不含持久化记录）。
    """
    import uuid
    from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
    from app.video_lab.renderers.visual.registry import get_visual_renderer

    renderer = get_visual_renderer(request.route_id)
    if not renderer:
        raise HTTPException(status_code=400, detail=f"Unknown route_id: {request.route_id}")

    available, msg = renderer.is_available()
    if not available:
        raise HTTPException(status_code=400, detail=f"Route not available: {msg}")

    content = request.content.strip() or (
        "今日 AI 前沿呈现多条并行进展：多语言 NLP 在低资源方言取得突破，"
        "AI 评估体系向多维化演进，安全对齐方面新范式推动可扩展监督研究，企业级 AI 落地加速。"
    )

    sample_id = f"sample_{request.route_id}_{uuid.uuid4().hex[:8]}"
    exp_id = f"sg_{uuid.uuid4().hex[:8]}"

    params = dict(request.params)
    params["visualRoute"] = request.route_id

    try:
        result = run_tts_subtitle_compose(
            experiment_id=exp_id,
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": content},
            params=params,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ── extract URLs and build response ─────────────────────────────────────────
    extracted = extract_style_sample_assets(result)

    return {
        "sample_id": sample_id,
        "route_id": request.route_id,
        "style_name": request.style_name,
        "description": request.description,
        "status": "generated" if not extracted["failed"] else "failed",
        "params": params,
        "output": {
            "type": "mp4",
            "path": _strip_runtime_url_prefix(extracted["final_video_url"]),
            "poster": _strip_runtime_url_prefix(extracted["cover_url"]),
            "audio_url": _strip_runtime_url_prefix(extracted["audio_url"]),
            "srt_url": _strip_runtime_url_prefix(extracted["srt_url"]),
            "manifest_url": _strip_runtime_url_prefix(extracted["manifest_url"]),
        },
        "duration_sec": extracted["duration_sec"],
        "audio_duration_sec": extracted["audio_duration_sec"],
        "content_preview": content[:100],
        "final_video_url": extracted["final_video_url"],
        "cover_url": extracted["cover_url"],
        "audio_url": extracted["audio_url"],
        "srt_url": extracted["srt_url"],
        "manifest_url": extracted["manifest_url"],
        "failed": extracted["failed"],
        "failed_reason": extracted["failed_reason"],
    }


@router.post("/style-samples")
def save_style_sample(request: StyleSampleSaveRequest) -> dict[str, Any]:
    """保存一条风格样片记录到 JSONL。"""
    import uuid
    from datetime import datetime
    from app.video_lab.style_gallery.models import (
        StyleSample, SampleStatus, StyleSampleOutput, EvaluationScore,
    )
    from app.video_lab.style_gallery import store as sg_store

    sample_id = request.id or f"sample_{uuid.uuid4().hex[:8]}"
    valid_statuses = [s.value for s in SampleStatus]
    status = SampleStatus(request.status) if request.status in valid_statuses else SampleStatus.CANDIDATE

    eval_score = EvaluationScore(
        readability=request.evaluation_readability,
        motion=request.evaluation_motion,
        visual_impact=request.evaluation_visual_impact,
        stability=request.evaluation_stability,
        cost=request.evaluation_cost,
        notes=request.evaluation_notes,
    )

    output = StyleSampleOutput(
        type=request.output_type or "mp4",
        path=request.output_path,
        poster=request.poster_path,
        audio_url=request.audio_url,
        srt_url=request.srt_url,
        manifest_url=request.manifest_url,
    )

    sample = StyleSample(
        id=sample_id,
        route_id=request.route_id,
        route_name=request.route_name,
        style_name=request.style_name,
        description=request.description,
        status=status,
        params=request.params,
        output=output,
        evaluation=eval_score,
        tags=request.tags or [],
        content_preview=request.content_preview,
        duration_sec=request.duration_sec,
        audio_duration_sec=request.audio_duration_sec,
        created_at=datetime.utcnow(),
    )

    sg_store.save_sample(sample)
    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


@router.get("/style-samples/{sample_id}")
def get_style_sample(sample_id: str) -> dict[str, Any]:
    """获取单条样片详情。"""
    from app.video_lab.style_gallery import store as sg_store
    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")
    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


@router.delete("/style-samples/{sample_id}")
def delete_style_sample(sample_id: str) -> dict[str, Any]:
    """删除一条风格样片记录（不删除文件）。"""
    from app.video_lab.style_gallery import store as sg_store
    deleted = sg_store.delete_sample(sample_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")
    return {"deleted": sample_id}


@router.post("/style-samples/{sample_id}/compare")
def mark_sample_for_compare(sample_id: str) -> dict[str, Any]:
    """将样片标记为 comparing 状态，加入对比队列。"""
    from app.video_lab.style_gallery import store as sg_store
    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")
    sample.status = SampleStatus.COMPARING
    sg_store.save_sample(sample)
    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


@router.post("/style-samples/{sample_id}/status")
def update_sample_status(sample_id: str, request: dict[str, str]) -> dict[str, Any]:
    """更新样片状态。

    支持的状态：candidate / comparing / approved / rejected
    """
    from app.video_lab.style_gallery import store as sg_store
    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")

    new_status = request.get("status", "")
    valid_statuses = [s.value for s in SampleStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    sample.status = SampleStatus(new_status)
    sg_store.save_sample(sample)
    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


def _extract_video_frame(video_path: str, fraction: float = 0.4) -> str | None:
    """从视频抽取一帧用于视觉评分（assess_visual_quality 适合图片/帧，不适合 mp4）。

    在视频 fraction 处抽一帧；无法取时长则用 1.5s。失败返回 None。
    """
    import subprocess
    import uuid
    from pathlib import Path

    vp = Path(video_path)
    if not vp.exists():
        return None
    # 取时长
    at_sec = 1.5
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", vp.as_posix()],
            capture_output=True, text=True, timeout=20,
        )
        dur = float((probe.stdout or "0").strip() or 0)
        if dur > 0:
            at_sec = max(0.0, dur * fraction)
    except Exception:
        pass
    out = vp.parent / f"_judge_frame_{uuid.uuid4().hex[:6]}.png"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{at_sec:.2f}", "-i", vp.as_posix(),
             "-vframes", "1", out.as_posix()],
            capture_output=True, timeout=60,
        )
    except Exception:
        return None
    return str(out) if out.exists() else None


@router.post("/style-samples/{sample_id}/judge")
def judge_style_sample(sample_id: str) -> dict[str, Any]:
    """对样片进行视觉评分。

    V0.4.0: 使用 AI 视觉模型对 poster 进行感知质量评分，
    结果保存到 StyleSample.visual_judgement。

    优先使用 poster_url，没有时使用 video_url。
    """
    from datetime import datetime
    from app.video_lab.style_gallery import store as sg_store
    from app.video_lab.style_gallery.models import VisualJudgement
    from app.video_lab.quality.visual_judge import assess_visual_quality

    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")

    # V0.4.0: 获取图片路径进行评分
    poster_path = sample.output.poster
    video_path = sample.output.path

    if not poster_path and not video_path:
        raise HTTPException(
            status_code=400,
            detail="No poster or video available for judging. Sample may still be generating.",
        )

    # 优先使用 poster_path
    image_path = poster_path if poster_path else video_path

    # 将 /runtime/ 路径转换为实际文件路径
    runtime_prefix = "runtime/"
    if image_path.startswith("/runtime/"):
        image_path = image_path[len("/runtime/"):]
    if not image_path.startswith(runtime_prefix):
        image_path = runtime_prefix + image_path

    # V0.4.5: 只有视频没有 poster 时，先抽一帧再评（mp4 不能直接送视觉模型）
    from pathlib import Path as _Path
    if _Path(image_path).suffix.lower() in (".mp4", ".webm", ".mov"):
        frame_path = _extract_video_frame(image_path)
        if not frame_path:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract a frame from video for judging (no poster available).",
            )
        image_path = frame_path

    # 调用视觉评分
    judge_result = assess_visual_quality(image_path)

    if not judge_result.get("success"):
        msg = judge_result.get("message", "unknown error")
        # V0.4.8: 缺 API Key 是配置问题，返回 503 + 明确提示（避免误以为是本地能力）
        if "MINIMAX_API_KEY" in msg or "not configured" in msg.lower():
            raise HTTPException(
                status_code=503,
                detail="视觉评分依赖 MiniMax 多模态模型，需配置 MINIMAX_API_KEY 后才可用（非本地能力）。",
            )
        raise HTTPException(status_code=500, detail=f"Visual judge failed: {msg}")

    scores = judge_result.get("scores", {})
    overall_1to5 = judge_result.get("overall", 3.0)

    # 将 1-5 分转换为 0-100 分
    raw_score = round(overall_1to5 * 20, 1)

    # 计算等级
    if raw_score >= 85:
        grade = "excellent"
    elif raw_score >= 70:
        grade = "good"
    elif raw_score >= 55:
        grade = "ok"
    else:
        grade = "poor"

    # 生成 strengths / weaknesses / suggestions
    suggestions = judge_result.get("suggestions", [])
    strengths = _infer_strengths_from_scores(scores)
    weaknesses = _infer_weaknesses_from_scores(scores)

    # 构建 summary
    summary = _build_summary(grade, scores, raw_score)

    # 保存评分结果
    judgement = VisualJudgement(
        score=raw_score,
        grade=grade,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=[str(s) for s in suggestions],
        judged_at=datetime.utcnow().isoformat(),
        dimensions={k: float(v) for k, v in scores.items()},
    )

    sample.visual_judgement = judgement
    sg_store.save_sample(sample)

    # V0.4.4: 评分历史留痕（append-only，使"历史可分析"成立；失败不影响评分）
    try:
        from app.video_lab.style_gallery import score_history
        score_history.append_score({
            "sampleId": sample.id,
            "route_id": sample.route_id,
            "route_name": sample.route_name,
            "styleName": sample.style_name,
            "score": raw_score,
            "grade": grade,
            "dimensions": {k: float(v) for k, v in scores.items()},
        })
    except Exception:
        pass

    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


@router.get("/style-gallery/judge-availability")
def judge_availability() -> dict[str, Any]:
    """视觉评分是否可用（依赖 MiniMax 多模态模型 / MINIMAX_API_KEY）。

    供前端在评分前提示用户：评分是云端能力，需配置 Key。
    """
    from app.video_lab.providers.minimax import MiniMaxChatClient
    available = MiniMaxChatClient().is_configured()
    return {
        "available": available,
        "message": "" if available else "视觉评分需配置 MINIMAX_API_KEY（云端多模态模型，非本地能力）。",
    }


@router.get("/style-gallery/route-fit")
def style_gallery_route_fit() -> dict[str, Any]:
    """每条路线"最适合风格"判定（宏观目标①）。

    基于已评分样片，给出每条路线得分最高的样片/风格 + 平均分 + 数量，
    用于沉淀"哪条路线适合什么风格"的探索结论。
    """
    from app.video_lab.style_gallery import store as sg_store

    samples = sg_store.list_samples(limit=10000)
    grouped: dict[str, dict[str, Any]] = {}
    for s in samples:
        g = grouped.setdefault(s.route_id, {"route_name": s.route_name, "samples": []})
        g["samples"].append(s)

    out: dict[str, Any] = {}
    for rid, g in grouped.items():
        scored = [s for s in g["samples"] if s.visual_judgement]
        best = max(scored, key=lambda s: s.visual_judgement.score) if scored else None
        avg = round(sum(s.visual_judgement.score for s in scored) / len(scored), 1) if scored else None
        best_d = None
        if best:
            urls = sg_store.resolve_sample_urls(best)
            best_d = {
                "sampleId": best.id,
                "styleName": best.style_name,
                "score": best.visual_judgement.score,
                "grade": best.visual_judgement.grade,
                "poster": urls.get("poster_url", ""),
            }
        out[rid] = {
            "routeName": g["route_name"],
            "sampleCount": len(g["samples"]),
            "scoredCount": len(scored),
            "avgScore": avg,
            "best": best_d,
        }
    return out


@router.get("/style-gallery/score-history")
def style_gallery_score_history(route_id: str = "", sample_id: str = "", limit: int = 200) -> dict[str, Any]:
    """样片评分历史 + 按路线趋势聚合（历史可分析）。"""
    from app.video_lab.style_gallery import score_history
    return {
        "byRoute": score_history.summarize_by_route(),
        "records": list(reversed(score_history.read_scores(
            route_id=route_id or None, sample_id=sample_id or None, limit=limit,
        ))),
    }


def _infer_strengths_from_scores(scores: dict[str, float]) -> list[str]:
    """从各维度分数推断优点（分数 >= 4 视为优点）。"""
    strengths = []
    labels = {
        "layout": "排版留白合理",
        "readability": "文字清晰可读",
        "hierarchy": "信息层级清晰",
        "aesthetics": "整体美观专业",
        "consistency": "风格一致稳定",
    }
    for dim, score in scores.items():
        if score >= 4.0:
            strengths.append(labels.get(dim, f"{dim}表现良好"))
    if not strengths:
        strengths.append("整体无明显缺陷")
    return strengths


def _infer_weaknesses_from_scores(scores: dict[str, float]) -> list[str]:
    """从各维度分数推断问题（分数 <= 2.5 视为问题）。"""
    weaknesses = []
    labels = {
        "layout": "排版略显拥挤",
        "readability": "文字清晰度不足",
        "hierarchy": "信息层级不够突出",
        "aesthetics": "美观度有提升空间",
        "consistency": "风格不够统一",
    }
    for dim, score in scores.items():
        if score <= 2.5:
            weaknesses.append(labels.get(dim, f"{dim}有待改善"))
    return weaknesses


def _build_summary(grade: str, scores: dict[str, float], raw_score: float) -> str:
    """基于等级和分数生成中文摘要。"""
    grade_labels = {
        "excellent": "优秀",
        "good": "良好",
        "ok": "一般",
        "poor": "较差",
    }
    label = grade_labels.get(grade, grade)
    top_dim = max(scores.items(), key=lambda x: x[1])[0] if scores else "整体"
    dim_labels = {
        "layout": "排版",
        "readability": "可读性",
        "hierarchy": "层级",
        "aesthetics": "美观度",
        "consistency": "一致性",
    }
    top_name = dim_labels.get(top_dim, top_dim)
    return f"{label}水准（{raw_score}分），{top_name}表现最佳，适合资讯类内容分享。"


# ─── V0.4.2: Style Templates ─────────────────────────────────────────────────

@router.post("/style-samples/{sample_id}/promote-template")
def promote_sample_to_template(
    sample_id: str,
    request: dict[str, Any],
) -> dict[str, Any]:
    """将样片升级为模板。

    V0.4.2: 从已有样片创建可复用模板记录。
    """
    import uuid
    from datetime import datetime
    from app.video_lab.style_gallery import store as sg_store
    from app.video_lab.style_gallery import templates as sg_templates
    from app.video_lab.style_gallery.models import VisualJudgement

    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")

    # V0.4.7: 升级去重 —— 同一样片默认不重复创建模板（force=true 可强制再建）
    force = bool(request.get("force", False))
    existing = sg_templates.find_by_source_sample(sample_id)
    if existing and not force:
        result = existing.to_dict()
        result["deduped"] = True
        result["warnings"] = ["该样片已存在模板，未重复创建。如需再建一份，请使用 force。"]
        return result

    name = request.get("name") or f"{sample.style_name} 模板"

    # Build visual_judgement dict if present
    vj_dict = None
    if sample.visual_judgement:
        vj_dict = sample.visual_judgement.model_dump(mode="json") if hasattr(sample.visual_judgement, "model_dump") else sample.visual_judgement

    template_id = f"template_{uuid.uuid4().hex[:8]}"
    template = sg_templates.StyleTemplate(
        id=template_id,
        name=name,
        route_id=sample.route_id,
        route_name=sample.route_name,
        style_name=sample.style_name,
        description=request.get("description", ""),
        params=sample.params,
        source_sample_id=sample.id,
        source_sample_score=sample.visual_judgement.score if sample.visual_judgement else None,
        visual_judgement=vj_dict,
        tags=sample.tags,
        created_at=datetime.utcnow(),
    )

    sg_templates.save_template(template)

    # Build warnings if any
    warnings: list[str] = []
    if not sample.visual_judgement:
        warnings.append("该样片尚未进行视觉评分，建议先评分后再确定是否适合作为模板。")
    elif sample.visual_judgement.score < 55:
        warnings.append("该样片视觉评分偏低（低于55分），作为模板效果可能有限。")

    result = template.to_dict()
    if warnings:
        result["warnings"] = warnings
    return result


@router.get("/style-templates")
def list_style_templates(route_id: str | None = None) -> list[dict[str, Any]]:
    """列出风格模板，支持按路线过滤。"""
    from app.video_lab.style_gallery import templates as sg_templates
    templates = sg_templates.list_templates(route_id=route_id)
    return [t.to_dict() for t in templates]


@router.get("/style-templates/{template_id}")
def get_style_template(template_id: str) -> dict[str, Any]:
    """获取单个模板详情。"""
    from app.video_lab.style_gallery import templates as sg_templates
    template = sg_templates.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return template.to_dict()


@router.delete("/style-templates/{template_id}")
def delete_style_template(template_id: str) -> dict[str, Any]:
    """删除一条模板记录（不删除原样片和视频文件）。"""
    from app.video_lab.style_gallery import templates as sg_templates
    deleted = sg_templates.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return {"deleted": template_id}


@router.get("/style-gallery/preset-styles")
def list_preset_styles() -> list[dict[str, Any]]:
    """返回每条路线的预置风格入口（数据见 style_gallery/presets.py，每路线多个覆盖参数空间）。"""
    from app.video_lab.style_gallery.presets import list_preset_styles as _presets
    return _presets()
