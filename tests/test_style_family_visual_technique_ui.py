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

    gallery_ids = _ids_from_block(lab_source, "EFFECT_PROTOTYPES")
    matrix_match = re.search(
        r"const ALL_VISUAL_TECHNIQUES: VisualTechniqueId\[\] = \[(.*?)\];",
        style_source,
        flags=re.DOTALL,
    )
    assert matrix_match is not None
    matrix_ids = re.findall(r'"([^"]+)"', matrix_match.group(1))
    expected = set(style_family_service.VALID_VISUAL_TECHNIQUES)

    assert len(gallery_ids) == 5
    assert len(matrix_ids) == 5
    assert set(gallery_ids) == expected
    assert set(matrix_ids) == expected


def test_effect_gallery_describes_current_implementation_truthfully():
    source = LAB_PAGE.read_text(encoding="utf-8")

    assert "已接入的效果样机（5 种）" in source
    assert "当前 Remotion 视频生成参数体系" in source
    assert "前往生成 5 种技法对比样片" in source
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
    assert "for (const technique of ALL_VISUAL_TECHNIQUES)" in source
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
