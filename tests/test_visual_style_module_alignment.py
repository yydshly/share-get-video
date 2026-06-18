"""UI contract tests for the aligned visual-style catalog and matrix."""

import re
from pathlib import Path


ROOT = Path(__file__).parent.parent
PRESETS = ROOT / "frontend" / "src" / "video-lab" / "presets" / "visualStylePresets.ts"
LAB_PAGE = ROOT / "frontend" / "src" / "video-lab" / "pages" / "RemotionLabPage.tsx"
FAMILY_PAGE = ROOT / "frontend" / "src" / "video-lab" / "pages" / "RemotionStyleFamilyPage.tsx"


def test_visual_style_catalog_is_the_single_source_for_supported_presets():
    source = PRESETS.read_text(encoding="utf-8")
    supported_block = re.search(
        r"export const VISUAL_STYLE_PRESETS.*?= \[(.*?)\];",
        source,
        flags=re.DOTALL,
    )
    assert supported_block is not None
    ids = re.findall(r'\bid:\s*"([^"]+)"', supported_block.group(1))
    assert ids == ["light_editorial", "warm_paper", "bold_magazine"]
    assert "evaluationFocus" in supported_block.group(1)
    assert "colors:" in supported_block.group(1)


def test_visual_style_catalog_and_matrix_import_the_same_definitions():
    lab_source = LAB_PAGE.read_text(encoding="utf-8")
    family_source = FAMILY_PAGE.read_text(encoding="utf-8")

    assert 'from "../presets/visualStylePresets"' in lab_source
    assert "VISUAL_STYLE_PRESETS.map" in lab_source
    assert "VISUAL_STYLE_EXPLORATION_DIRECTIONS.map" in lab_source
    assert "已实现 · 可渲染" in lab_source
    assert "不进入当前矩阵" in lab_source

    assert 'from "../presets/visualStylePresets"' in family_source
    assert "SHARED_VISUAL_STYLE_PRESETS.map" in family_source
    assert "SHARED_VISUAL_STYLE_MATRIX_FAMILIES.map" in family_source


def test_visual_style_matrix_progressively_submits_one_cell_at_a_time():
    source = FAMILY_PAGE.read_text(encoding="utf-8")

    assert "for (const family of SHARED_VISUAL_STYLE_MATRIX_FAMILIES)" in source
    assert "for (const preset of SHARED_VISUAL_STYLE_PRESETS)" in source
    assert "families: [family.id]" in source
    assert "visualStylePresets: [preset.id]" in source
    assert "setVisualStyleMatrixResult({" in source
    assert "渲染中 ${totalItems}/" in source
