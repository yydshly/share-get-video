"""
tests/test_remotion_lab_effect_prototypes.py
V1.2.3: Tests for the 12 new prototype visualTechnique overlays.

Covers:
- All 17 visualTechniques (5 existing + 12 new) are accepted by props_builder
- All 17 visualTechniques are accepted by style_family_service VALID_VISUAL_TECHNIQUES
- Invalid visualTechnique is rejected by visual-technique-matrix endpoint
- All new technique overlays exist in AiNewsVideo.tsx source
- RemotionLabPage.tsx marks new techniques as implemented_minimal
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.video_lab.renderers.remotion.props_builder import build_remotion_props
import app.video_lab.services.style_family_service as style_family_service


# All 17 techniques (5 existing + 12 new)
ALL_VISUAL_TECHNIQUES = [
    # V1.2.4/1.2.5 existing
    "academic_sketch",
    "blueprint",
    "data_viz_dashboard",
    "agent_sandbox_25d",
    "kinetic_code_typography",
    # V1.2.3 new prototypes
    "whiteboard_explainer",
    "benchmark_ranking",
    "architecture_diagram",
    "product_demo_flow",
    "launch_countdown",
    "map_timeline",
    "audio_visualizer",
    "tiktok_caption_story",
    "magazine_headline",
    "capability_radar",
    "timeline_recap",
    "lottie_icon_story",
]

NEW_TECHNIQUES = [
    "whiteboard_explainer",
    "benchmark_ranking",
    "architecture_diagram",
    "product_demo_flow",
    "launch_countdown",
    "map_timeline",
    "audio_visualizer",
    "tiktok_caption_story",
    "magazine_headline",
    "capability_radar",
    "timeline_recap",
    "lottie_icon_story",
]


def _build_props(key_points, params):
    """Helper: build props with mocked experiment dir."""
    structured = {"lead": "测试", "subtitle": "AI"}
    with patch("app.video_lab.renderers.remotion.props_builder.get_experiment_dir") as mock_dir:
        mock_dir.return_value = MagicMock()
        mock_path = MagicMock()
        mock_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_path.open = MagicMock()
        with patch("builtins.open", mock_path.open):
            return build_remotion_props("test_exp", structured, key_points, params)


class TestVisualTechniqueWhitelistInPropsBuilder:
    """All 17 visualTechniques must be passed through to props.style by props_builder."""

    def test_existing_techniques_passed(self):
        """Existing 5 visualTechniques are passed through to props.style."""
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        for technique in ["academic_sketch", "blueprint", "data_viz_dashboard", "agent_sandbox_25d", "kinetic_code_typography"]:
            props = _build_props(key_points, {"visualTechnique": technique})
            assert props["style"].get("visualTechnique") == technique, f"{technique} not passed"

    def test_new_techniques_passed(self):
        """All 12 new visualTechniques are passed through to props.style."""
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        for technique in NEW_TECHNIQUES:
            props = _build_props(key_points, {"visualTechnique": technique})
            assert props["style"].get("visualTechnique") == technique, f"{technique} not passed"

    def test_invalid_technique_not_passed(self):
        """Invalid visualTechnique values are silently ignored."""
        key_points = {"keyPoints": [{"title": "T", "body": "B", "source": "S"}]}
        props = _build_props(key_points, {"visualTechnique": "not_a_real_technique"})
        assert "visualTechnique" not in props.get("style", {})


class TestVisualTechniqueServiceWhitelist:
    """VALID_VISUAL_TECHNIQUES in style_family_service must include all 17 techniques."""

    def test_all_17_techniques_in_service_whitelist(self):
        """All 17 visualTechniques (5 existing + 12 new) are in VALID_VISUAL_TECHNIQUES."""
        for technique in ALL_VISUAL_TECHNIQUES:
            assert technique in style_family_service.VALID_VISUAL_TECHNIQUES, f"{technique} missing from VALID_VISUAL_TECHNIQUES"

    def test_valid_count(self):
        """VALID_VISUAL_TECHNIQUES has exactly 17 entries."""
        assert len(style_family_service.VALID_VISUAL_TECHNIQUES) == 17


class TestVisualTechniqueMatrixEndpoint:
    """Visual technique matrix endpoint accepts all 17 techniques."""

    def test_all_new_techniques_accepted_by_endpoint(self, monkeypatch):
        """Each new visualTechnique is accepted by the matrix endpoint and returns 200."""
        def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
            return {
                "success": True,
                "clipUrl": "/runtime/clip.mp4",
                "experimentId": "exp_test",
                "clipSeconds": clip_seconds,
                "elapsedMs": 10,
                "message": "",
                "warnings": [],
            }

        monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)
        client = TestClient(app)

        for technique in NEW_TECHNIQUES:
            resp = client.post(
                "/video-lab/style-family/visual-technique-matrix",
                json={
                    "content": "test",
                    "params": {"clipSeconds": 2, "keyPointCount": 2},
                    "matrix": {
                        "families": ["data_news"],
                        "visualTechniques": [technique],
                    },
                },
            )
            assert resp.status_code == 200, f"{technique} returned {resp.status_code}: {resp.json()}"

    def test_invalid_technique_returns_400(self, monkeypatch):
        """Invalid visualTechnique filter returns 400 with error detail."""
        def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
            return {
                "success": True,
                "clipUrl": "/runtime/clip.mp4",
                "experimentId": "exp_test",
                "clipSeconds": clip_seconds,
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
                    "families": ["data_news"],
                    "visualTechniques": ["not_a_real_technique"],
                },
            },
        )
        assert resp.status_code == 400
        assert "visualTechniques filter resulted in empty set" in resp.json()["detail"]

    def test_matrix_over_limit_returns_400(self, monkeypatch):
        """Matrix with more than 9 clips returns 400."""
        def fake_render_clip_preview(*, content, visual_route, params, clip_seconds):
            return {
                "success": True,
                "clipUrl": "/runtime/clip.mp4",
                "experimentId": "exp_test",
                "clipSeconds": clip_seconds,
                "elapsedMs": 10,
                "message": "",
                "warnings": [],
            }

        monkeypatch.setattr(style_family_service, "render_clip_preview", fake_render_clip_preview)
        client = TestClient(app)

        # 3 families × 5 techniques = 15 clips > 9
        resp = client.post(
            "/video-lab/style-family/visual-technique-matrix",
            json={
                "content": "test",
                "params": {"clipSeconds": 2, "keyPointCount": 2},
                "matrix": {
                    "families": ["data_news", "dashboard_brief", "caption_story"],
                    "visualTechniques": list(style_family_service.VALID_VISUAL_TECHNIQUES),
                },
            },
        )
        assert resp.status_code == 400
        assert "over the maximum" in resp.json()["detail"] or "limit" in resp.json()["detail"]


class TestVisualTechniqueOverlayInSource:
    """Each new visualTechnique has a dedicated rendering branch in AiNewsVideo.tsx."""

    def test_all_new_technique_branches_exist(self):
        """Each of the 12 new techniques has an if-branch in BackgroundLayer."""
        import re
        source_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "remotion",
            "src",
            "AiNewsVideo.tsx",
        )
        source = open(source_path, encoding="utf-8").read()

        for technique in NEW_TECHNIQUES:
            # Check for `if (visualTechnique === "technique_name")`
            pattern = rf'if\s*\(\s*visualTechnique\s*===\s*["\']' + re.escape(technique) + rf'["\']'
            assert re.search(pattern, source), f"No BackgroundLayer branch found for visualTechnique={technique}"

    def test_all_new_technique_chip_colors_exist(self):
        """Each of the 12 new techniques has a chip color entry in VisualTechniqueContentProbeLayer."""
        import re
        source_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "remotion",
            "src",
            "AiNewsVideo.tsx",
        )
        source = open(source_path, encoding="utf-8").read()

        for technique in NEW_TECHNIQUES:
            # Check for technique key in the chip colors object
            pattern = rf'{re.escape(technique)}\s*:\s*\{{[^}}]*\}}'
            assert re.search(pattern, source), f"No chip color entry found for visualTechnique={technique}"


class TestRemotionLabPagePrototypes:
    """RemotionLabPage.tsx marks all 12 new techniques as implemented_minimal."""

    def test_all_new_techniques_are_implemented_minimal(self):
        """All 12 new techniques appear in IMPLEMENTED_PROTOTYPES with implementationLevel=implemented_minimal."""
        import re

        lab_page_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "frontend",
            "src",
            "video-lab",
            "pages",
            "RemotionLabPage.tsx",
        )
        source = open(lab_page_path, encoding="utf-8").read()

        # IMPLEMENTED_PROTOTYPES must exist
        assert "IMPLEMENTED_PROTOTYPES" in source, "IMPLEMENTED_PROTOTYPES not found in RemotionLabPage.tsx"

        for technique in NEW_TECHNIQUES:
            # Must have id entry
            id_pattern = rf'id:\s*["\']' + re.escape(technique) + rf'["\']'
            assert re.search(id_pattern, source), f"id:{technique} not found in IMPLEMENTED_PROTOTYPES"

            # Must have implementationLevel: "implemented_minimal"
            impl_pattern = 'id:\\s*["\']' + re.escape(technique) + '["\'][^}]*implementationLevel:\\s*["\']implemented_minimal["\']'
            assert re.search(impl_pattern, source, re.DOTALL), f"{technique} not marked as implemented_minimal in IMPLEMENTED_PROTOTYPES"

    def test_no_new_techniques_remain_in_future_directions(self):
        """New techniques no longer appear in FUTURE_EFFECT_DIRECTIONS."""
        import re

        lab_page_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "frontend",
            "src",
            "video-lab",
            "pages",
            "RemotionLabPage.tsx",
        )
        source = open(lab_page_path, encoding="utf-8").read()

        # If FUTURE_EFFECT_DIRECTIONS is not empty, none of the new techniques should be in it
        future_match = re.search(r'const FUTURE_EFFECT_DIRECTIONS[^=]*=\s*\[(.*?)\];', source, re.DOTALL)
        if future_match:
            future_body = future_match.group(1)
            for technique in NEW_TECHNIQUES:
                assert technique not in future_body, f"{technique} still in FUTURE_EFFECT_DIRECTIONS"
