"""
Video Capability Lab - FastAPI Router
"""

from typing import Any
from fastapi import APIRouter, HTTPException

from app.video_lab.models import VideoTestCase, VideoMethod, VideoExperimentResult, VideoExperimentEvaluation
from app.video_lab.seed_data import SEED_TEST_CASES, SEED_VIDEO_METHODS, get_test_case_by_id, get_method_by_id
from app.video_lab.advisor import getVideoMethodAdvice, get_all_advice
from app.video_lab.experiment_runner import get_runner
from app.video_lab.schemas import CreateExperimentRequest, SaveEvaluationRequest, CreateBenchmarkRequest, CreateChainBenchmarkRequest, VisualComposeRequest, FramePreviewRequest, ClipPreviewRequest, VisualJudgeRequest, StyleSampleGenerateRequest, StyleSampleSaveRequest


router = APIRouter(prefix="/video-lab", tags=["VideoLab"])


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
    rel = url[len("/runtime/"):] if url.startswith("/runtime/") else url.lstrip("/")
    local = Path("runtime") / rel if not rel.startswith("runtime") else Path(rel)
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


@router.post("/visual-compose")
def visual_compose(request: VisualComposeRequest) -> dict[str, Any]:
    """Run ONE visual route end-to-end (LLM plan + TTS + 字幕 + 合成) and return
    the final video URL + auto quality report. Frontend calls this per route.

    Synchronous: returns after the video is produced (TTS/render may take minutes).
    Business failures return HTTP 200 with status='failed' + failedReason.
    """
    import uuid
    from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose

    exp_id = f"web_{request.visualRoute}_{uuid.uuid4().hex[:8]}"
    params = dict(request.params or {})
    params["visualRoute"] = request.visualRoute

    try:
        result = run_tts_subtitle_compose(
            experiment_id=exp_id,
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": request.content},
            params=params,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

    # 从 manifest artifact 提取中间产物链接（音频/字幕/manifest）
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

    # 结构层评分留痕（趋势/防退化）
    try:
        from app.video_lab.quality.quality_log import append_record
        _q = raw.get("quality", {}) or {}
        append_record({
            "kind": "structural",
            "route": request.visualRoute,
            "experimentId": exp_id,
            "status": status,
            "overall": _q.get("overallScore"),
            "dimensions": _q.get("dimensionScores", {}),
            "durationSec": assets.get("audioDurationSec", 0),
            "subtitleCount": assets.get("subtitleCount", 0),
            "contentChars": len(request.content),
            "params": params,
        })
    except Exception:
        pass

    return {
        "experimentId": exp_id,
        "visualRoute": request.visualRoute,
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

    final_video_url = ""
    cover_url = ""
    audio_url = ""
    srt_url = ""
    manifest_url = ""
    duration_sec = 0.0
    audio_duration_sec = 0.0

    raw = result.raw_output if hasattr(result, "raw_output") else {}
    steps = getattr(result, "production_steps", [])

    for step in steps:
        for art in step.get("artifacts", []):
            atype = art.get("type", "")
            payload = art.get("payload", {})
            url = payload.get("url", "") if isinstance(payload, dict) else ""
            if not url:
                continue
            if atype == "final_video":
                final_video_url = url
            elif atype == "cover":
                cover_url = url
            elif atype == "manifest":
                manifest_url = url
            elif atype == "audio" and not audio_url:
                audio_url = url
            elif atype == "subtitle_srt" and not srt_url:
                srt_url = url

    assets = getattr(result, "assets", {}) or {}
    audio_duration_sec = float(assets.get("audioDurationSec", 0) or 0)
    duration_sec = float(assets.get("durationSec", audio_duration_sec) or audio_duration_sec)

    return {
        "sample_id": sample_id,
        "route_id": request.route_id,
        "style_name": request.style_name,
        "description": request.description,
        "status": "generated",
        "params": params,
        "output": {
            "type": "mp4",
            "path": final_video_url.replace("/runtime/", ""),
            "poster": cover_url.replace("/runtime/", ""),
            "audio_url": audio_url.replace("/runtime/", ""),
            "srt_url": srt_url.replace("/runtime/", ""),
            "manifest_url": manifest_url.replace("/runtime/", ""),
        },
        "duration_sec": duration_sec,
        "audio_duration_sec": audio_duration_sec,
        "content_preview": content[:100],
        "final_video_url": final_video_url,
        "cover_url": cover_url,
        "audio_url": audio_url,
        "srt_url": srt_url,
        "manifest_url": manifest_url,
        "failed": raw.get("status") != "succeeded",
        "failed_reason": raw.get("error") or ("生成失败" if raw.get("status") == "failed" else ""),
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


@router.get("/style-gallery/preset-styles")
def list_preset_styles() -> list[dict[str, Any]]:
    """
    返回每条路线的预置风格入口。
    V0.3.7: 每条路线至少 2 个风格。
    """
    return [
        # ── Pillow ──
        {
            "route_id": "local_frame_compose",
            "route_name": "Pillow 信息卡路线",
            "style_id": "pillow_data_card",
            "style_name": "稳定数据卡",
            "description": "清晰展示数据指标，强调数字和来源，适合资讯类内容",
            "capabilities": ["长文本可读", "数据卡清楚", "排版稳定", "批量生成可靠"],
            "tags": ["数据", "资讯", "稳定"],
            "params": {
                "showDataViz": True,
                "highlightMode": "auto",
                "contentAlign": "top",
                "themeAdaptive": True,
                "transitionEnabled": True,
                "transitionFrames": 4,
                "titleColor": "#f8fafc",
                "bodyColor": "#94a3b8",
                "highlightColor": "#f59e0b",
            },
        },
        {
            "route_id": "local_frame_compose",
            "route_name": "Pillow 信息卡路线",
            "style_id": "pillow_minimal",
            "style_name": "极简资讯卡",
            "description": "极简排版，去除装饰，聚焦内容本身，适合深度阅读",
            "capabilities": ["极简排版", "聚焦内容", "无干扰"],
            "tags": ["极简", "深度阅读"],
            "params": {
                "showDataViz": False,
                "highlightMode": "numbers",
                "contentAlign": "center",
                "themeAdaptive": False,
                "transitionEnabled": False,
                "transitionFrames": 0,
                "titleColor": "#f8fafc",
                "bodyColor": "#cbd5e1",
                "highlightColor": "#22d3ee",
            },
        },
        # ── Remotion ──
        {
            "route_id": "template_programmatic_render",
            "route_name": "Remotion 动态模板路线",
            "style_id": "remotion_metric_motion",
            "style_name": "动态数据栏目",
            "description": "数字滚动 + 进度条生长，展示 Remotion 时间轴动画能力，适合数据驱动内容",
            "capabilities": ["数字滚动", "进度条生长", "卡片入场", "页面转场", "栏目包装感"],
            "tags": ["动态", "数据", "栏目包装"],
            "params": {
                "showDataViz": True,
                "accentColor": "#3b82f6",
                "highlightColor": "#f59e0b",
                "fontScale": 1,
                "showIcon": True,
                "motionIntensity": "medium",
                "coverStyle": "editorial",
                "overviewStyle": "timeline",
                "metricAnimation": "countup_bar",
                "transitionStyle": "slide_fade",
            },
        },
        {
            "route_id": "template_programmatic_render",
            "route_name": "Remotion 动态模板路线",
            "style_id": "remotion_cinematic",
            "style_name": "电影感快讯",
            "description": "电影感配色 + 慢速转场，营造大屏资讯氛围，适合重点报道",
            "capabilities": ["电影感", "慢速转场", "大屏氛围", "重点报道"],
            "tags": ["电影感", "大屏", "重点"],
            "params": {
                "showDataViz": True,
                "accentColor": "#a78bfa",
                "highlightColor": "#fbbf24",
                "fontScale": 1.1,
                "showIcon": False,
                "motionIntensity": "low",
                "coverStyle": "cinematic",
                "overviewStyle": "grid",
                "metricAnimation": "countup_number",
                "transitionStyle": "fade",
            },
        },
        # ── AI Asset ──
        {
            "route_id": "ai_asset_then_compose",
            "route_name": "AI 素材氛围路线",
            "style_id": "ai_asset_tech_mood",
            "style_name": "深蓝科技氛围",
            "description": "AI 生成深蓝科技背景 + 信息卡融合，传播型视觉，适合前沿资讯",
            "capabilities": ["AI 背景", "科技感氛围", "封面感", "背景+信息卡融合", "传播型视觉"],
            "tags": ["科技", "氛围", "传播"],
            "params": {
                "showDataViz": True,
                "imageStyle": "深蓝科技数据可视化背景，未来感，抽象光线，电影质感，无文字，无文本，柔和景深",
                "backgroundDarken": 0.55,
                "cardOpacity": 0.85,
                "cardBlur": True,
                "highlightColor": "#f59e0b",
                "contentAlign": "top",
                "kenBurns": True,
            },
        },
        {
            "route_id": "ai_asset_then_compose",
            "route_name": "AI 素材氛围路线",
            "style_id": "ai_asset_cinematic",
            "style_name": "电影感光线背景",
            "description": "暖色调电影感光线背景 + 高对比度信息卡，适合深度分析和专题报道",
            "capabilities": ["电影感光线", "高对比度信息卡", "深度分析", "专题报道"],
            "tags": ["电影感", "光线", "深度"],
            "params": {
                "showDataViz": True,
                "imageStyle": "暖色调电影感光线背景，柔和散景，戏剧性光照，无文字，无文本，电影质感",
                "backgroundDarken": 0.6,
                "cardOpacity": 0.9,
                "cardBlur": False,
                "highlightColor": "#fbbf24",
                "contentAlign": "center",
                "kenBurns": True,
            },
        },
    ]
