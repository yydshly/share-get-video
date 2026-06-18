from types import SimpleNamespace
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
import app.video_lab.services.style_family_service as style_family_service


PROJECT_ROOT = Path(__file__).parent.parent
STYLE_FAMILY_PAGE_PATH = (
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


def test_transition_variant_matrix_passes_transition_params(monkeypatch):
    captured = []

    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        captured.append({
            "content": content,
            "visual_route": visual_route,
            "params": dict(params),
            "clip_seconds": clip_seconds,
        })
        return {
            "success": True,
            "clipUrl": f"/runtime/{params['remotionFamily']}_{params['transitionStyle']}.mp4",
            "experimentId": f"exp_{len(captured)}",
            "clipSeconds": clip_seconds,
            "elapsedMs": 12,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)

    request = SimpleNamespace(
        content="",
        params={"clipSeconds": 2, "keyPointCount": 2, "backgroundPreset": "tech_grid_dark"},
        matrix={
            "families": ["data_news", "caption_story"],
            "transitionStyles": ["push", "wipe"],
        },
    )

    result = style_family_service.run_transition_variant_matrix(request)

    assert len(result["items"]) == 4
    assert {item["transitionStyle"] for item in result["items"]} == {"push", "wipe"}
    assert {item["family"] for item in result["items"]} == {"data_news", "caption_story"}
    assert all(call["visual_route"] == "template_programmatic_render" for call in captured)
    assert all(call["params"]["visualRoute"] == "template_programmatic_render" for call in captured)
    assert all(call["params"]["backgroundPreset"] == "tech_grid_dark" for call in captured)


def test_transition_matrix_endpoint_filters_to_supported_values(monkeypatch):
    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": "exp_test",
            "clipSeconds": clip_seconds,
            "elapsedMs": 1,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)
    client = TestClient(app)

    resp = client.post(
        "/video-lab/style-family/transition-matrix",
        json={
            "content": "one: body\ntwo: body",
            "params": {"clipSeconds": 1, "keyPointCount": 2},
            "matrix": {
                "families": ["data_news", "unknown_family"],
                "transitionStyles": ["zoom_blur", "flip", "glitch", "bad_transition"],
            },
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 3
    assert data["items"][0]["family"] == "data_news"
    assert {item["transitionStyle"] for item in data["items"]} == {"zoom_blur", "flip", "glitch"}


def test_transition_matrix_accepts_all_supported_transitions(monkeypatch):
    """One family × all eight transitions remains below the nine-item limit."""
    captured = []

    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        captured.append(dict(params))
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": f"exp_{len(captured)}",
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
        params={
            "clipSeconds": 2,
            "keyPointCount": 2,
            "backgroundPreset": "tech_grid_dark",
        },
        matrix={
            "families": ["data_news"],
            "transitionStyles": style_family_service.VALID_TRANSITION_STYLES,
        },
    )

    result = style_family_service.run_transition_variant_matrix(request)

    assert len(result["items"]) == 8
    assert len(captured) == 8
    assert {
        item["transitionStyle"] for item in result["items"]
    } == set(style_family_service.VALID_TRANSITION_STYLES)


def test_both_remotion_pages_submit_every_listed_transition():
    """Both UIs derive transition requests from their complete visible lists."""
    style_family_source = STYLE_FAMILY_PAGE_PATH.read_text(encoding="utf-8")
    lab_source = LAB_PAGE_PATH.read_text(encoding="utf-8")

    style_family_block = re.search(
        r"const MATRIX_TRANSITIONS = \[(.*?)\];",
        style_family_source,
        flags=re.DOTALL,
    )
    lab_block = re.search(
        r"const TRANSITIONS = \[(.*?)\];",
        lab_source,
        flags=re.DOTALL,
    )

    assert style_family_block is not None
    assert lab_block is not None

    style_family_ids = re.findall(
        r'\bid:\s*"([^"]+)"',
        style_family_block.group(1),
    )
    lab_ids = re.findall(r'\bid:\s*"([^"]+)"', lab_block.group(1))
    expected = set(style_family_service.VALID_TRANSITION_STYLES)

    assert set(style_family_ids) == expected
    assert set(lab_ids) == expected
    assert (
        "transitionStyles: MATRIX_TRANSITIONS.map((transition) => transition.id)"
        in style_family_source
    )
    assert (
        "transitionStyles: TRANSITIONS.map((transition) => transition.id)"
        in lab_source
    )
