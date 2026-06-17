"""
tests/test_style_family_visual_technique_matrix.py
V1.2.4: Tests for visual technique matrix endpoint and service (academic_sketch).
"""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
import app.video_lab.services.style_family_service as style_family_service


def test_visual_technique_matrix_passes_technique_params(monkeypatch):
    """run_visual_technique_matrix should pass visualTechnique=academic_sketch to render_clip_preview."""
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
            "clipUrl": f"/runtime/{params['remotionFamily']}_{params['visualTechnique']}.mp4",
            "experimentId": f"exp_{len(captured)}",
            "clipSeconds": clip_seconds,
            "elapsedMs": 12,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)

    request = SimpleNamespace(
        content="Test content",
        params={"clipSeconds": 2, "keyPointCount": 2},
        matrix={
            "families": ["caption_story", "data_news"],
            "visualTechniques": ["academic_sketch"],
        },
    )

    result = style_family_service.run_visual_technique_matrix(request)

    # 2 families × 1 technique = 2 items
    assert len(result["items"]) == 2
    # All items should have visualTechnique=academic_sketch in params
    assert all(call["params"]["visualTechnique"] == "academic_sketch" for call in captured)
    assert all(call["params"]["visualStylePreset"] == "warm_paper" for call in captured)
    assert all(call["params"]["backgroundPreset"] == "warm_cinematic" for call in captured)


def test_visual_technique_matrix_injects_defaults(monkeypatch):
    """Service should inject warm_paper / warm_cinematic / slide_fade defaults when not set."""
    captured = []

    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        captured.append(dict(params))
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": "exp_1",
            "clipSeconds": 2,
            "elapsedMs": 10,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)

    request = SimpleNamespace(
        content="Test",
        params={"clipSeconds": 2, "keyPointCount": 2},
        matrix={
            "families": ["timeline_news"],
            "visualTechniques": ["academic_sketch"],
        },
    )

    style_family_service.run_visual_technique_matrix(request)

    assert len(captured) == 1
    assert captured[0]["visualStylePreset"] == "warm_paper"
    assert captured[0]["backgroundPreset"] == "warm_cinematic"
    assert captured[0]["transitionStyle"] == "slide_fade"


def test_visual_technique_matrix_3_clips_at_limit(monkeypatch):
    """3 families × 1 technique = 3 items — within MAX_MATRIX_ITEMS=9."""
    call_count = [0]

    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        call_count[0] += 1
        return {
            "success": True,
            "clipUrl": f"/runtime/clip_{call_count[0]}.mp4",
            "experimentId": f"exp_{call_count[0]}",
            "clipSeconds": clip_seconds,
            "elapsedMs": 10,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)

    request = SimpleNamespace(
        content="Test",
        params={"clipSeconds": 2, "keyPointCount": 2},
        matrix={
            "families": ["caption_story", "data_news", "timeline_news"],
            "visualTechniques": ["academic_sketch"],
        },
    )

    result = style_family_service.run_visual_technique_matrix(request)
    assert len(result["items"]) == 3
    assert call_count[0] == 3
    assert all(item["visualTechnique"] == "academic_sketch" for item in result["items"])


def test_visual_technique_matrix_invalid_technique_returns_400(monkeypatch):
    """Invalid visualTechnique values should raise ValueError."""
    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": "exp_1",
            "clipSeconds": 2,
            "elapsedMs": 10,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)

    request = SimpleNamespace(
        content="Test",
        params={"clipSeconds": 2, "keyPointCount": 2},
        matrix={
            "families": ["data_news"],
            "visualTechniques": ["not_a_real_technique"],
        },
    )

    try:
        style_family_service.run_visual_technique_matrix(request)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "visualTechniques filter resulted in empty set" in str(e)


def test_visual_technique_matrix_over_limit_returns_400(monkeypatch):
    """Request exceeding MAX_MATRIX_ITEMS=9 should raise ValueError.

    Temporarily expands both VALID lists to create a 5×2=10 scenario,
    then restores the original values.
    """
    original_families = style_family_service.VALID_VISUAL_TECHNIQUE_MATRIX_FAMILIES
    original_techniques = style_family_service.VALID_VISUAL_TECHNIQUES
    style_family_service.VALID_VISUAL_TECHNIQUE_MATRIX_FAMILIES = [
        "caption_story", "data_news", "timeline_news", "card_stack", "dashboard_brief"
    ]
    style_family_service.VALID_VISUAL_TECHNIQUES = ["academic_sketch", "data_viz_dashboard"]

    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": "exp_1",
            "clipSeconds": 2,
            "elapsedMs": 10,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)

    try:
        request = SimpleNamespace(
            content="Test",
            params={"clipSeconds": 2, "keyPointCount": 2},
            matrix={
                "families": ["caption_story", "data_news", "timeline_news", "card_stack", "dashboard_brief"],
                "visualTechniques": ["academic_sketch", "data_viz_dashboard"],
            },
        )
        style_family_service.run_visual_technique_matrix(request)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "visual technique matrix is limited to 9 clips" in str(e)
    finally:
        style_family_service.VALID_VISUAL_TECHNIQUE_MATRIX_FAMILIES = original_families
        style_family_service.VALID_VISUAL_TECHNIQUES = original_techniques


def test_visual_technique_matrix_endpoint_valid_1x1(monkeypatch):
    """Endpoint returns 200 for valid 1×1 request."""
    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": "exp_test",
            "clipSeconds": 2,
            "elapsedMs": 1,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)
    client = TestClient(app)

    resp = client.post(
        "/video-lab/style-family/visual-technique-matrix",
        json={
            "content": "test",
            "params": {"clipSeconds": 2, "keyPointCount": 2},
            "matrix": {
                "families": ["caption_story"],
                "visualTechniques": ["academic_sketch"],
            },
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["family"] == "caption_story"
    assert data["items"][0]["visualTechnique"] == "academic_sketch"


def test_visual_technique_matrix_endpoint_empty_families_returns_400(monkeypatch):
    """Empty families after filter should return 400."""
    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": "exp_1",
            "clipSeconds": 2,
            "elapsedMs": 10,
            "message": "",
            "warnings": [],
        }

    monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)
    client = TestClient(app)

    resp = client.post(
        "/video-lab/style-family/visual-technique-matrix",
        json={
            "content": "test",
            "params": {"clipSeconds": 2, "keyPointCount": 2},
            "matrix": {
                "families": ["not_a_family"],
                "visualTechniques": ["academic_sketch"],
            },
        },
    )

    assert resp.status_code == 400
    assert "families filter resulted in empty set" in resp.json()["detail"]
