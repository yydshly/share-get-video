"""Regression tests for the Remotion Style Family background matrix."""

import re
import time
from pathlib import Path
from types import SimpleNamespace

import app.video_lab.background_matrix_jobs as background_matrix_jobs
import app.video_lab.services.style_family_service as style_family_service


PROJECT_ROOT = Path(__file__).parent.parent
PAGE_PATH = PROJECT_ROOT / "frontend" / "src" / "video-lab" / "pages" / "RemotionStyleFamilyPage.tsx"
LAB_PAGE_PATH = PROJECT_ROOT / "frontend" / "src" / "video-lab" / "pages" / "RemotionLabPage.tsx"


def test_style_family_page_default_background_matrix_stays_within_backend_limit():
    source = PAGE_PATH.read_text(encoding="utf-8")
    families_block = re.search(r"const MATRIX_FAMILIES = \[(.*?)\];", source, flags=re.DOTALL)
    backgrounds_block = re.search(r"const MATRIX_BACKGROUNDS = \[(.*?)\];", source, flags=re.DOTALL)

    assert families_block is not None
    assert backgrounds_block is not None
    family_ids = re.findall(r'\bid:\s*"([^"]+)"', families_block.group(1))
    background_ids = re.findall(r'\bid:\s*"([^"]+)"', backgrounds_block.group(1))

    assert family_ids == ["timeline_news"]
    assert set(background_ids) == set(style_family_service.VALID_BACKGROUND_PRESETS)
    assert len(family_ids) * len(background_ids) <= style_family_service.MAX_MATRIX_ITEMS


def test_background_matrix_accepts_the_page_default_1x6_request(monkeypatch):
    calls = []

    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        calls.append(dict(params))
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": f"exp_{len(calls)}",
            "clipSeconds": clip_seconds,
            "elapsedMs": 1,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)
    request = SimpleNamespace(
        content="",
        params={"clipSeconds": 3, "keyPointCount": 3},
        matrix={
            "families": ["timeline_news"],
            "backgroundPresets": style_family_service.VALID_BACKGROUND_PRESETS,
        },
    )

    result = style_family_service.run_background_variant_matrix(request)

    assert len(result["items"]) == 6
    assert len(calls) == 6
    assert {item["backgroundPreset"] for item in result["items"]} == set(
        style_family_service.VALID_BACKGROUND_PRESETS
    )


def test_remotion_lab_background_matrix_uses_async_job():
    source = LAB_PAGE_PATH.read_text(encoding="utf-8")
    backgrounds_block = re.search(r"const BACKGROUNDS = \[(.*?)\];", source, flags=re.DOTALL)

    assert backgrounds_block is not None
    background_ids = re.findall(r'\bid:\s*"([^"]+)"', backgrounds_block.group(1))
    assert set(background_ids) == set(style_family_service.VALID_BACKGROUND_PRESETS)
    assert "runBackgroundMatrixJob<BackgroundMatrixItem>" in source
    assert "backgroundPresets: BACKGROUNDS.map" in source
    assert "setResult({" in source


def test_style_family_background_matrix_uses_async_job():
    source = PAGE_PATH.read_text(encoding="utf-8")

    assert "runBackgroundMatrixJob<MatrixItem>" in source
    assert "families: MATRIX_FAMILIES.map" in source
    assert "backgroundPresets: MATRIX_BACKGROUNDS.map" in source
    assert "setMatrixResult({" in source


def test_background_matrix_job_returns_immediately_and_reports_progress(monkeypatch):
    calls = []

    def fake_run(request):
        background = request.matrix["backgroundPresets"][0]
        calls.append(background)
        time.sleep(0.02)
        return {
            "items": [{
                "family": request.matrix["families"][0],
                "backgroundPreset": background,
                "success": True,
                "videoUrl": f"/runtime/{background}.mp4",
                "elapsedMs": 20,
                "message": "",
                "warnings": [],
            }],
            "totalElapsedMs": 20,
        }

    monkeypatch.setattr(background_matrix_jobs, "run_background_variant_matrix", fake_run)
    request = SimpleNamespace(
        content="test",
        params={"clipSeconds": 2},
        matrix={
            "families": ["timeline_news"],
            "backgroundPresets": ["tech_grid_dark", "aurora_blue"],
        },
    )

    created = background_matrix_jobs.create_background_matrix_job(request)
    assert created["status"] in {"pending", "running"}
    assert created["completed"] == 0

    deadline = time.time() + 2
    job = created
    while time.time() < deadline:
        job = background_matrix_jobs.get_background_matrix_job(created["jobId"])
        if job and job["status"] == "completed":
            break
        time.sleep(0.01)

    assert job is not None
    assert job["status"] == "completed"
    assert job["completed"] == 2
    assert len(job["items"]) == 2
    assert calls == ["tech_grid_dark", "aurora_blue"]
