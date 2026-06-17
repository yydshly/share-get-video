"""
Video Capability Lab - FastAPI Router (V1.0.2)

Thin router: only defines APIRouter, request/response entry points,
and delegates business logic to services.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.video_lab.models import VideoTestCase, VideoMethod, VideoExperimentResult, VideoExperimentEvaluation
from app.video_lab.seed_data import SEED_TEST_CASES, SEED_VIDEO_METHODS, get_test_case_by_id, get_method_by_id
from app.video_lab.advisor import getVideoMethodAdvice, get_all_advice
from app.video_lab.experiment_runner import get_runner
from app.video_lab.schemas import (
    CreateExperimentRequest,
    SaveEvaluationRequest,
    CreateBenchmarkRequest,
    CreateChainBenchmarkRequest,
    VisualComposeRequest,
    FramePreviewRequest,
    ClipPreviewRequest,
    VisualJudgeRequest,
    StyleSampleGenerateRequest,
    StyleSampleSaveRequest,
    StyleFamilyCompareRequest,
    BackgroundVariantMatrixRequest,
    TransitionVariantMatrixRequest,
    VisualStyleMatrixRequest,
    TechniqueProbeRequest,
    StyleSweepRequest,
)
from app.video_lab.config import PUBLIC_RUNTIME_URL_PREFIX, ffmpeg_bin, ffprobe_bin
from app.video_lab.path_contract import runtime_url_to_path
from app.video_lab.errors import make_error
from app.video_lab.run_context import RunContext

# Services
from app.video_lab.services import (
    run_clip_preview_contract,
    run_visual_compose_contract,
    run_visual_compose_endpoint,
    run_style_family_compare,
    run_background_variant_matrix,
    run_transition_variant_matrix,
    run_visual_style_matrix,
    run_technique_probe_endpoint,
    run_style_sweep_endpoint,
    extract_style_sample_assets,
)
from app.video_lab.services.assets import _safe_get, _artifact_type_value


router = APIRouter(prefix="/video-lab", tags=["VideoLab"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────
def _strip_runtime_url_prefix(url: str) -> str:
    """Strip PUBLIC_RUNTIME_URL_PREFIX to get stored path."""
    if not url:
        return ""
    prefix = PUBLIC_RUNTIME_URL_PREFIX.rstrip("/")
    if prefix and url.startswith(prefix + "/"):
        return url[len(prefix) + 1:]
    if url.startswith("/runtime/"):
        return url[len("/runtime/"):]
    return url.lstrip("/")


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
    runner = get_runner()

    tc = get_test_case_by_id(request.testCaseId)
    if not tc:
        raise HTTPException(status_code=400, detail=f"Unknown test case: {request.testCaseId}")

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
    from app.video_lab.routes_benchmark.registry import list_routes as _list_routes
    return _list_routes()


@router.post("/route-benchmarks")
def create_benchmark(request: CreateBenchmarkRequest) -> dict[str, Any]:
    from app.video_lab.routes_benchmark.registry import get_route_by_id
    from app.video_lab.routes_benchmark.runner import get_runner as _get_runner

    invalid_routes = []
    for rid in request.routeIds:
        if get_route_by_id(rid) is None:
            invalid_routes.append(rid)

    if invalid_routes:
        raise HTTPException(status_code=400, detail=f"Unknown route IDs: {invalid_routes}")

    runner = _get_runner()

    benchmark = runner.create_benchmark(
        test_case_id=request.testCaseId,
        title=request.title,
        input_payload=request.inputPayload,
        common_params=request.commonParams,
        route_ids=request.routeIds,
    )

    result = runner.run_benchmark(benchmark.benchmark_id)
    return result.to_dict()


@router.get("/route-benchmarks/{benchmark_id}")
def get_benchmark(benchmark_id: str) -> dict[str, Any]:
    from app.video_lab.routes_benchmark.runner import get_runner as _get_runner

    runner = _get_runner()
    benchmark = runner.get_benchmark(benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"Benchmark not found: {benchmark_id}")

    return benchmark.to_dict()


# ─────────────────────────────────────────────
# Visual Routes
# ─────────────────────────────────────────────
@router.get("/visual-routes")
def list_visual_routes() -> list[dict[str, Any]]:
    from app.video_lab.renderers.visual import list_visual_renderers
    return list_visual_renderers()


@router.post("/frame-preview")
def frame_preview(request: FramePreviewRequest) -> dict[str, Any]:
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
    import subprocess
    import uuid
    from pathlib import Path
    from app.video_lab.quality.visual_judge import assess_visual_quality

    url = request.imageUrl
    local = runtime_url_to_path(url)
    if not local.exists():
        raise HTTPException(status_code=404, detail=f"file not found: {local}")

    judge_paths: list[str] = [str(local)]
    if local.suffix.lower() in (".mp4", ".webm", ".mov"):
        try:
            probe = subprocess.run(
                [ffprobe_bin(), "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", local.as_posix()],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
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
                    [ffmpeg_bin(), "-y", "-ss", f"{t:.2f}", "-i", local.as_posix(),
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
            logger.warning("visual-judge score logging failed (non-fatal)", exc_info=True)

    return result


@router.get("/quality-history")
def quality_history(route: str = "", kind: str = "", limit: int = 300) -> list[dict[str, Any]]:
    from app.video_lab.quality.quality_log import read_records
    return read_records(route=route or None, kind=kind or None, limit=limit)


@router.get("/quality-summary")
def quality_summary() -> dict[str, Any]:
    from app.video_lab.quality.quality_log import summarize_by_route
    return summarize_by_route()


# ─────────────────────────────────────────────
# clip-preview — delegates to clip_preview_service
# ─────────────────────────────────────────────
@router.post("/clip-preview")
def clip_preview(request: ClipPreviewRequest) -> dict[str, Any]:
    """Render a short (~3s) animated clip. V1 contract: always returns
    success/status/contractStatus/artifacts/error/rawOutput."""
    return run_clip_preview_contract(request)


# ─────────────────────────────────────────────
# style-family — delegates to style_family_service
# ─────────────────────────────────────────────
@router.post("/style-family/compare")
def style_family_compare(request: StyleFamilyCompareRequest) -> dict[str, Any]:
    """Compare Data News vs Card Stack vs Timeline vs Dashboard vs Caption Story
    Remotion presentation paradigms."""
    return run_style_family_compare(request)


# V1.2.3: Lab-only 背景差异化实验
@router.post("/style-family/background-matrix")
def style_family_background_matrix(request: BackgroundVariantMatrixRequest) -> dict[str, Any]:
    """Background Variant Matrix: 3 families × 3 background presets = 9 clips.

    Lab-only: does NOT write Style Sweep job, Style Gallery sample, or promote.
    """
    try:
        return run_background_variant_matrix(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/style-family/transition-matrix")
def style_family_transition_matrix(request: TransitionVariantMatrixRequest) -> dict[str, Any]:
    """Transition Variant Matrix: family x transition style clips.

    Lab-only: does NOT write Style Sweep job, Style Gallery sample, or promote.
    """
    try:
        return run_transition_variant_matrix(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# V1.2.4: Lab-only visual style preset matrix
@router.post("/style-family/visual-style-matrix")
def style_family_visual_style_matrix(request: VisualStyleMatrixRequest) -> dict[str, Any]:
    """Visual Style Preset Matrix: family x visualStylePreset clips.

    Lab-only: does NOT write Style Sweep job, Style Gallery sample, or promote.
    """
    try:
        return run_visual_style_matrix(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────
# visual-compose — delegates to visual_compose_service
# ─────────────────────────────────────────────
def _run_visual_compose(content: str, visual_route: str, params_in: dict | None) -> dict[str, Any]:
    """
    Thin compatibility wrapper — delegates to run_visual_compose_contract.

    Kept in router so technique_probe.py can continue to import it without
    needing to know about services/.
    """
    return run_visual_compose_contract(content, visual_route, params_in)


@router.post("/visual-compose")
def visual_compose(request: VisualComposeRequest) -> dict[str, Any]:
    """Run ONE visual route end-to-end (LLM plan + TTS + 字幕 + 合成).
    V1 contract: always returns success/status/contractStatus/artifacts/error/rawOutput."""
    return run_visual_compose_endpoint(request)


# ─────────────────────────────────────────────
# information-structure — V1.2.1: Information Summary Video Mode
# ─────────────────────────────────────────────

class InformationStructureRequest(BaseModel):
    """JSON body for POST /video-lab/information-structure"""
    content: str = Field(..., min_length=1, description="报告原文内容")
    title: str | None = Field(default=None, description="可选标题，仅用于元数据")
    body: str | None = Field(default=None, description="可选正文，报告型输入优先使用正文做结构化")
    compression_mode: str = Field(default="balanced", description="精简摘要 | 均衡总结 | 严格保留 | 逐条展开 | 手动分段")
    target_point_count: str = Field(default="auto", description="自动 | 3 | 5 | 8 | all")
    include_overview: bool = Field(default=True, description="是否生成首页总览")
    include_conclusion: bool = Field(default=True, description="是否生成尾部总结")
    evidence_policy: str = Field(default="ending_sources", description="隐藏 | 角标 | 片尾来源 | 原文保留")
    target_duration_mode: str = Field(default="auto", description="自动匹配信息量 | 30秒快讯 | 60秒标准总结 | 90秒完整展开")
    input_profile: str = Field(default="auto", description="auto | report_overview_items")


@router.post("/information-structure")
def generate_information_structure(request: InformationStructureRequest) -> dict[str, Any]:
    """Parse content and generate an InformationSummaryPlan structure.

    Used by Workbench "Information Summary Video Mode" to show content structure
    before generating a video, helping users understand what will be included.
    """
    from app.video_lab.services.information_structure_service import (
        generate_information_structure as _gen_structure,
        serialize_for_visual_compose,
    )

    plan = _gen_structure(
        content=request.content,
        title=request.title,
        body=request.body,
        compression_mode=request.compression_mode,
        target_point_count=request.target_point_count,
        include_overview=request.include_overview,
        include_conclusion=request.include_conclusion,
        evidence_policy=request.evidence_policy,
        target_duration_mode=request.target_duration_mode,
        input_profile=request.input_profile,
    )

    # Also provide serialized version for visual-compose
    serialized = serialize_for_visual_compose(plan)

    return {
        "success": True,
        "plan": plan,
        "serializedContent": serialized,
    }


# ─────────────────────────────────────────────
# technique-probe — delegates to probe_service
# ─────────────────────────────────────────────
def _judge_probe_result(result: dict[str, Any]) -> dict[str, Any] | None:
    """Judge a single route's output for technique probe ranking.
    Kept in router.py for compatibility (passed as judge_fn to technique-probe)."""
    from app.video_lab.services.probe_service import _judge_probe_result as _judge
    return _judge(result)


@router.post("/technique-probe")
def technique_probe(request: TechniqueProbeRequest) -> dict[str, Any]:
    """Best technique probe: one content → all routes produce full video →
    unified quality ranking → recommended route. Synchronous."""
    return run_technique_probe_endpoint(
        request=request,
        compose_fn=_run_visual_compose,
        judge_fn=_judge_probe_result,
    )


# ─────────────────────────────────────────────
# style-sweep — delegates to style_sweep_service
# ─────────────────────────────────────────────
@router.post("/style-sweep")
def style_sweep(request: StyleSweepRequest) -> dict[str, Any]:
    """Style comparison: select one technical route → render each preset style →
    side-by-side results. Synchronous."""
    return run_style_sweep_endpoint(
        request=request,
        render_fn=_run_visual_compose,
    )


# ─────────────────────────────────────────────
# style-sweep-jobs — async job API for progress reporting
# ─────────────────────────────────────────────
@router.post("/style-sweep-jobs")
def create_style_sweep_job(request: StyleSweepRequest) -> dict[str, Any]:
    """Create a new async style-sweep job. Returns jobId immediately;
    poll GET /style-sweep-jobs/{jobId} for progress."""
    from app.video_lab.style_sweep import styles_for_route
    from app.video_lab.style_sweep_jobs import create_sweep_job

    route_styles = styles_for_route(request.routeId)
    route_name = route_styles[0].get("route_name", request.routeId) if route_styles else request.routeId

    job = create_sweep_job(
        content=request.content,
        route_id=request.routeId,
        route_name=route_name,
        total=len(route_styles),
        params=request.params,
        render_fn=_run_visual_compose,
        styles=route_styles,
    )
    return {"jobId": job.jobId, "status": job.status}


@router.get("/style-sweep-jobs/{job_id}")
def get_style_sweep_job(job_id: str) -> dict[str, Any]:
    """Return current state of a style-sweep job."""
    from app.video_lab.style_sweep_jobs import get_sweep_job

    job = get_sweep_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job.to_dict()


@router.get("/style-sweep-jobs")
def list_style_sweep_jobs(limit: int = 20) -> dict[str, Any]:
    """Return recent style-sweep job summaries (no full results), newest first."""
    from app.video_lab.style_sweep_jobs import list_sweep_jobs as _list
    jobs = _list(limit=limit)
    return {"jobs": jobs}


@router.delete("/style-sweep-jobs/{job_id}")
def delete_style_sweep_job(job_id: str) -> dict[str, Any]:
    """Delete a sweep job record (JSON only; does NOT delete any video/audio/subtitle assets).

    Asset cleanup is intentionally deferred — promoted samples in Style Gallery may still
    reference the job's output files. Use Stage 3A-2 for safe asset cleanup.
    """
    from app.video_lab.style_sweep_jobs import delete_sweep_job as _delete

    deleted = _delete(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {
        "jobId": job_id,
        "deleted": True,
        "deletedAssets": False,
        "message": "Style Sweep job record deleted",
    }


# ─────────────────────────────────────────────
# style-sweep-assets — dry-run scan (Stage 3A-4)
# ─────────────────────────────────────────────
@router.get("/style-sweep-assets/scan")
def scan_style_sweep_assets(
    minAgeDays: int = 7,
    includeProtected: bool = True,
    limit: int = 500,
) -> dict[str, Any]:
    """Dry-run scan of Style Sweep runtime assets.

    Returns asset inventory grouped into:
    - protectedItems: files still referenced by Style Gallery samples (MUST NOT delete)
    - deletableItems: unreferenced files old enough to consider cleaning
    - skippedItems: unreferenced files too new to safely clean

    This endpoint does NOT delete any files.
    """
    from app.video_lab.services.style_sweep_asset_cleanup_service import (
        scan_style_sweep_assets as _scan,
    )

    return _scan(
        min_age_days=minAgeDays,
        include_protected=includeProtected,
        limit=limit,
    )


class UpdateSweepJobMarksRequest(BaseModel):
    manualMarks: dict[str, Any] = Field(default_factory=dict)


@router.patch("/style-sweep-jobs/{job_id}/marks")
def update_style_sweep_job_marks(job_id: str, request: UpdateSweepJobMarksRequest) -> dict[str, Any]:
    """Save human-readable marks (issues + notes) for a style-sweep job."""
    from datetime import datetime, timezone
    from app.video_lab.style_sweep_jobs import update_sweep_job_marks as _update_marks

    updated = _update_marks(job_id, request.manualMarks)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {
        "jobId": updated.jobId,
        "saved": True,
        "manualMarkCount": len(updated.manualMarks),
        "updatedAt": updated.updatedAt,
    }


class PromoteSweepJobRequest(BaseModel):
    styleIds: list[str] = Field(..., description="List of styleId values to promote")
    targetStatus: str = Field(default="candidate", description="Initial sample status")
    note: str = Field(default="", description="Optional note stored in source.saved_from")


@router.post("/style-sweep-jobs/{job_id}/promote")
def promote_style_sweep_job(job_id: str, request: PromoteSweepJobRequest) -> dict[str, Any]:
    """Promote one or more successful Style Sweep results as Style Gallery samples.

    Does NOT regenerate any video/TTS/AI assets. Re-uses existing finalVideoUrl /
    manifestUrl / audioUrl / srtUrl / assUrl from the job result.
    """
    from app.video_lab.services.style_sweep_promotion_service import (
        promote_sweep_results_to_gallery as _promote,
    )

    try:
        result = _promote(
            job_id=job_id,
            style_ids=request.styleIds,
            target_status=request.targetStatus,
            note=request.note,
        )
    except ValueError as e:
        msg = str(e)
        if "Job not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return result


# ─────────────────────────────────────────────
# Route Recommendation
# ─────────────────────────────────────────────
@router.get("/route-recommendation")
def route_recommendation() -> dict[str, Any]:
    from app.video_lab.route_recommendation import recommend_route
    return recommend_route()


# ─────────────────────────────────────────────
# Chain Benchmarks
# ─────────────────────────────────────────────
@router.get("/chains")
def list_chains() -> list[dict[str, Any]]:
    from app.video_lab.chains.registry import list_chains as _list_chains
    return [c.to_dict() for c in _list_chains()]


@router.post("/chain-benchmarks")
def create_chain_benchmark(request: CreateChainBenchmarkRequest) -> dict[str, Any]:
    from app.video_lab.chains.registry import get_chain
    from app.video_lab.routes_benchmark.chain_runner import get_chain_runner as _get_chain_runner

    invalid_chains = []
    for cid in request.chainIds:
        if get_chain(cid) is None:
            invalid_chains.append(cid)

    if invalid_chains:
        raise HTTPException(status_code=400, detail=f"Unknown chain IDs: {invalid_chains}")

    runner = _get_chain_runner()

    benchmark = runner.create_benchmark(
        test_case_id=request.testCaseId,
        title=request.title,
        input_payload=request.inputPayload,
        common_params=request.commonParams,
        chain_ids=request.chainIds,
    )

    result = runner.run_benchmark(benchmark.benchmark_id)
    return result.to_dict()


@router.get("/chain-benchmarks/{benchmark_id}")
def get_chain_benchmark(benchmark_id: str) -> dict[str, Any]:
    from app.video_lab.routes_benchmark.chain_runner import get_chain_runner as _get_chain_runner
    runner = _get_chain_runner()
    benchmark = runner.get_benchmark(benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"Chain benchmark not found: {benchmark_id}")
    return benchmark.to_dict()


# ─────────────────────────────────────────────
# Style Sample Gallery
# ─────────────────────────────────────────────
@router.get("/style-samples")
def list_style_samples(
    route_id: str | None = None,
    status: str | None = None,
    source_type: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from app.video_lab.style_gallery import store as sg_store
    samples = sg_store.list_samples(route_id=route_id, status=status, source_type=source_type, tag=tag, limit=limit)
    out = []
    for s in samples:
        d = s.to_dict()
        urls = sg_store.resolve_sample_urls(s)
        d["urls"] = urls
        out.append(d)
    return out


@router.post("/style-samples/generate")
def generate_style_sample(request: StyleSampleGenerateRequest) -> dict[str, Any]:
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
    import uuid
    from datetime import datetime
    from app.video_lab.style_gallery.models import (
        StyleSample, SampleStatus, StyleSampleOutput, EvaluationScore,
        SampleSource, SampleGenerationMeta, SampleAssetMeta,
        SampleQualityMeta, SampleReviewMeta,
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
        # V1.0.5: Experiment asset metadata
        source=SampleSource(**request.source) if request.source else SampleSource(),
        generation=SampleGenerationMeta(**request.generation) if request.generation else SampleGenerationMeta(),
        asset_meta=SampleAssetMeta(**request.asset_meta) if request.asset_meta else SampleAssetMeta(),
        quality_meta=SampleQualityMeta(**request.quality_meta) if request.quality_meta else SampleQualityMeta(),
        review_meta=SampleReviewMeta(**request.review_meta) if request.review_meta else SampleReviewMeta(),
        job_run=request.job_run or {},
        schema_version=request.schema_version or "1.0.5",
    )

    sg_store.save_sample(sample)
    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


@router.get("/style-samples/{sample_id}")
def get_style_sample(sample_id: str) -> dict[str, Any]:
    from app.video_lab.style_gallery import store as sg_store
    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")
    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


@router.delete("/style-samples/{sample_id}")
def delete_style_sample(sample_id: str) -> dict[str, Any]:
    from app.video_lab.style_gallery import store as sg_store
    deleted = sg_store.delete_sample(sample_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")
    return {"deleted": sample_id}


@router.post("/style-samples/{sample_id}/compare")
def mark_sample_for_compare(sample_id: str) -> dict[str, Any]:
    from app.video_lab.style_gallery import store as sg_store
    from app.video_lab.style_gallery.models import SampleStatus
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
    from app.video_lab.style_gallery import store as sg_store
    from app.video_lab.style_gallery.models import SampleStatus

    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")

    new_status = request.get("status", "")
    valid_statuses = [s.value for s in SampleStatus]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    sample.status = SampleStatus(new_status)
    sg_store.save_sample(sample)
    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


# V1.0.6: Style Sample Replay
@router.get("/style-samples/{sample_id}/rerun-payload")
def get_style_sample_rerun_payload(sample_id: str) -> dict[str, Any]:
    """Build a rerun payload from a StyleSample record. Does NOT execute generation."""
    from app.video_lab.style_gallery import store as sg_store
    from app.video_lab.style_gallery import replay

    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")

    return replay.build_rerun_payload(sample)


def _extract_video_frame(video_path: str, fraction: float = 0.4) -> str | None:
    """Extract one frame from video at fraction position. Kept in router for
    judge_style_sample compatibility."""
    import subprocess
    import uuid
    from pathlib import Path

    vp = Path(video_path)
    if not vp.exists():
        return None
    at_sec = 1.5
    try:
        probe = subprocess.run(
            [ffprobe_bin(), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", vp.as_posix()],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
        )
        dur = float((probe.stdout or "0").strip() or 0)
        if dur > 0:
            at_sec = max(0.0, dur * fraction)
    except Exception:
        pass
    out = vp.parent / f"_judge_frame_{uuid.uuid4().hex[:6]}.png"
    try:
        subprocess.run(
            [ffmpeg_bin(), "-y", "-ss", f"{at_sec:.2f}", "-i", vp.as_posix(),
             "-vframes", "1", out.as_posix()],
            capture_output=True, timeout=60,
        )
    except Exception:
        return None
    return str(out) if out.exists() else None


@router.post("/style-samples/{sample_id}/judge")
def judge_style_sample(sample_id: str) -> dict[str, Any]:
    from datetime import datetime
    from app.video_lab.style_gallery import store as sg_store
    from app.video_lab.style_gallery.models import VisualJudgement
    from app.video_lab.quality.visual_judge import assess_visual_quality

    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")

    poster_path = sample.output.poster
    video_path = sample.output.path

    if not poster_path and not video_path:
        raise HTTPException(
            status_code=400,
            detail="No poster or video available for judging. Sample may still be generating.",
        )

    image_path = poster_path if poster_path else video_path

    from app.video_lab.path_contract import runtime_url_to_path
    image_path = str(runtime_url_to_path(image_path))

    from pathlib import Path as _Path
    if _Path(image_path).suffix.lower() in (".mp4", ".webm", ".mov"):
        frame_path = _extract_video_frame(image_path)
        if not frame_path:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract a frame from video for judging (no poster available).",
            )
        image_path = frame_path

    judge_result = assess_visual_quality(image_path)

    if not judge_result.get("success"):
        msg = judge_result.get("message", "unknown error")
        if "MINIMAX_API_KEY" in msg or "not configured" in msg.lower():
            raise HTTPException(
                status_code=503,
                detail="视觉评分依赖 MiniMax 多模态模型，需配置 MINIMAX_API_KEY 后才可用（非本地能力）。",
            )
        raise HTTPException(status_code=500, detail=f"Visual judge failed: {msg}")

    scores = judge_result.get("scores", {})
    overall_1to5 = judge_result.get("overall", 3.0)

    raw_score = round(overall_1to5 * 20, 1)

    if raw_score >= 85:
        grade = "excellent"
    elif raw_score >= 70:
        grade = "good"
    elif raw_score >= 55:
        grade = "ok"
    else:
        grade = "poor"

    suggestions = judge_result.get("suggestions", [])
    strengths = _infer_strengths_from_scores(scores)
    weaknesses = _infer_weaknesses_from_scores(scores)
    summary = _build_summary(grade, scores, raw_score)

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
        logger.warning("style score-history logging failed (non-fatal)", exc_info=True)

    d = sample.to_dict()
    d["urls"] = sg_store.resolve_sample_urls(sample)
    return d


@router.get("/style-gallery/judge-availability")
def judge_availability() -> dict[str, Any]:
    from app.video_lab.providers.minimax import MiniMaxChatClient
    available = MiniMaxChatClient().is_configured()
    return {
        "available": available,
        "message": "" if available else "视觉评分需配置 MINIMAX_API_KEY（云端多模态模型，非本地能力）。",
    }


@router.get("/style-gallery/route-fit")
def style_gallery_route_fit() -> dict[str, Any]:
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
    from app.video_lab.style_gallery import score_history
    return {
        "byRoute": score_history.summarize_by_route(),
        "records": list(reversed(score_history.read_scores(
            route_id=route_id or None, sample_id=sample_id or None, limit=limit,
        ))),
    }


# ─────────────────────────────────────────────
# Style Templates
# ─────────────────────────────────────────────
@router.post("/style-samples/{sample_id}/promote-template")
def promote_sample_to_template(sample_id: str, request: dict[str, Any]) -> dict[str, Any]:
    import uuid
    from datetime import datetime
    from app.video_lab.style_gallery import store as sg_store
    from app.video_lab.style_gallery import templates as sg_templates
    from app.video_lab.style_gallery.models import VisualJudgement

    sample = sg_store.get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")

    force = bool(request.get("force", False))
    existing = sg_templates.find_by_source_sample(sample_id)
    if existing and not force:
        result = existing.to_dict()
        result["deduped"] = True
        result["warnings"] = ["该样片已存在模板，未重复创建。如需再建一份，请使用 force。"]
        return result

    name = request.get("name") or f"{sample.style_name} 模板"

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
    from app.video_lab.style_gallery import templates as sg_templates
    templates = sg_templates.list_templates(route_id=route_id)
    return [t.to_dict() for t in templates]


@router.get("/style-templates/{template_id}")
def get_style_template(template_id: str) -> dict[str, Any]:
    from app.video_lab.style_gallery import templates as sg_templates
    template = sg_templates.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return template.to_dict()


@router.delete("/style-templates/{template_id}")
def delete_style_template(template_id: str) -> dict[str, Any]:
    from app.video_lab.style_gallery import templates as sg_templates
    deleted = sg_templates.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return {"deleted": template_id}


@router.get("/style-gallery/preset-styles")
def list_preset_styles() -> list[dict[str, Any]]:
    from app.video_lab.style_gallery.presets import list_preset_styles as _presets
    return _presets()


# ─────────────────────────────────────────────
# V1.0.7: Compare Bundle
# ─────────────────────────────────────────────
@router.post("/style-compare-bundles")
def create_style_compare_bundle(request: dict[str, Any]) -> dict[str, Any]:
    """Create a new Compare Bundle from a list of sample IDs."""
    from app.video_lab.style_gallery import compare_bundle as sg_bundle

    sample_ids = request.get("sampleIds", [])
    if not sample_ids:
        raise HTTPException(status_code=400, detail="sampleIds cannot be empty")

    if not isinstance(sample_ids, list):
        raise HTTPException(status_code=400, detail="sampleIds must be a list")

    title = request.get("title", "")
    goal = request.get("goal", "")
    tags = request.get("tags", None)

    bundle = sg_bundle.build_compare_bundle(
        sample_ids=sample_ids,
        title=title,
        goal=goal,
        tags=tags if isinstance(tags, list) else None,
    )

    if not bundle.sample_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid samples found for the given sampleIds",
        )

    saved = sg_bundle.save_compare_bundle(bundle)
    return saved.to_dict()


@router.get("/style-compare-bundles")
def list_style_compare_bundles(limit: int = 50) -> list[dict[str, Any]]:
    """List all Compare Bundles, sorted by updated_at descending."""
    from app.video_lab.style_gallery import compare_bundle as sg_bundle
    bundles = sg_bundle.list_compare_bundles(limit=limit)
    return [b.to_dict() for b in bundles]


@router.get("/style-compare-bundles/{bundle_id}")
def get_style_compare_bundle(bundle_id: str) -> dict[str, Any]:
    """Get a specific Compare Bundle by ID."""
    from app.video_lab.style_gallery import compare_bundle as sg_bundle
    bundle = sg_bundle.get_compare_bundle(bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Compare Bundle not found: {bundle_id}")
    return bundle.to_dict()


@router.delete("/style-compare-bundles/{bundle_id}")
def delete_style_compare_bundle(bundle_id: str) -> dict[str, Any]:
    """Delete a Compare Bundle by ID."""
    from app.video_lab.style_gallery import compare_bundle as sg_bundle
    deleted = sg_bundle.delete_compare_bundle(bundle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Compare Bundle not found: {bundle_id}")
    return {"deleted": bundle_id}


# ─────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────
def _infer_strengths_from_scores(scores: dict[str, float]) -> list[str]:
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
