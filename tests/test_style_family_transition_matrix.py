from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
import app.video_lab.services.style_family_service as style_family_service


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
