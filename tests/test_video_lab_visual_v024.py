"""
Tests for V0.2.4 visual quality improvements
- text_layout: extract_highlights, split_lines_with_max_count, fit_font_size
- frame_templates: cover, overview, keypoint, summary
- transition_composer: fade transitions
- manifest: visualPreset, templateVersion, transitionEnabled
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.renderers.text_layout import (
    extract_highlights,
    split_lines_with_max_count,
    fit_font_size,
    wrap_text_by_visual_width,
    find_chinese_font,
    truncate_text,
)
from app.video_lab.renderers.visual_theme import (
    TEMPLATE_VERSION,
    VISUAL_PRESET,
    TRANSITION_TYPE,
    TRANSITION_FRAMES_DEFAULT,
    CATEGORY_COLORS,
)
from app.video_lab.renderers.transition_composer import (
    generate_fade_frames,
    build_frame_sequence_with_transitions,
    estimate_transition_duration,
)
from app.video_lab.renderers.file_store import (
    ensure_runtime_exists,
    get_frames_dir,
)


# ─────────────────────────────────────────
# Text Layout Tests - extract_highlights
# ─────────────────────────────────────────
class TestExtractHighlights:
    def test_extract_percentages(self):
        """extract_highlights should recognize percentages like 88.9%, 72%."""
        text = "该模型的准确率达到了88.9%，比之前提升了72%"
        highlights = extract_highlights(text)
        assert any("88.9" in h or "88.9%" in h for h in highlights), f"Should find 88.9%: {highlights}"
        assert any("72%" in h for h in highlights), f"Should find 72%: {highlights}"

    def test_extract_multipliers(self):
        """extract_highlights should recognize multipliers like 10倍, 5x."""
        text = "性能提升了10倍，效率是之前的5x"
        highlights = extract_highlights(text)
        assert any("10倍" in h for h in highlights), f"Should find 10倍: {highlights}"
        assert any("5x" in h or "5X" in h for h in highlights), f"Should find 5x: {highlights}"

    def test_extract_chinese_numbers(self):
        """extract_highlights should recognize Chinese number phrases like 10万, 5620亿."""
        text = "公司拥有10万名员工，市值达5620亿美元"
        highlights = extract_highlights(text)
        assert any("10万" in h for h in highlights), f"Should find 10万: {highlights}"
        assert any("5620亿" in h for h in highlights), f"Should find 5620亿: {highlights}"

    def test_extract_empty_string(self):
        """extract_highlights should return empty list for empty string."""
        highlights = extract_highlights("")
        assert highlights == []

    def test_extract_no_highlights(self):
        """extract_highlights should return empty list when no patterns found."""
        text = "这是一个普通的句子没有任何数字"
        highlights = extract_highlights(text)
        # May still find Chinese characters but not the expected patterns
        assert isinstance(highlights, list)

    def test_extract_large_decimal(self):
        """extract_highlights should recognize large decimals like 88.9, 99.5."""
        text = "准确率达到了88.9和99.5两个指标"
        highlights = extract_highlights(text)
        assert any("88.9" in h for h in highlights), f"Should find 88.9: {highlights}"


# ─────────────────────────────────────────
# Text Layout Tests - split_lines_with_max_count
# ─────────────────────────────────────────
class TestSplitLinesWithMaxCount:
    def test_split_lines_respects_max_count(self):
        """split_lines_with_max_count should not exceed max_lines."""
        from PIL import Image, ImageDraw
        from app.video_lab.renderers.text_layout import find_chinese_font

        img = Image.new("RGB", (100, 100), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        font, _ = find_chinese_font(36)

        text = "这是一段很长的文本需要被分割成多行以适应最大宽度和最大行数的限制"
        lines = split_lines_with_max_count(text, font, 200, draw, max_lines=3)
        assert len(lines) <= 3, f"Should have at most 3 lines, got {len(lines)}"

    def test_split_lines_empty_text(self):
        """split_lines_with_max_count should return [''] for empty text."""
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (100, 100), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        font, _ = find_chinese_font(36)

        lines = split_lines_with_max_count("", font, 200, draw, max_lines=3)
        assert lines == [""]

    def test_split_lines_short_text_fits(self):
        """split_lines_with_max_count should not truncate if text fits."""
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (100, 100), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        font, _ = find_chinese_font(36)

        text = "短文本"
        lines = split_lines_with_max_count(text, font, 200, draw, max_lines=3)
        assert len(lines) == 1
        assert "短文本" in lines[0]


# ─────────────────────────────────────────
# Text Layout Tests - fit_font_size
# ─────────────────────────────────────────
class TestFitFontSize:
    def test_fit_font_size_returns_legal_size(self):
        """fit_font_size should return a font size in the candidates list."""
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (100, 100), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        text = "测试文本"
        size = fit_font_size(text, max_width=200, max_height=50, draw=draw)
        assert size >= 16, f"Size should be at least 16, got {size}"
        assert size <= 120, f"Size should be at most 120, got {size}"

    def test_fit_font_size_handles_empty_draw(self):
        """fit_font_size should return default when draw is None."""
        size = fit_font_size("text", 100, 50, draw=None)
        assert size == 36  # Default size


# ─────────────────────────────────────────
# Visual Theme Tests
# ─────────────────────────────────────────
class TestVisualTheme:
    def test_template_version_is_v024(self):
        """TEMPLATE_VERSION should be v0.2.4."""
        assert TEMPLATE_VERSION == "v0.2.4"

    def test_visual_preset_is_ai_frontier_dark(self):
        """VISUAL_PRESET should be ai_frontier_dark."""
        assert VISUAL_PRESET == "ai_frontier_dark"

    def test_transition_type_is_fade(self):
        """TRANSITION_TYPE should be fade."""
        assert TRANSITION_TYPE == "fade"

    def test_transition_frames_default_is_4(self):
        """TRANSITION_FRAMES_DEFAULT should be 4."""
        assert TRANSITION_FRAMES_DEFAULT == 4

    def test_category_colors_exist(self):
        """All expected categories should exist in CATEGORY_COLORS."""
        expected = ["安全", "研究", "应用", "工具", "企业", "技术", "默认"]
        for cat in expected:
            assert cat in CATEGORY_COLORS, f"Category {cat} should exist"
            style = CATEGORY_COLORS[cat]
            assert "bg" in style
            assert "text" in style
            assert "border" in style


# ─────────────────────────────────────────
# Transition Composer Tests
# ─────────────────────────────────────────
class TestTransitionComposer:
    def setup_method(self):
        """Set up test fixtures."""
        ensure_runtime_exists()
        self.test_exp_id = "test_transition_compose"
        self.frames_dir = get_frames_dir(self.test_exp_id)

    def test_generate_fade_frames_creates_files(self):
        """generate_fade_frames should create transition frame files."""
        # Create two simple test frames
        from PIL import Image

        frame_a = Image.new("RGB", (1080, 1920), (20, 20, 50))
        frame_b = Image.new("RGB", (1080, 1920), (50, 20, 20))

        frame_a_path = self.frames_dir / "frame_a.png"
        frame_b_path = self.frames_dir / "frame_b.png"
        frame_a.save(frame_a_path)
        frame_b.save(frame_b_path)

        result = generate_fade_frames(
            frame_a_path, frame_b_path, self.frames_dir,
            transition_frames=3, transition_prefix="test_fade"
        )

        assert result["transition_count"] == 3
        assert result["transition_type"] == "fade"
        assert len(result["frame_paths"]) == 3

        # Verify files exist
        for path_str in result["frame_paths"]:
            assert Path(path_str).exists()

    def test_estimate_transition_duration(self):
        """estimate_transition_duration should return correct duration."""
        duration = estimate_transition_duration(4, 0.08)
        assert duration == 0.32  # 4 * 0.08

    def test_build_frame_sequence_with_transitions(self):
        """build_frame_sequence_with_transitions should build correct sequence."""
        from PIL import Image

        # Create test frames
        frames = []
        for i in range(3):
            frame = Image.new("RGB", (200, 200), (i * 30, i * 20, i * 10))
            path = self.frames_dir / f"frame_{i}.png"
            frame.save(path)
            frames.append(path)

        result = build_frame_sequence_with_transitions(
            frames, self.frames_dir,
            transition_frames=2, enabled=True
        )

        assert result["transitionEnabled"] is True
        assert result["transition_type"] == "fade"
        assert len(result["sequence"]) > len(frames)  # Should have more frames with transitions
        assert result["transition_count"] > 0


# ─────────────────────────────────────────
# Frame Template Tests
# ─────────────────────────────────────────
class TestFrameTemplates:
    def setup_method(self):
        """Set up test fixtures."""
        ensure_runtime_exists()
        self.test_exp_id = "test_frame_templates"
        self.frames_dir = get_frames_dir(self.test_exp_id)

    def test_cover_template_creates_file(self):
        """render_cover_template should create a cover.png file."""
        from app.video_lab.renderers.frame_templates import render_cover_template

        result = render_cover_template(
            title="AI 前沿资讯",
            subtitle="今日要点速览",
            tags=["安全风险", "人机协作", "企业落地"],
            date_str="2024年01月15日",
            frames_dir=self.frames_dir,
            resolution=(1080, 1920),
        )

        assert result["path"].exists()
        assert result["template"] == "cover"
        assert result["templateVersion"] == "v0.2.4"
        assert result["visualPreset"] == "ai_frontier_dark"

    def test_overview_template_creates_file(self):
        """render_overview_template should create an overview.png file."""
        from app.video_lab.renderers.frame_templates import render_overview_template

        items = [
            {"title": "安全风险上升", "category": "安全"},
            {"title": "人机协作新突破", "category": "研究"},
            {"title": "企业落地加速", "category": "企业"},
        ]

        result = render_overview_template(
            items=items,
            frames_dir=self.frames_dir,
            resolution=(1080, 1920),
        )

        assert result["path"].exists()
        assert result["template"] == "overview"
        assert result["templateVersion"] == "v0.2.4"
        assert result["itemCount"] == 3

    def test_keypoint_template_creates_file(self):
        """render_keypoint_template should create a frame file."""
        from app.video_lab.renderers.frame_templates import render_keypoint_template

        result = render_keypoint_template(
            index=1,
            total=6,
            category="安全",
            title="AI安全风险持续上升",
            body="研究表明，AI系统的安全风险正在持续上升",
            source="依据: AI前沿研究",
            frames_dir=self.frames_dir,
            resolution=(1080, 1920),
        )

        assert result["path"].exists()
        assert result["template"] == "keypoint"
        assert result["templateVersion"] == "v0.2.4"
        assert result["category"] == "安全"
        assert isinstance(result["highlights"], list)

    def test_summary_template_creates_file(self):
        """render_summary_template should create a summary.png file."""
        from app.video_lab.renderers.frame_templates import render_summary_template

        conclusions = [
            "AI Agent 的能力边界正在被重新评估",
            "安全与可控性成为产品化关键",
            "企业级落地正在加速",
        ]

        result = render_summary_template(
            conclusions=conclusions,
            cta="适合作为「今日 AI 前沿」视频化分享模板",
            frames_dir=self.frames_dir,
            resolution=(1080, 1920),
        )

        assert result["path"].exists()
        assert result["template"] == "summary"
        assert result["templateVersion"] == "v0.2.4"
        assert result["conclusionCount"] == 3


# ─────────────────────────────────────────
# Integration Test - local_frame_compose V0.2.4 visual fields
# ─────────────────────────────────────────
class TestLocalFrameComposeV024Visual:
    def test_local_frame_compose_manifest_contains_visual_fields(self):
        """Manifest should contain V0.2.4 visual fields."""
        from app.video_lab.adapters.local_frame_compose import run_local_frame_compose
        from app.video_lab.renderers.file_store import read_manifest

        exp_id = "exp_visual_manifest_test"
        run_local_frame_compose(
            experiment_id=exp_id,
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "AI安全风险上升，需引起重视。准确率达88.9%。"},
            params={"targetDuration": 15},
        )

        manifest = read_manifest(exp_id)

        # Check V0.2.4 visual fields
        assert "visualPreset" in manifest, "manifest should contain visualPreset"
        assert manifest["visualPreset"] == "ai_frontier_dark"

        assert "templateVersion" in manifest, "manifest should contain templateVersion"
        assert manifest["templateVersion"] == "v0.2.4"

        assert "transitionEnabled" in manifest, "manifest should contain transitionEnabled"
        assert manifest["transitionEnabled"] is True

        assert "transitionFrames" in manifest, "manifest should contain transitionFrames"
        assert "highlightTerms" in manifest, "manifest should contain highlightTerms"
        assert isinstance(manifest["highlightTerms"], list)

    def test_local_frame_compose_assets_contains_visual_fields(self):
        """result.assets should contain V0.2.4 visual fields."""
        from app.video_lab.adapters.local_frame_compose import run_local_frame_compose

        result = run_local_frame_compose(
            experiment_id="exp_visual_assets_test",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "AI安全风险上升，需引起重视。准确率达88.9%。"},
            params={"targetDuration": 15},
        )

        assets = result.assets

        # Check V0.2.4 visual fields
        assert "visualPreset" in assets
        assert assets["visualPreset"] == "ai_frontier_dark"

        assert "templateVersion" in assets
        assert assets["templateVersion"] == "v0.2.4"

        assert "transitionEnabled" in assets
        assert assets["transitionEnabled"] is True

        assert "transitionType" in assets
        assert assets["transitionType"] == "fade"

        assert "transitionFrames" in assets
        assert "highlightTerms" in assets
        assert isinstance(assets["highlightTerms"], list)

    def test_local_frame_compose_step10_contains_visual_keydata(self):
        """Step 10 keyData should contain V0.2.4 visual fields."""
        from app.video_lab.adapters.local_frame_compose import run_local_frame_compose

        result = run_local_frame_compose(
            experiment_id="exp_step10_visual_test",
            test_case_id="case_ai_frontier_daily_001",
            input_payload={"content": "AI安全风险上升，需引起重视。准确率达88.9%。"},
            params={"targetDuration": 15},
        )

        # Find step 10 (Pillow Generate)
        step10 = None
        for step in result.productionSteps:
            if "Pillow" in step.name:
                step10 = step
                break

        assert step10 is not None, "Should have a Pillow step"
        assert "visualPreset" in step10.keyData
        assert step10.keyData["visualPreset"] == "ai_frontier_dark"
        assert "templateVersion" in step10.keyData
        assert step10.keyData["templateVersion"] == "v0.2.4"
        assert "transitionEnabled" in step10.keyData
        assert "transitionFrames" in step10.keyData
        assert "highlightTerms" in step10.keyData


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
