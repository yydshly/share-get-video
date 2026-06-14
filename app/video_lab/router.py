"""
Video Capability Lab - FastAPI Router
"""

from typing import Any
from fastapi import APIRouter, HTTPException

from app.video_lab.models import VideoTestCase, VideoMethod, VideoExperimentResult, VideoExperimentEvaluation
from app.video_lab.seed_data import SEED_TEST_CASES, SEED_VIDEO_METHODS, get_test_case_by_id, get_method_by_id
from app.video_lab.advisor import getVideoMethodAdvice, get_all_advice
from app.video_lab.experiment_runner import get_runner
from app.video_lab.schemas import CreateExperimentRequest, SaveEvaluationRequest, CreateBenchmarkRequest, CreateChainBenchmarkRequest, VisualComposeRequest


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
