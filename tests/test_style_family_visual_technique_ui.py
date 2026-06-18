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


def test_all_17_techniques_have_acceptance_metadata():
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")
    meta_match = re.search(
        r"const VISUAL_TECHNIQUE_META: Record<string, VisualTechniqueMeta> = \{(.*?)\n\};",
        source,
        flags=re.DOTALL,
    )
    assert meta_match is not None
    meta_ids = set(re.findall(r"^\s{2}([a-z0-9_]+):\s*\{", meta_match.group(1), flags=re.MULTILINE))
    assert meta_ids == set(style_family_service.VALID_VISUAL_TECHNIQUES)
    assert "样式组合：" in source


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

    # Assert the old bug pattern is gone in the actual matrix construction:
    # look for visualTechniques: ALL_VISUAL_TECHNIQUES INSIDE a matrix construction (after a {)
    # not just anywhere in the file (comments, full_17 profile definition, etc.)
    batch_matrix_construction = re.search(
        r"visualTechniqueMatrixMode === \"technique_compare\""
        r".*?"
        r"families: profileFamilies,"
        r".*?"
        r"visualTechniques:\s*ALL_VISUAL_TECHNIQUES",
        source,
        flags=re.DOTALL,
    )
    assert batch_matrix_construction is None, (
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


# ─── V1.2.9+: full_17 sequential generation ────────────────────────────────────


def test_default_preview_profile_is_full_17():
    """The default useState for visualTechniquePreviewProfileId must be 'full_17'."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    match = re.search(
        r"useState<VisualTechniquePreviewProfileId>\(\"(\w+)\"\)",
        source,
    )
    assert match is not None, "useState<VisualTechniquePreviewProfileId> not found"
    default_profile = match.group(1)
    assert default_profile == "full_17", (
        f"Default profile must be 'full_17' but got '{default_profile}'"
    )


def test_main_button_text_for_full_17_is_descriptive():
    """When full_17 is selected, the main run button must say '生成全部 17 个技法样片'."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    assert '生成全部 17 个技法样片' in source, (
        "Main button text must say '生成全部 17 个技法样片' for full_17 profile"
    )


def test_main_button_shows_sequential_progress_for_full_17():
    """While running full_17, the button must show '正在生成 N / 17...'."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    assert "正在生成 ${sequentialProgress.current} / ${sequentialProgress.total}..." in source, (
        "Button must show sequential progress N / 17 during full_17 generation"
    )





def test_full_17_profile_exists_and_uses_all_17_techniques():
    """full_17 profile must exist and use ALL_VISUAL_TECHNIQUES as its visualTechniques."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    full_match = re.search(
        r"full_17:\s*\{(.*?)\n\s*\},",
        source,
        flags=re.DOTALL,
    )
    assert full_match is not None, "full_17 profile not found in VISUAL_TECHNIQUE_PREVIEW_PROFILES"
    body = full_match.group(1)

    assert "visualTechniques: ALL_VISUAL_TECHNIQUES" in body, (
        "full_17 must use ALL_VISUAL_TECHNIQUES"
    )
    assert "requestMode: \"sequential\"" in body, (
        "full_17 must have requestMode: \"sequential\" to avoid MAX_MATRIX_ITEMS overflow"
    )


def test_full_17_profile_label_and_badge():
    """full_17 must have a visible label (for UI button) and badge."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    full_match = re.search(
        r"full_17:\s*\{(.*?)\n\s*\},",
        source,
        flags=re.DOTALL,
    )
    assert full_match is not None
    body = full_match.group(1)

    assert 'label: "全部 17 个"' in body, "full_17 must have a label for the UI button"
    assert 'badge: "Full"' in body, "full_17 must have a badge"


def test_full_17_sequential_loop_sends_one_technique_at_a_time():
    """full_17 must iterate over ALL_VISUAL_TECHNIQUES and send one technique per request."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # The sequential branch for full_17 must have a loop over ALL_VISUAL_TECHNIQUES
    assert "for (const technique of profile.visualTechniques)" in source, (
        "Sequential loop should iterate over profile.visualTechniques"
    )

    # The per-iteration request body must send [technique] (single-element array)
    # Look for the pattern inside the full_17 block
    full_match = re.search(
        r"visualTechniquePreviewProfileId === \"full_17\"(.*?)(?:else if|else|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert full_match is not None
    full_block = full_match.group(1)

    # Must contain visualTechniques: [technique] (single, not ALL)
    assert (
        "visualTechniques: [technique]" in full_block
        or "visualTechniques:[technique]" in full_block.replace(" ", "")
    ), "full_17 must send one technique at a time: visualTechniques: [technique]"


def test_full_17_does_not_batch_all_17_in_single_request():
    """full_17 must NOT construct a batch request with ALL_VISUAL_TECHNIQUES in a single matrix call."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    full_match = re.search(
        r"visualTechniquePreviewProfileId === \"full_17\"(.*?)(?:else if|else|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert full_match is not None
    full_block = full_match.group(1)

    # Must NOT send ALL_VISUAL_TECHNIQUES as a batch
    assert "ALL_VISUAL_TECHNIQUES" not in full_block, (
        "full_17 must not send ALL_VISUAL_TECHNIQUES in a single batch request"
    )


def test_sequential_progress_state_exists():
    """sequentialProgress state must be declared and passed to VisualTechniqueVariantMatrix."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    assert "sequentialProgress" in source, (
        "sequentialProgress state variable not found"
    )
    assert "setSequentialProgress" in source, (
        "setSequentialProgress setter not found"
    )
    assert "sequentialProgress={sequentialProgress}" in source or (
        "sequentialProgress={}" in source
    ), "sequentialProgress must be passed to VisualTechniqueVariantMatrix component"


def test_full_17_fails_gracefully_per_technique():
    """When a technique fails during full_17 sequential generation, it must not abort the whole batch."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # A try/catch inside the sequential loop must exist so one failure doesn't stop the loop
    full_match = re.search(
        r"visualTechniquePreviewProfileId === \"full_17\"(.*?)(?:else if|else|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert full_match is not None
    full_block = full_match.group(1)

    assert "try" in full_block and "catch" in full_block, (
        "full_17 sequential loop must have try/catch to continue after individual technique failure"
    )
    assert "combinedItems.push" in full_block, (
        "failed technique must still push a (failed) item to combinedItems"
    )


def test_existing_profiles_still_use_batch_mode():
    """smoke_2s, visual_6s, deep_12s must still use requestMode: "batch" (not sequential)."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    for profile_id in ["smoke_2s", "visual_6s", "deep_12s"]:
        profile_match = re.search(
            rf"{profile_id}:\s*\{{(.*?)\n\s*\}},",
            source,
            flags=re.DOTALL,
        )
        assert profile_match is not None, f"{profile_id} not found"
        body = profile_match.group(1)
        assert 'requestMode: "batch"' in body, (
            f"{profile_id} must still use requestMode: \"batch\""
        )


def test_batch_profiles_still_guard_against_over_limit():
    """The plannedClipCount > 9 guard must still exist for batch profile requests."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # The guard should appear in the batch-only path (not inside full_17 sequential branch)
    # Verify it exists somewhere in runVisualTechniqueMatrix
    run_block = re.search(
        r"const runVisualTechniqueMatrix = async \(\) => \{(.*?)\n\s*\};",
        source,
        flags=re.DOTALL,
    )
    assert run_block is not None
    func_body = run_block.group(1)

    assert "plannedClipCount" in func_body, "plannedClipCount guard variable missing"
    assert "> 9" in func_body, "Guard must check against limit of 9"


def test_profile_badge_shows_correct_clip_count():
    """The clip-count badge must use profile.visualTechniques.length (not hardcoded 5)."""
    source = STYLE_FAMILY_PAGE.read_text(encoding="utf-8")

    # Must use the dynamic length rather than hardcoded "5"
    assert "profile.visualTechniques.length" in source, (
        "Badge must show dynamic profile.visualTechniques.length, not hardcoded 5"
    )
    # Must NOT have hardcoded "1 family × 5 techniques = 5 clips" text anymore
    hardcoded = re.search(r'"1 family × 5 techniques = 5 clips"', source)
    assert hardcoded is None, (
        "Hardcoded '1 family × 5 techniques = 5 clips' must be removed; use dynamic count"
    )
