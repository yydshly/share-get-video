"""
tests/test_style_family_visual_style_matrix.py
V1.2.4: Tests for visual style preset matrix endpoint and service.
"""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
import app.video_lab.services.style_family_service as style_family_service


def test_visual_style_matrix_passes_preset_params(monkeypatch):
    """run_visual_style_matrix should pass visualStylePreset to render_clip_preview."""
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
            "clipUrl": f"/runtime/{params['remotionFamily']}_{params['visualStylePreset']}.mp4",
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
            "families": ["data_news", "dashboard_brief"],
            "visualStylePresets": ["light_editorial", "warm_paper"],
        },
    )

    result = style_family_service.run_visual_style_matrix(request)

    # 2 families × 2 presets = 4 items
    assert len(result["items"]) == 4
    # All items should have visualStylePreset in params
    assert all(
        call["params"]["visualStylePreset"] in ("light_editorial", "warm_paper")
        for call in captured
    )
    assert all(
        call["params"]["remotionFamily"] in ("data_news", "dashboard_brief")
        for call in captured
    )
    # V1.2.3: Lab debug label should be injected by the matrix service
    assert all(
        call["params"].get("remotionStyle", {}).get("showVisualStyleDebugLabel") is True
        for call in captured
    )


def test_visual_style_matrix_3x3_at_limit(monkeypatch):
    """3 families × 3 presets = 9 items — exactly at the MAX_MATRIX_ITEMS limit."""
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
            "families": ["data_news", "dashboard_brief", "caption_story"],
            "visualStylePresets": ["light_editorial", "warm_paper", "bold_magazine"],
        },
    )

    result = style_family_service.run_visual_style_matrix(request)
    assert len(result["items"]) == 9
    assert call_count[0] == 9


def test_visual_style_matrix_bold_magazine_is_valid_preset(monkeypatch):
    """bold_magazine is a valid visualStylePreset and should be accepted."""
    captured = []

    def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
        captured.append(params)
        return {
            "success": True,
            "clipUrl": "/runtime/clip.mp4",
            "experimentId": f"exp_{len(captured)}",
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
            "families": ["data_news"],
            "visualStylePresets": ["bold_magazine"],
        },
    )

    result = style_family_service.run_visual_style_matrix(request)
    assert len(result["items"]) == 1
    assert result["items"][0]["visualStylePreset"] == "bold_magazine"
    assert captured[0]["visualStylePreset"] == "bold_magazine"


def test_visual_style_matrix_invalid_preset_returns_error(monkeypatch):
    """Invalid visualStylePreset values should raise ValueError."""
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
            "visualStylePresets": ["not_a_real_preset"],
        },
    )

    try:
        style_family_service.run_visual_style_matrix(request)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "visualStylePresets filter resulted in empty set" in str(e)
        assert "light_editorial" in str(e)  # error should list allowed values


def test_visual_style_matrix_endpoint_filters_supported_values(monkeypatch):
    """Endpoint should filter unknown families and presets, return 200 with valid subset."""
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
        "/video-lab/style-family/visual-style-matrix",
        json={
            "content": "test",
            "params": {"clipSeconds": 2, "keyPointCount": 2},
            "matrix": {
                "families": ["data_news", "unknown_family"],
                "visualStylePresets": ["light_editorial", "bad_preset"],
            },
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    # Only data_news (unknown_family filtered), only light_editorial (bad_preset filtered)
    assert len(data["items"]) == 1
    assert data["items"][0]["family"] == "data_news"
    assert data["items"][0]["visualStylePreset"] == "light_editorial"


def test_visual_style_matrix_endpoint_empty_families_returns_400(monkeypatch):
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
        "/video-lab/style-family/visual-style-matrix",
        json={
            "content": "test",
            "params": {"clipSeconds": 2, "keyPointCount": 2},
            "matrix": {
                "families": ["not_a_family"],
                "visualStylePresets": ["light_editorial"],
            },
        },
    )

    assert resp.status_code == 400
    assert "families filter resulted in empty set" in resp.json()["detail"]
