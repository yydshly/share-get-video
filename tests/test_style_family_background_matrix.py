"""Regression tests for the Remotion Style Family background matrix."""

import re
from pathlib import Path
from types import SimpleNamespace

import app.video_lab.services.style_family_service as style_family_service


PROJECT_ROOT = Path(__file__).parent.parent
PAGE_PATH = (
    PROJECT_ROOT
    / "frontend"
    / "src"
    / "video-lab"
    / "pages"
    / "RemotionStyleFamilyPage.tsx"
)
LAB_PAGE_PATH = (
    PROJECT_ROOT
    / "frontend"
    / "src"
    / "video-lab"
    / "pages"
    / "RemotionLabPage.tsx"
)


def test_style_family_page_default_background_matrix_stays_within_backend_limit():
    """The UI displays every background with one fixed family, within the limit."""
    source = PAGE_PATH.read_text(encoding="utf-8")

    families_block = re.search(
        r"const MATRIX_FAMILIES = \[(.*?)\];",
        source,
        flags=re.DOTALL,
    )
    backgrounds_block = re.search(
        r"const MATRIX_BACKGROUNDS = \[(.*?)\];",
        source,
        flags=re.DOTALL,
    )

    assert families_block is not None
    assert backgrounds_block is not None

    family_ids = re.findall(r'\bid:\s*"([^"]+)"', families_block.group(1))
    background_ids = re.findall(r'\bid:\s*"([^"]+)"', backgrounds_block.group(1))

    assert family_ids == ["timeline_news"]
    assert set(background_ids) == set(style_family_service.VALID_BACKGROUND_PRESETS)
    assert len(family_ids) * len(background_ids) <= style_family_service.MAX_MATRIX_ITEMS


def test_background_matrix_accepts_the_page_default_1x6_request(monkeypatch):
    """The backend accepts and renders all six backgrounds sent by the page."""
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

    monkeypatch.setattr(
        style_family_service,
        "render_clip_preview",
        fake_render_clip_preview,
    )

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
    assert {
        item["backgroundPreset"] for item in result["items"]
    } == set(style_family_service.VALID_BACKGROUND_PRESETS)


def test_remotion_lab_background_matrix_submits_every_listed_background():
    """The Remotion Lab request must derive its presets from the full UI list."""
    source = LAB_PAGE_PATH.read_text(encoding="utf-8")

    backgrounds_block = re.search(
        r"const BACKGROUNDS = \[(.*?)\];",
        source,
        flags=re.DOTALL,
    )

    assert backgrounds_block is not None
    background_ids = re.findall(r'\bid:\s*"([^"]+)"', backgrounds_block.group(1))

    assert set(background_ids) == set(style_family_service.VALID_BACKGROUND_PRESETS)
    assert "backgroundPresets: BACKGROUNDS.map((background) => background.id)" in source
    assert "运行完整背景矩阵（1 family × 6 backgrounds）" in source
