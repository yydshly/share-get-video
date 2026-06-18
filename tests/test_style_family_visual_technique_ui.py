"""UI contract tests for the five implemented Remotion visual techniques."""

import re
from pathlib import Path

import app.video_lab.services.style_family_service as style_family_service


PROJECT_ROOT = Path(__file__).parent.parent
STYLE_FAMILY_PAGE = (
    PROJECT_ROOT
    / "frontend"
    / "src"
    / "video-lab"
    / "pages"
    / "RemotionStyleFamilyPage.tsx"
)
LAB_PAGE = (
    PROJECT_ROOT
    / "frontend"
    / "src"
    / "video-lab"
    / "pages"
    / "RemotionLabPage.tsx"
)


def _ids_from_block(source: str, const_name: str) -> list[str]:
    match = re.search(
        rf"const {const_name} = \[(.*?)\];",
        source,
        flags=re.DOTALL,
    )
    assert match is not None
    return re.findall(r'\bid:\s*"([^"]+)"', match.group(1))


def test_effect_gallery_and_matrix_show_the_same_five_supported_techniques():
    lab_source = LAB_PAGE.read_text(encoding="utf-8")
    style_source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # All implemented prototypes (EFFECT_PROTOTYPES + IMPLEMENTED_PROTOTYPES)
    gallery_ids = set(_ids_from_block(lab_source, "EFFECT_PROTOTYPES"))
    impl_ids = set(_ids_from_block(lab_source, "IMPLEMENTED_PROTOTYPES"))
    all_gallery_ids = gallery_ids | impl_ids
    matrix_match = re.search(
        r"const ALL_VISUAL_TECHNIQUES: VisualTechniqueId\[\] = \[(.*?)\];",
        style_source,
        flags=re.DOTALL,
    )
    assert matrix_match is not None
    matrix_ids = set(re.findall(r'"([^"]+)"', matrix_match.group(1)))
    expected = set(style_family_service.VALID_VISUAL_TECHNIQUES)

    assert len(all_gallery_ids) == len(expected), f"Gallery IDs: {len(all_gallery_ids)}, expected: {len(expected)}"
    assert len(matrix_ids) == len(expected), f"Matrix IDs: {len(matrix_ids)}, expected: {len(expected)}"
    assert all_gallery_ids == expected
    assert matrix_ids == expected


def test_effect_gallery_describes_current_implementation_truthfully():
    source = LAB_PAGE.read_text(encoding="utf-8")

    # V1.2.3: now 17 techniques (5 original + 12 prototype)
    assert "已接入的效果样机（17 种）" in source or "已接入的效果样机（" in source
    assert "当前 Remotion 视频生成参数体系" in source
    assert "visualTechnique 参数：" in source
    assert "4 prototypes from remotion.html" not in source
    assert "尚未接入真实 Remotion 渲染" not in source
    assert "Rough.js" not in source
    assert "D3/Recharts" not in source
    assert "CSS 3D / Canvas" not in source
    assert "AST span split" not in source


def test_technique_compare_does_not_hide_visuals_behind_content_probe():
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    assert (
        'visualTechniqueContentProbe: visualTechniqueMatrixMode === "family_adaptation"'
        in source
    )
    assert "Technique 横向比较优先展示五种真实技法本身" in source


def test_visual_acceptance_resets_and_stale_results_cannot_be_accepted():
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    assert "useEffect(() => {" in source
    assert "setLocalAcceptance({});" in source
    assert "}, [resultSignature]);" in source
    assert "disabled={isResultStale || !item.success}" in source


def test_real_preview_profiles_use_technique_specific_content():
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    expected_mappings = {
        "academic_sketch": "academic_explainer",
        "blueprint": "blueprint_architecture",
        "data_viz_dashboard": "data_dashboard",
        "agent_sandbox_25d": "agent_sandbox",
        "kinetic_code_typography": "code_typography",
    }
    for technique, fixture in expected_mappings.items():
        assert f'{technique}: "{fixture}"' in source

    assert 'visualTechniquePreviewProfileId !== "smoke_2s"' in source
    # V1.2.8+: sequential rendering now iterates over profile.visualTechniques, not ALL_VISUAL_TECHNIQUES
    assert "for (const technique of profile.visualTechniques)" in source
    assert "Render sequentially to avoid launching five Remotion jobs at once." in source
    assert "8s / 12s 不再让五种技法共用通用文案" in source


def test_smoke_uses_generic_content_and_deep_preview_is_really_12_seconds():
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    assert '? "generic_ai_eval"' in source
    deep_profile = re.search(
        r"deep_12s:\s*\{(.*?)\n\s*\},",
        source,
        flags=re.DOTALL,
    )
    assert deep_profile is not None
    assert 'label: "12s 深度预览"' in deep_profile.group(1)
    assert "clipSeconds: 12" in deep_profile.group(1)


def test_smoke_preview_profile_has_explicit_visual_techniques():
    """smoke_2s profile must declare its own visualTechniques list (not rely on ALL_VISUAL_TECHNIQUES)."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    smoke_match = re.search(
        r"smoke_2s:\s*\{(.*?)\n\s*\},",
        source,
        flags=re.DOTALL,
    )
    assert smoke_match is not None, "smoke_2s profile not found"
    smoke_body = smoke_match.group(1)

    # Profile must have a visualTechniques field
    assert "visualTechniques:" in smoke_body, "smoke_2s is missing visualTechniques field"
    # It must list exactly 5 technique IDs
    vt_match = re.search(r"visualTechniques:\s*\[(.*?)\]", smoke_body, flags=re.DOTALL)
    assert vt_match is not None
    techniques = re.findall(r'"([^"]+)"', vt_match.group(1))
    assert len(techniques) == 5, f"smoke_2s should have 5 techniques, got {len(techniques)}: {techniques}"


def test_all_preview_profiles_have_visual_techniques_and_stay_within_limit():
    """Every profile must declare visualTechniques, and 1 family × N techniques must be ≤ 9."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    for profile_id in ["smoke_2s", "visual_6s", "deep_12s"]:
        profile_match = re.search(
            rf"{profile_id}:\s*\{{(.*?)\n\s*\}},",
            source,
            flags=re.DOTALL,
        )
        assert profile_match is not None, f"{profile_id} profile not found"
        body = profile_match.group(1)

        assert "visualTechniques:" in body, f"{profile_id} is missing visualTechniques field"
        vt_match = re.search(r"visualTechniques:\s*\[(.*?)\]", body, flags=re.DOTALL)
        assert vt_match is not None, f"{profile_id} visualTechniques array not found"
        techniques = re.findall(r'"([^"]+)"', vt_match.group(1))

        # 1 family × N techniques ≤ 9
        clip_count = 1 * len(techniques)
        assert clip_count <= 9, (
            f"{profile_id}: {clip_count} clips (1 family × {len(techniques)} techniques) exceeds MAX_MATRIX_ITEMS=9"
        )


def test_no_path_sends_all_17_visual_techniques_in_technique_compare_mode():
    """In technique_compare mode the request must not send ALL_VISUAL_TECHNIQUES (17) to the backend."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # The matrix construction block for technique_compare must not reference ALL_VISUAL_TECHNIQUES
    matrix_block = re.search(
        r"visualTechniqueMatrixMode === \"technique_compare\""
        r".*?"
        r"families: profileFamilies,"
        r".*?"
        r"visualTechniques:",
        source,
        flags=re.DOTALL,
    )
    assert matrix_block is not None, "technique_compare matrix construction not found"

    # After our fix: visualTechniques should come from profile.visualTechniques or spread of it,
    # NOT from ALL_VISUAL_TECHNIQUES
    # The block should contain "profile.visualTechniques" or spread "[...profileTechniques]"
    assert (
        "profile.visualTechniques" in matrix_block.group(0)
        or "[...profileTechniques]" in matrix_block.group(0)
    ), (
        "technique_compare matrix still uses ALL_VISUAL_TECHNIQUES instead of profile.visualTechniques"
    )

    # Assert the old bug pattern is gone: visualTechniques: ALL_VISUAL_TECHNIQUES must NOT appear
    # in the technique_compare branch
    technique_compare_all_match = re.search(
        r"technique_compare.*?visualTechniques:\s*ALL_VISUAL_TECHNIQUES",
        source,
        flags=re.DOTALL,
    )
    assert technique_compare_all_match is None, (
        "Bug still present: technique_compare branch sends ALL_VISUAL_TECHNIQUES (17) to backend"
    )


def test_frontend_guard_prevents_over_limit_requests():
    """Frontend must throw before sending a request that would exceed MAX_MATRIX_ITEMS=9."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # A guard checking plannedClipCount > 9 must exist in runVisualTechniqueMatrix
    assert "plannedClipCount" in source, "plannedClipCount variable not found in runVisualTechniqueMatrix"
    assert "MAX_MATRIX_ITEMS" in source or "> 9" in source, (
        "Frontend over-limit guard (> 9) not found"
    )

    # The guard must throw an error, not silently proceed
    guard_block = re.search(
        r"if\s*\(\s*plannedClipCount\s*>\s*9\s*\).*?throw\s*new\s*Error",
        source,
        flags=re.DOTALL,
    )
    assert guard_block is not None, "Frontend guard does not throw on plannedClipCount > 9"


def test_smoke_visual_techniques_match_generic_ai_eval_recommendations():
    """smoke_2s visualTechniques must match generic_ai_eval.recommendedTechniques (5 shared baseline techniques)."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # Extract generic_ai_eval recommendedTechniques
    fixture_match = re.search(
        r"generic_ai_eval:\s*\{(.*?)\n\s*\},",
        source,
        flags=re.DOTALL,
    )
    assert fixture_match is not None
    fixture_body = fixture_match.group(1)
    vt_match = re.search(r"recommendedTechniques:\s*\[(.*?)\]", fixture_body, flags=re.DOTALL)
    assert vt_match is not None
    recommended = set(re.findall(r'"([^"]+)"', vt_match.group(1)))

    # Extract smoke_2s visualTechniques
    smoke_match = re.search(
        r"smoke_2s:\s*\{(.*?)\n\s*\},",
        source,
        flags=re.DOTALL,
    )
    assert smoke_match is not None
    smoke_body = smoke_match.group(1)
    smoke_vt_match = re.search(r"visualTechniques:\s*\[(.*?)\]", smoke_body, flags=re.DOTALL)
    assert smoke_vt_match is not None
    smoke_techniques = set(re.findall(r'"([^"]+)"', smoke_vt_match.group(1)))

    assert smoke_techniques == recommended, (
        f"smoke_2s visualTechniques {smoke_techniques} != generic_ai_eval.recommendedTechniques {recommended}"
    )


def test_remotion_lab_effect_prototypes_still_comprehensive():
    """Effect prototype gallery must still list all 12 new prototype techniques added in V1.2.3."""
    lab_source = LAB_PAGE.read_text(encoding="utf-8")

    # The 12 V1.2.3 prototype techniques must be present in EFFECT_PROTOTYPES
    expected_prototypes = [
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
    for proto in expected_prototypes:
        assert proto in lab_source, f"Prototype {proto} missing from RemotionLabPage"
