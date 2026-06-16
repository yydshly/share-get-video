"""
Visual Compose Service — extracted from router.py V1.0.2.

Provides:
  - run_visual_compose_contract(): core end-to-end compose logic
  - run_visual_compose_endpoint(): /visual-compose endpoint wrapper

V1 contract: returns runId / success / status / contractStatus / artifacts / error / rawOutput.
V1.0.4: also returns jobRun (JobRun v1 status contract).
"""

import logging
from typing import Any

from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
from app.video_lab.errors import make_error
from app.video_lab.experiment_manifest import build_experiment_manifest, write_experiment_manifest
from app.video_lab.job_run import (
    JobRun,
    JOB_STAGE_COMPOSE,
    JOB_STAGE_FAILED,
    JOB_STAGE_MANIFEST,
    JOB_STAGE_PLANNING,
    JOB_STAGE_SUBTITLE,
    JOB_STAGE_TTS,
    JOB_STAGE_VISUAL_RENDER,
    new_job_id,
)
from app.video_lab.renderers.visual_profiles import merge_visual_profile
from app.video_lab.run_context import RunContext

logger = logging.getLogger(__name__)


def run_visual_compose_contract(
    content: str,
    visual_route: str,
    params_in: dict | None,
) -> dict[str, Any]:
    """
    Run ONE visual route end-to-end (LLM plan + TTS + 字幕 + 合成) and return a
    UI-ready result dict (finalVideoUrl + coverUrl + quality + steps).

    Reused by: POST /visual-compose (single route) and POST /technique-probe (multi-route probe).
    Business failures do not raise exceptions; they return status='failed' + failedReason.

    V1 contract: returns runId / success / status / contractStatus / artifacts / error / rawOutput.
    V1.0.4: also returns jobRun (sync task status tracking).

    Args:
        content: article/text content to render
        visual_route: route id (e.g. "local_frame_compose")
        params_in: optional dict of render parameters

    Returns:
        V1 contract dict with all required fields, including jobRun.
    """
    run_ctx = RunContext(mode="compose", route_id=visual_route)

    # V1.0.4: Create JobRun for sync task status tracking.
    # Reuses run_id / experiment_id from RunContext to keep IDs aligned.
    job_run = JobRun(
        job_id=new_job_id(),
        run_id=run_ctx.run_id,
        experiment_id=run_ctx.experiment_id,
        mode=run_ctx.mode,
        route_id=visual_route,
    )
    job_run.mark_running(stage=JOB_STAGE_PLANNING, progress=10)
    job_run.log(f"[job {job_run.job_id}] starting visual-compose route={visual_route}")

    params = dict(params_in or {})
    params["visualRoute"] = visual_route

    # V1 VisualProfile: merge profile defaults, explicit params take priority
    merged_profile, profile_warnings = merge_visual_profile(
        params.get("visualProfile"),
        params,
    )
    # Apply merged params back — explicit params already in params win over profile defaults
    for k, v in merged_profile.items():
        if k not in params:
            params[k] = v
    run_ctx.render_params = params
    run_ctx.input_snapshot = {"content": content}
    run_ctx.warnings.extend(profile_warnings)

    job_run.advance(JOB_STAGE_TTS, 25)
    job_run.log("[job] entering TTS + subtitle stage")
    result = run_tts_subtitle_compose(
        experiment_id=run_ctx.experiment_id,
        test_case_id="case_ai_frontier_daily_001",
        input_payload={"content": content},
        params=params,
    )

    raw = getattr(result, "rawOutput", {}) or {}
    assets = getattr(result, "assets", {}) or {}
    status = raw.get("status", "unknown")
    run_ctx.status = status
    failed_reason = ""
    if status != "succeeded":
        for step in getattr(result, "productionSteps", []):
            if getattr(step, "status", None) and step.status.value == "failed":
                failed_reason = step.outputSummary or step.name
                break
        failed_reason = failed_reason or raw.get("error", "")

    # Merge result.logs into run_ctx.logs (deduplicate)
    result_logs: list[str] = getattr(result, "logs", []) or []
    seen = set(run_ctx.logs)
    for line in result_logs:
        if line not in seen:
            run_ctx.log(line)
            seen.add(line)
    # Also surface factory logs into JobRun for stage observability
    for line in result_logs:
        job_run.log(f"[factory] {line}")

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

    final_video_url = getattr(result, "videoUrl", "") or ""
    cover_url = getattr(result, "coverUrl", "") or ""

    # Derive JobRun stage from productionSteps (best-effort)
    step_names = {s["name"] for s in steps_summary if s.get("name")}
    if any("plan" in n.lower() or "llm" in n.lower() for n in step_names):
        job_run.advance(JOB_STAGE_PLANNING, 30)
    if any("tts" in n.lower() for n in step_names):
        job_run.advance(JOB_STAGE_TTS, 50)
    if any("subtitle" in n.lower() or "srt" in n.lower() for n in step_names):
        job_run.advance(JOB_STAGE_SUBTITLE, 60)
    if any("render" in n.lower() or "frame" in n.lower() or "visual" in n.lower() for n in step_names):
        job_run.advance(JOB_STAGE_VISUAL_RENDER, 75)
    if any("compose" in n.lower() or "mux" in n.lower() for n in step_names):
        job_run.advance(JOB_STAGE_COMPOSE, 85)

    # Write experiment manifest (success or failure)
    manifest = build_experiment_manifest(
        experiment_id=run_ctx.experiment_id,
        run_id=run_ctx.run_id,
        mode=run_ctx.mode,
        route_id=visual_route,
        status=status,
        input_data=run_ctx.input_snapshot,
        artifacts={
            "cover": cover_url,
            "frames": [],
            "silentVideo": None,
            "audio": audio_url,
            "subtitles": srt_url,
            "finalVideo": final_video_url,
            "manifest": manifest_url,
        },
        logs=run_ctx.logs,
        warnings=run_ctx.warnings,
        raw_output=raw,
        error=make_error(failed_reason, type="ComposeError", code="VIDEO_LAB_COMPOSE_FAILED",
                         stage="compose", route=visual_route) if status != "succeeded" else None,
    )
    job_run.advance(JOB_STAGE_MANIFEST, 90)
    try:
        mw = write_experiment_manifest(run_ctx.experiment_id, manifest)
        run_ctx.artifacts["manifestUrl"] = mw["url"]
    except Exception:
        logger.warning("manifest write failed (non-fatal)", exc_info=True)

    try:
        from app.video_lab.quality.quality_log import append_record
        _q = raw.get("quality", {}) or {}
        append_record({
            "kind": "structural",
            "route": visual_route,
            "experimentId": run_ctx.experiment_id,
            "status": status,
            "overall": _q.get("overallScore"),
            "dimensions": _q.get("dimensionScores", {}),
            "durationSec": assets.get("audioDurationSec", 0),
            "subtitleCount": assets.get("subtitleCount", 0),
            "contentChars": len(content),
            "params": params,
        })
    except Exception:
        logger.warning("structural quality logging failed (non-fatal)", exc_info=True)

    # Build V1 base
    v1_success = status == "succeeded"
    v1_base = {
        **run_ctx.to_response_base(),
        "success": v1_success,
        "status": status,
        "contractStatus": "success" if v1_success else "failed",
    }

    # V1 artifacts (mirrors top-level asset fields for easy consumption)
    v1_artifacts = {
        "finalVideoUrl": final_video_url,
        "coverUrl": cover_url,
        "audioUrl": audio_url,
        "srtUrl": srt_url,
        "manifestUrl": run_ctx.artifacts.get("manifestUrl", ""),
    }

    if v1_success:
        job_run.mark_succeeded()
        job_run.set_artifact("finalVideoUrl", final_video_url)
        job_run.set_artifact("coverUrl", cover_url)
        job_run.set_artifact("manifestUrl", run_ctx.artifacts.get("manifestUrl", ""))
        return {
            **v1_base,
            "artifacts": v1_artifacts,
            "experimentId": run_ctx.experiment_id,
            "visualRoute": visual_route,
            "params": params,
            "finalVideoUrl": final_video_url,
            "coverUrl": cover_url,
            "audioUrl": audio_url,
            "srtUrl": srt_url,
            "manifestUrl": manifest_url,
            "audioDurationSec": assets.get("audioDurationSec", 0),
            "subtitleCount": assets.get("subtitleCount", 0),
            "quality": raw.get("quality", {}),
            "failedReason": "",
            "warnings": raw.get("warnings", []) or run_ctx.warnings,
            "steps": steps_summary,
            "logs": run_ctx.logs,
            "error": None,
            "rawOutput": raw,
            "jobRun": job_run.to_dict(),
        }
    else:
        job_run.mark_failed(
            error=make_error(
                failed_reason,
                type="ComposeError",
                code="VIDEO_LAB_COMPOSE_FAILED",
                stage="compose",
                route=visual_route,
            )
        )
        return {
            **v1_base,
            "artifacts": v1_artifacts,
            "experimentId": run_ctx.experiment_id,
            "visualRoute": visual_route,
            "params": params,
            "finalVideoUrl": "",
            "coverUrl": "",
            "audioUrl": audio_url,
            "srtUrl": srt_url,
            "manifestUrl": manifest_url,
            "audioDurationSec": 0,
            "subtitleCount": 0,
            "quality": {},
            "failedReason": failed_reason,
            "warnings": raw.get("warnings", []) or run_ctx.warnings,
            "steps": steps_summary,
            "logs": run_ctx.logs,
            "error": make_error(
                failed_reason,
                type="ComposeError",
                code="VIDEO_LAB_COMPOSE_FAILED",
                stage="compose",
                route=visual_route,
            ),
            "rawOutput": raw,
            "jobRun": job_run.to_dict(),
        }


def run_visual_compose_endpoint(request) -> dict[str, Any]:
    """
    /visual-compose endpoint handler.

    Run ONE visual route end-to-end (LLM plan + TTS + 字幕 + 合成) and return
    the final video URL + auto quality report.

    Synchronous: returns after the video is produced (TTS/render may take minutes).
    Business failures return HTTP 200 with status='failed' + failedReason.
    V1 contract: always returns success/status/contractStatus/artifacts/error/rawOutput.
    V1.0.4: also returns jobRun even on outer exception (status=failed, stage=failed).

    Args:
        request: VisualComposeRequest object

    Returns:
        V1 contract dict (same shape as run_visual_compose_contract), plus jobRun.
    """
    import traceback
    from app.video_lab.job_run import (
        JobRun as _JobRun,
        JOB_STAGE_FAILED,
        new_job_id as _new_job_id,
    )
    from app.video_lab.run_context import RunContext

    run_ctx = RunContext(mode="compose", route_id=request.visualRoute)
    run_ctx.input_snapshot = {"content": request.content}

    # Pre-create JobRun so we can return it even if the contract raises.
    job_run = _JobRun(
        job_id=_new_job_id(),
        run_id=run_ctx.run_id,
        experiment_id=run_ctx.experiment_id,
        mode=run_ctx.mode,
        route_id=request.visualRoute,
    )

    try:
        return run_visual_compose_contract(request.content, request.visualRoute, request.params)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("[visual-compose] exception", exc_info=True)
        run_ctx.log(f"[visual-compose] exception: {type(e).__name__}: {e}\n{tb}")
        run_ctx.mark_failed()

        err = make_error(
            str(e),
            type=type(e).__name__,
            code="VIDEO_LAB_INTERNAL_ERROR",
            stage="compose",
            route=request.visualRoute,
        )
        job_run.mark_failed(error=err, stage=JOB_STAGE_FAILED, progress=100)
        job_run.log(f"[visual-compose] outer exception: {type(e).__name__}: {e}")

        return {
            "success": False,
            "status": "failed",
            "contractStatus": "failed",
            **run_ctx.to_response_base(),
            "artifacts": {},
            "logs": run_ctx.logs,
            "warnings": run_ctx.warnings,
            "error": err,
            "rawOutput": {},
            "jobRun": job_run.to_dict(),
        }
