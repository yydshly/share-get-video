"""
style_sweep_promotion_service.py
Stage 2A: Promote Style Sweep results to Style Gallery samples.

Does NOT regenerate any video/TTS/AI assets.
Does NOT call Remotion, FFmpeg, or any render pipeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.video_lab.style_gallery.models import (
    StyleSample,
    SampleStatus,
    SampleSource,
    SampleGenerationMeta,
    SampleAssetMeta,
    SampleQualityMeta,
    StyleSampleOutput,
)
from app.video_lab.style_gallery import store as sg_store
from app.video_lab.style_sweep_jobs import get_sweep_job


# ─── Idempotency helper ───────────────────────────────────────────────────────

def _find_sample_by_sweep_ref(
    sweep_job_id: str,
    style_id: str,
) -> str | None:
    """Return sample_id if a sample already exists for this sweep job + style_id."""
    # V1.2.3: Use direct store lookup — no limit cap (previously had limit=200 which
    # could miss samples when the store grew beyond 200 style_sweep entries).
    sample = sg_store.find_sample_by_source(
        source_type="style_sweep",
        job_id=sweep_job_id,
        run_id=style_id,
    )
    return sample.id if sample else None


# ─── Core promotion logic ─────────────────────────────────────────────────────

def promote_sweep_results_to_gallery(
    job_id: str,
    style_ids: list[str],
    *,
    target_status: str = "candidate",
    note: str = "",
) -> dict[str, Any]:
    """Promote one or more successful Style Sweep results as Style Gallery samples.

    Parameters
    ----------
    job_id
        Style Sweep job ID (e.g. ``sweep_30d80edad1f5``).
    style_ids
        List of styleId values from the job results to promote.
    target_status
        Initial ``status`` for the new samples. Defaults to ``candidate``.
    note
        Optional note stored in source.saved_from.

    Returns
    -------
    dict with keys:
        - jobId: str
        - promotedCount: int
        - skippedCount: int
        - samples: list[dict]  (each has sampleId, styleId, routeId, reused)
        - skipped: list[dict]  (each has styleId, reason)

    Does NOT re-render anything. Re-uses finalVideoUrl / manifestUrl / audioUrl /
    srtUrl / assUrl / coverUrl from the existing job result.
    """
    # 1. Load job
    job = get_sweep_job(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    if not style_ids:
        raise ValueError("styleIds must not be empty")

    # Build a lookup from styleId → StyleResultEntry
    results_map: dict[str, Any] = {
        r.styleId: r for r in job.results
    }

    promoted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for style_id in style_ids:
        entry = results_map.get(style_id)

        # ── reason: not found ───────────────────────────────────────────────
        if entry is None:
            skipped.append({"styleId": style_id, "reason": "style_id_not_found"})
            continue

        result = entry.result or {}

        # ── reason: not succeeded ───────────────────────────────────────────
        if result.get("status") != "succeeded":
            skipped.append({"styleId": style_id, "reason": "result_not_succeeded"})
            continue

        # ── reason: missing video url ───────────────────────────────────────
        video_url = result.get("finalVideoUrl") or result.get("videoUrl") or ""
        if not video_url:
            skipped.append({"styleId": style_id, "reason": "no_video_url"})
            continue

        # ── idempotency: already promoted ───────────────────────────────────
        existing_sample_id = _find_sample_by_sweep_ref(job_id, style_id)
        if existing_sample_id:
            promoted.append({
                "sampleId": existing_sample_id,
                "styleId": style_id,
                "routeId": job.routeId,
                "reused": True,
            })
            continue

        # ── collect fields ─────────────────────────────────────────────────
        manifest_url = result.get("manifestUrl") or ""
        audio_url = result.get("audioUrl") or ""
        srt_url = result.get("srtUrl") or ""
        ass_url = result.get("assUrl") or ""
        cover_url = result.get("coverUrl") or ""
        raw_output = result.get("rawOutput") or {}
        subtitle_diagnostics = raw_output.get("subtitleDiagnostics") or {}

        # Params: prefer result.params (merged), fall back to job-level params
        params = result.get("params") or job.params or {}

        # Tags
        tags = list(entry.tags) if entry.tags else []
        tags.extend([job.routeId, style_id, "style_sweep"])
        if job.routeId:
            tags.append(job.routeId)
        # If manual mark says "ok", tag as validated
        manual_mark = job.manualMarks.get(style_id)
        if manual_mark and isinstance(manual_mark, dict):
            issues = manual_mark.get("issues") or []
            if "ok" in issues:
                tags.append("validated_candidate")

        # ── build SampleSource ───────────────────────────────────────────────
        source = SampleSource(
            source_type="style_sweep",
            source_page="style_sweep",
            job_id=job_id,
            run_id=style_id,
            saved_from=note,
        )

        # ── build SampleGenerationMeta ──────────────────────────────────────
        generation = SampleGenerationMeta(
            visual_route=job.routeId,
            route_preset=style_id,
            aspect_ratio=params.get("aspectRatio", ""),
            output_aspect_ratio=params.get("outputAspectRatio", ""),
            display_aspect_ratio=params.get("displayAspectRatio", ""),
            fit_mode=params.get("fitMode", ""),
            target_duration=params.get("targetDuration", 0.0),
        )

        # ── build SampleAssetMeta ───────────────────────────────────────────
        asset_meta = SampleAssetMeta(
            final_video_url=video_url,
            cover_url=cover_url,
            audio_url=audio_url,
            srt_url=srt_url,
            manifest_url=manifest_url,
            aspect_ratio=params.get("aspectRatio", ""),
            display_aspect_ratio=params.get("displayAspectRatio", ""),
            fit_mode=params.get("fitMode", ""),
        )

        # ── build SampleQualityMeta ─────────────────────────────────────────
        quality_meta = SampleQualityMeta(
            warnings=result.get("warnings") or [],
            steps=result.get("steps") or [],
        )

        # ── resolve status ─────────────────────────────────────────────────
        try:
            status = SampleStatus(target_status)
        except ValueError:
            status = SampleStatus.CANDIDATE

        # ── build StyleSample ───────────────────────────────────────────────
        sample_id = f"sample_{uuid.uuid4().hex[:12]}"

        # content_preview from job
        content_preview = job.contentPreview or ""

        # ── output: store relative path if possible, fall back to full URL ──
        output_path = video_url if video_url.startswith("runtime/") or video_url.startswith("/runtime/") else video_url
        sample_output = StyleSampleOutput(
            type="mp4",
            path=output_path,
            poster=cover_url,
            audio_url=audio_url,
            srt_url=srt_url,
            manifest_url=manifest_url,
        )

        sample = StyleSample(
            id=sample_id,
            route_id=job.routeId,
            route_name=job.routeName,
            style_name=entry.styleName,
            description=entry.description or "",
            status=status,
            params=params,
            output=sample_output,
            tags=tags,
            content_preview=content_preview[:100],
            created_at=datetime.now(timezone.utc),
            source=source,
            generation=generation,
            asset_meta=asset_meta,
            quality_meta=quality_meta,
            # job_run stores sweep job reference + manualMark + all asset refs
            job_run={
                "sweep_job_id": job_id,
                "style_id": style_id,
                "manual_mark": manual_mark,
                "subtitle_diagnostics": subtitle_diagnostics,
                "note": note,
                "asset_refs": {
                    "video_url": video_url,
                    "manifest_url": manifest_url,
                    "audio_url": audio_url,
                    "srt_url": srt_url,
                    "ass_url": ass_url,
                    "cover_url": cover_url,
                },
            },
        )

        sg_store.save_sample(sample)

        promoted.append({
            "sampleId": sample_id,
            "styleId": style_id,
            "routeId": job.routeId,
            "videoUrl": video_url,
            "manifestUrl": manifest_url,
            "source": "style_sweep",
            "sweepJobId": job_id,
            "reused": False,
        })

    return {
        "jobId": job_id,
        "promotedCount": len(promoted),
        "skippedCount": len(skipped),
        "samples": promoted,
        "skipped": skipped,
    }
