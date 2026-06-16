"""
Clip Preview Service — extracted from router.py V1.0.2.

Provides run_clip_preview_contract() which implements the /clip-preview business logic.
V1 contract: always returns success/status/contractStatus/artifacts/error/rawOutput.
V1.0.4: also returns jobRun (JobRun v1 status contract).
"""

import logging
import traceback
from typing import Any

from app.video_lab.errors import make_error
from app.video_lab.experiment_manifest import build_experiment_manifest, write_experiment_manifest
from app.video_lab.job_run import (
    JobRun,
    JOB_STAGE_FAILED,
    JOB_STAGE_MANIFEST,
    JOB_STAGE_VISUAL_RENDER,
    new_job_id,
)
from app.video_lab.renderers.frame_preview import render_clip_preview
from app.video_lab.renderers.visual_profiles import merge_visual_profile
from app.video_lab.run_context import RunContext

logger = logging.getLogger(__name__)


def run_clip_preview_contract(request) -> dict[str, Any]:
    """
    Render a short (~3s) animated clip.

    - Remotion: renders the first few seconds of real animation
    - Pillow / AI素材: Ken Burns (slow zoom + fade-in)

    V1 contract: always returns success/status/contractStatus/artifacts/error/rawOutput.
    V1.0.4: also returns jobRun (sync task status tracking).

    Args:
        request: ClipPreviewRequest object

    Returns:
        dict with V1 contract fields, plus jobRun.
    """
    run_ctx = RunContext(
        mode="preview",
        route_id=request.visualRoute,
    )

    # V1.0.4: Create JobRun for sync task status tracking.
    job_run = JobRun(
        job_id=new_job_id(),
        run_id=run_ctx.run_id,
        experiment_id=run_ctx.experiment_id,
        mode=run_ctx.mode,
        route_id=request.visualRoute,
    )
    job_run.mark_running(stage=JOB_STAGE_VISUAL_RENDER, progress=30)
    job_run.log(f"[job {job_run.job_id}] starting clip-preview route={request.visualRoute}")

    params = dict(request.params or {})

    # V1 VisualProfile: merge profile defaults
    merged_params, profile_warnings = merge_visual_profile(params.get("visualProfile"), params)
    for k, v in merged_params.items():
        if k not in params:
            params[k] = v
    run_ctx.render_params = params
    run_ctx.warnings.extend(profile_warnings)

    try:
        raw = render_clip_preview(
            content=request.content,
            visual_route=request.visualRoute,
            params=params,
            clip_seconds=int(params.get("clipSeconds", 3)),
            shot=request.shot,
            frame_type=request.frameType,
            cover_title=request.coverTitle,
        )

        success = raw.get("success", False)
        run_ctx.status = "success" if success else "failed"

        clip_url = raw.get("clipUrl", "") or ""

        # Advance JobRun to manifest stage
        job_run.advance(JOB_STAGE_MANIFEST, 85)

        # Write experiment manifest (success or failure)
        manifest = build_experiment_manifest(
            experiment_id=run_ctx.experiment_id,
            run_id=run_ctx.run_id,
            mode=run_ctx.mode,
            route_id=request.visualRoute,
            status="success" if success else "failed",
            input_data={"content": request.content},
            artifacts={
                "cover": None,
                "frames": [],
                "silentVideo": clip_url,
                "audio": None,
                "subtitles": None,
                "finalVideo": clip_url,
                "manifest": None,
            },
            logs=run_ctx.logs,
            warnings=run_ctx.warnings,
            raw_output=raw,
            error=None if success else make_error(
                raw.get("message", "Clip preview failed"),
                type="RenderError",
                code="VIDEO_LAB_CLIP_PREVIEW_FAILED",
                stage="visual_render",
                route=request.visualRoute,
            ),
        )
        try:
            mw = write_experiment_manifest(run_ctx.experiment_id, manifest)
            manifest_url = mw["url"]
        except Exception:
            logger.warning("clip-preview manifest write failed (non-fatal)", exc_info=True)
            manifest_url = ""

        if success:
            job_run.mark_succeeded()
            job_run.set_artifact("videoUrl", clip_url)
            job_run.set_artifact("manifestUrl", manifest_url)
            return {
                "success": True,
                "status": "success",
                "contractStatus": "success",
                **run_ctx.to_response_base(),
                "artifacts": {
                    "videoUrl": clip_url,
                    "coverUrl": "",
                    "manifestUrl": manifest_url,
                },
                "logs": run_ctx.logs,
                "warnings": raw.get("warnings", []) or run_ctx.warnings,
                "error": None,
                "rawOutput": raw,
                "jobRun": job_run.to_dict(),
            }
        else:
            err = make_error(
                raw.get("message", "Clip preview failed"),
                type="RenderError",
                code="VIDEO_LAB_CLIP_PREVIEW_FAILED",
                stage="visual_render",
                route=request.visualRoute,
            )
            job_run.mark_failed(error=err, stage=JOB_STAGE_FAILED, progress=100)
            return {
                "success": False,
                "status": "failed",
                "contractStatus": "failed",
                **run_ctx.to_response_base(),
                "artifacts": {
                    "videoUrl": "",
                    "coverUrl": "",
                    "manifestUrl": manifest_url,
                },
                "logs": run_ctx.logs,
                "warnings": raw.get("warnings", []) or run_ctx.warnings,
                "error": err,
                "rawOutput": raw,
                "jobRun": job_run.to_dict(),
            }

    except Exception as e:
        tb = traceback.format_exc()
        logger.error("[clip-preview] render failed", exc_info=True)
        run_ctx.log(f"[clip-preview] exception: {type(e).__name__}: {e}\n{tb}")
        run_ctx.mark_failed()

        err = make_error(
            str(e),
            type=type(e).__name__,
            code="VIDEO_LAB_INTERNAL_ERROR",
            stage="clip_preview",
            route=request.visualRoute,
        )
        job_run.mark_failed(error=err, stage=JOB_STAGE_FAILED, progress=100)
        job_run.log(f"[clip-preview] outer exception: {type(e).__name__}: {e}")

        # Try to write a failed manifest even on early exception
        manifest_url = ""
        try:
            mfail = build_experiment_manifest(
                experiment_id=run_ctx.experiment_id,
                run_id=run_ctx.run_id,
                mode=run_ctx.mode,
                route_id=request.visualRoute,
                status="failed",
                input_data={"content": request.content},
                artifacts={},
                logs=run_ctx.logs,
                warnings=run_ctx.warnings,
                error=err,
            )
            mw = write_experiment_manifest(run_ctx.experiment_id, mfail)
            manifest_url = mw["url"]
        except Exception:
            logger.warning("clip-preview failed manifest write also failed (non-fatal)", exc_info=True)

        return {
            "success": False,
            "status": "failed",
            "contractStatus": "failed",
            **run_ctx.to_response_base(),
            "artifacts": {
                "videoUrl": "",
                "coverUrl": "",
                "manifestUrl": manifest_url,
            },
            "logs": run_ctx.logs,
            "warnings": run_ctx.warnings,
            "error": err,
            "rawOutput": {},
            "jobRun": job_run.to_dict(),
        }
