"""
Tests for V0.3.3 Subtitle Planner (SRT generation)
- Generates SRT files from voiceover segments
- No external dependencies
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.planners.subtitle_planner import generate_srt_from_segments, _format_srt_time, _split_subtitle_text


def test_format_srt_time():
    """SRT time format should be HH:MM:SS,mmm."""
    assert _format_srt_time(0.0) == "00:00:00,000"
    assert _format_srt_time(1.5) == "00:00:01,500"
    assert _format_srt_time(65.3) == "00:01:05,300"
    assert _format_srt_time(3661.123) == "01:01:01,123"


def test_split_subtitle_text():
    """Subtitle text should be split into reasonable-length lines."""
    text = "今天有三个AI信号值得关注，分别是GPT-5发布、Claude 4发布和Gemini Ultra更新。"
    lines = _split_subtitle_text(text, max_chars=15)
    assert len(lines) > 1
    for line in lines:
        assert len(line) <= 15


def test_srt_generation_from_segments():
    """SRT generation should produce valid SRT content."""
    segments = [
        {"text": "今天为大家带来AI前沿资讯。", "startSec": 0.0, "durationSec": 3.5},
        {"text": "第一条：GPT-5 发布，性能大幅提升。", "startSec": 3.5, "durationSec": 5.0},
    ]

    result = generate_srt_from_segments(segments)

    assert result["format"] == "srt"
    assert len(result["subtitles"]) == 2
    assert result["subtitles"][0]["text"] == "今天为大家带来AI前沿资讯。"
    assert result["subtitles"][0]["startSec"] == 0.0
    assert result["subtitles"][0]["endSec"] == 3.5


def test_srt_file_written():
    """SRT file should be written to output_path."""
    segments = [
        {"text": "测试字幕", "startSec": 0.0, "durationSec": 2.0},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        srt_path = Path(tmpdir) / "test.srt"
        result = generate_srt_from_segments(segments, output_path=srt_path)

        assert srt_path.exists(), "SRT file should be created"
        content = srt_path.read_text(encoding="utf-8")
        assert "测试字幕" in content
        assert "00:00:00,000 --> 00:00:02,000" in content
        assert result["srtPath"] != ""
        assert result["srtUrl"] != ""


def test_srt_content_format():
    """SRT content should follow standard format: index, time, text, blank line."""
    segments = [
        {"text": "第一行字幕", "startSec": 0.0, "durationSec": 2.0},
        {"text": "第二行字幕", "startSec": 2.0, "durationSec": 3.0},
    ]

    from app.video_lab.planners.subtitle_planner import _build_srt_content
    subtitles = [{"startSec": 0.0, "endSec": 2.0, "text": "第一行字幕"},
                {"startSec": 2.0, "endSec": 5.0, "text": "第二行字幕"}]
    content = _build_srt_content(subtitles)

    lines = content.split("\n")
    assert "1" in lines
    assert "2" in lines
    assert "第一行字幕" in content
    assert "第二行字幕" in content


def test_empty_segments_handled():
    """Empty segment list should produce empty SRT."""
    result = generate_srt_from_segments([])
    assert result["subtitles"] == []
    assert result["format"] == "srt"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])


# ─── V1.2.3: No text loss / no truncation tests ─────────────────────────────────

import re


def normalize_text(text: str) -> str:
    """Remove whitespace for comparison."""
    return re.sub(r"\s+", "", text)


def make_seg(text: str, start: float = 0.0, dur: float = 5.0) -> dict:
    return {"text": text, "startSec": start, "durationSec": dur}


def get_all_subtitle_text(entries: list[dict]) -> str:
    """Reconstruct full text from subtitle entries (uses subLines or text)."""
    parts = []
    for e in entries:
        lines = e.get("subLines", [e.get("text", "")])
        parts.append("".join(lines))
    return "".join(parts)


class TestShortSentenceNoLoss:
    """Test 1: Short sentences produce single entries with no text loss."""

    def test_single_entry_short_text(self):
        """A short sentence produces exactly 1 subtitle entry."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        seg = make_seg("这是一个短字幕。", start=0.0, dur=3.0)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)

        assert len(entries) == 1
        assert normalize_text(entries[0]["text"]) == normalize_text("这是一个短字幕。")

    def test_short_text_not_truncated(self):
        """Short text must not be truncated."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        text = "今天天气真好。"
        seg = make_seg(text)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)

        reconstructed = get_all_subtitle_text(entries)
        assert normalize_text(reconstructed) == normalize_text(text)


class TestLongSentenceSplits:
    """Test 2: Long sentences exceeding max_lines split into MULTIPLE entries (no truncation)."""

    def test_long_text_splits_not_truncates(self):
        """A long sentence must create multiple entries, not truncate to 2 lines."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        # ~80 chars with max_chars=20 → wraps to 4 lines → exceeds max_lines=2
        text = "人工智能技术正在快速改变我们的生活方式，从智能家居到自动驾驶，从医疗诊断到金融分析，各个领域都在经历深刻的变革和创新。"
        seg = make_seg(text, start=0.0, dur=10.0)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)

        # Must create more than 1 entry (can't fit in one 2-line entry)
        assert len(entries) >= 2, f"Expected multiple entries, got {len(entries)}"

    def test_long_text_no_character_loss(self):
        """Split text must not lose any characters."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        text = "人工智能技术正在快速改变我们的生活方式，从智能家居到自动驾驶，从医疗诊断到金融分析，各个领域都在经历深刻的变革和创新。"
        seg = make_seg(text, start=0.0, dur=10.0)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)

        reconstructed = get_all_subtitle_text(entries)
        assert normalize_text(reconstructed) == normalize_text(text)

    def test_each_entry_at_most_max_lines(self):
        """Each subtitle entry must have at most max_lines lines — no truncation."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        text = "人工智能技术正在快速改变我们的生活方式，从智能家居到自动驾驶，从医疗诊断到金融分析，各个领域都在经历深刻的变革和创新。"
        seg = make_seg(text, start=0.0, dur=10.0)
        max_lines = 2
        entries = _segment_to_entries(seg, max_chars=20, max_lines=max_lines)

        for i, entry in enumerate(entries):
            assert len(entry["subLines"]) <= max_lines, \
                f"Entry {i} has {len(entry['subLines'])} lines (> {max_lines})"


class TestPunctuationPreserved:
    """Test 3: Chinese punctuation splits correctly with no character loss."""

    def test_punctuation_not_lost(self):
        """Text split by punctuation must preserve all characters and punctuation marks."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        text = "第一句很短。第二句稍微长一些，需要拆开显示；第三句继续补充说明。"
        seg = make_seg(text, start=0.0, dur=8.0)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)

        reconstructed = get_all_subtitle_text(entries)
        assert normalize_text(reconstructed) == normalize_text(text)
        assert "。" in reconstructed
        assert "，" in reconstructed
        assert "；" in reconstructed


class TestSrtAssNoTextLoss:
    """Test 4: Both SRT and ASS preserve all text without loss."""

    def test_srt_no_text_loss(self):
        """generate_srt_from_segments must preserve all text."""
        segments = [
            make_seg("短句。", start=0.0, dur=2.0),
            make_seg("这是一个非常长的句子，用来测试字幕拆分功能是否正常工作，确保没有任何字符被截断或遗漏。", start=2.0, dur=8.0),
            make_seg("最后一句。", start=10.0, dur=2.0),
        ]
        result = generate_srt_from_segments(segments)

        all_text = get_all_subtitle_text(result["subtitles"])
        original = "".join(s["text"] for s in segments)
        assert normalize_text(all_text) == normalize_text(original)

    def test_ass_no_text_loss(self):
        """generate_ass_from_segments must preserve all text."""
        from app.video_lab.planners.subtitle_planner import generate_ass_from_segments
        segments = [
            make_seg("短句。", start=0.0, dur=2.0),
            make_seg("这是一个非常长的句子，用来测试字幕拆分功能是否正常工作，确保没有任何字符被截断或遗漏。", start=2.0, dur=8.0),
            make_seg("最后一句。", start=10.0, dur=2.0),
        ]
        result = generate_ass_from_segments(segments)

        all_text = get_all_subtitle_text(result["subtitles"])
        original = "".join(s["text"] for s in segments)
        assert normalize_text(all_text) == normalize_text(original)

    def test_ass_each_entry_max_lines(self):
        """ASS entries must each have at most max_lines lines."""
        from app.video_lab.planners.subtitle_planner import generate_ass_from_segments
        text = "人工智能技术正在快速改变我们的生活方式，从智能家居到自动驾驶，从医疗诊断到金融分析，各个领域都在经历深刻的变革和创新。"
        segments = [make_seg(text, start=0.0, dur=10.0)]
        result = generate_ass_from_segments(segments, max_chars=20, max_lines=2)

        for i, entry in enumerate(result["subtitles"]):
            assert len(entry["subLines"]) <= 2, \
                f"Entry {i} has {len(entry['subLines'])} lines (> 2)"


class TestChunkTextNoOverflow:
    """Test 5: _chunk_text must not create chunks that overflow 2 lines."""

    def test_no_chunk_exceeds_2_lines(self):
        """No chunk from _chunk_text should wrap to more than 2 lines."""
        from app.video_lab.planners.subtitle_planner import _chunk_text, _wrap_chars
        text = "人工智能技术正在快速改变我们的生活方式，从智能家居到自动驾驶，从医疗诊断到金融分析，各个领域都在经历深刻的变革和创新。"
        chunks = _chunk_text(text, max_chars=20)

        for c in chunks:
            wrapped = _wrap_chars(c, max_chars=20)
            assert len(wrapped) <= 2, \
                f"Chunk '{c}' ({len(c)} chars) wraps to {len(wrapped)} lines (> 2)"


class TestTimeAllocation:
    """Test 6: Time allocation remains correct after splitting."""

    def test_time_sum_equals_segment_duration(self):
        """Split entries' total time should equal the original segment duration."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        text = "这是一个非常长的句子，用来验证时间分配是否正确，确保分配给每个拆分后的字幕条的时间加起来等于原始时长。"
        seg = make_seg(text, start=1.0, dur=10.0)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)

        total_time = sum(e["endSec"] - e["startSec"] for e in entries)
        assert abs(total_time - 10.0) < 0.5, f"Total time {total_time} should be ~10.0"

    def test_entries_have_valid_time_range(self):
        """Each entry must have startSec < endSec."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        text = "这是一个非常长的句子，用来验证时间分配是否正确，确保分配给每个拆分后的字幕条的时间加起来等于原始时长。"
        seg = make_seg(text, start=0.0, dur=10.0)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)

        for i, e in enumerate(entries):
            assert e["startSec"] < e["endSec"], f"Entry {i}: startSec >= endSec"


# ─── V1.2.3 P1: Subtitle style resolution + diagnostics tests ─────────────────

class TestResolveAssSubtitleStyle:
    """Test 1: Different visual routes produce different default subtitle styles."""

    def test_ai_asset_then_compose_style(self):
        """AI 素材 + 合成 route uses higher margin_v and darker back_colour."""
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        style = resolve_ass_subtitle_style(visual_route="ai_asset_then_compose")
        assert style["font_size"] == 34
        assert style["margin_v"] == 190
        assert style["back_colour"] == "&HC0000000"
        assert style["max_chars"] == 20
        assert style["max_lines"] == 2

    def test_template_programmatic_render_style(self):
        """Remotion route uses restrained bottom subtitle."""
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        style = resolve_ass_subtitle_style(visual_route="template_programmatic_render")
        assert style["font_size"] == 32
        assert style["margin_v"] == 160
        assert style["max_chars"] == 20
        assert style["max_lines"] == 2

    def test_local_frame_compose_style(self):
        """Pillow static card uses stable bottom subtitle."""
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        style = resolve_ass_subtitle_style(visual_route="local_frame_compose")
        assert style["font_size"] == 36
        assert style["margin_v"] == 150
        assert style["max_chars"] == 22

    def test_routes_produce_different_styles(self):
        """At least font_size, margin_v, and back_colour differ across routes."""
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        ai = resolve_ass_subtitle_style(visual_route="ai_asset_then_compose")
        rem = resolve_ass_subtitle_style(visual_route="template_programmatic_render")
        lfc = resolve_ass_subtitle_style(visual_route="local_frame_compose")
        # font_size differs
        assert ai["font_size"] != rem["font_size"]
        assert rem["font_size"] != lfc["font_size"]
        # margin_v differs
        assert ai["margin_v"] != rem["margin_v"]
        assert rem["margin_v"] != lfc["margin_v"]
        # back_colour differs across at least two routes
        assert ai["back_colour"] != lfc["back_colour"]

    def test_unknown_route_uses_defaults(self):
        """Unknown route falls back to DEFAULT_ASS_STYLE."""
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style, DEFAULT_ASS_STYLE
        style = resolve_ass_subtitle_style(visual_route="unknown_route_xyz")
        assert style["font_size"] == DEFAULT_ASS_STYLE["font_size"]
        assert style["margin_v"] == DEFAULT_ASS_STYLE["margin_v"]


class TestSubtitleStyleOverride:
    """Test 2: params.subtitleStyle overrides are applied correctly."""

    def test_override_applies_values(self):
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        params = {
            "subtitleStyle": {
                "font_size": 40,
                "margin_v": 220,
                "max_chars": 18,
                "max_lines": 2,
            }
        }
        style = resolve_ass_subtitle_style(visual_route="local_frame_compose", params=params)
        assert style["font_size"] == 40
        assert style["margin_v"] == 220
        assert style["max_chars"] == 18
        assert style["max_lines"] == 2

    def test_unknown_keys_ignored(self):
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        params = {
            "subtitleStyle": {
                "font_size": 40,
                "unknown_key": "xxx",
                "another_bad": 123,
            }
        }
        style = resolve_ass_subtitle_style(visual_route="local_frame_compose", params=params)
        assert style["font_size"] == 40
        assert "unknown_key" not in style
        assert "another_bad" not in style

    def test_override_clamps_to_safe_range(self):
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        params = {
            "subtitleStyle": {
                "font_size": 999,      # way above 56 max
                "margin_v": -1,        # below 80 min
                "max_chars": 999,      # above 30 max
                "max_lines": 99,       # above 3 max
            }
        }
        style = resolve_ass_subtitle_style(visual_route="local_frame_compose", params=params)
        assert style["font_size"] == 56   # clamp to upper limit
        assert style["margin_v"] == 80    # clamp to lower limit
        assert style["max_chars"] == 30   # clamp to upper limit
        assert style["max_lines"] == 3    # clamp to upper limit

    def test_override_clamps_below_minimum(self):
        from app.video_lab.planners.subtitle_planner import resolve_ass_subtitle_style
        params = {
            "subtitleStyle": {
                "font_size": 10,        # below 24 min
                "margin_v": 10,        # below 80 min
                "max_chars": 5,        # below 14 min
                "max_lines": 0,        # below 1 min
            }
        }
        style = resolve_ass_subtitle_style(visual_route="local_frame_compose", params=params)
        assert style["font_size"] == 24
        assert style["margin_v"] == 80
        assert style["max_chars"] == 14
        assert style["max_lines"] == 1


class TestSubtitleDiagnostics:
    """Test 4 & 5: Diagnostics detect too-fast and over-limit entries."""

    def test_diagnostics_detects_too_fast(self):
        from app.video_lab.planners.subtitle_planner import analyze_subtitle_entries
        subtitles = [
            {"startSec": 0.0, "endSec": 0.3, "text": "短", "subLines": ["短"]},
            {"startSec": 0.3, "endSec": 3.0, "text": "正常字幕", "subLines": ["正常字幕"]},
        ]
        result = analyze_subtitle_entries(subtitles, max_chars=22, max_lines=2)
        assert result["hasTooFastEntries"] is True
        assert result["tooFastCount"] == 1
        assert result["minDurationSec"] == 0.3

    def test_diagnostics_detects_over_line_limit(self):
        from app.video_lab.planners.subtitle_planner import analyze_subtitle_entries
        # One entry has 3 lines while max_lines=2
        subtitles = [
            {"startSec": 0.0, "endSec": 3.0, "text": "三行内容", "subLines": ["第一行", "第二行", "第三行"]},
        ]
        result = analyze_subtitle_entries(subtitles, max_chars=22, max_lines=2)
        assert result["hasOverLineLimit"] is True
        assert result["overLineLimitCount"] == 1
        assert result["maxLinesPerEntry"] == 3

    def test_diagnostics_detects_over_char_limit(self):
        from app.video_lab.planners.subtitle_planner import analyze_subtitle_entries
        # One line exceeds max_chars=22 (this string is 26 chars)
        long_line = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 26 chars
        subtitles = [
            {"startSec": 0.0, "endSec": 3.0, "text": long_line, "subLines": [long_line]},
        ]
        result = analyze_subtitle_entries(subtitles, max_chars=22, max_lines=2)
        assert result["hasOverCharLimit"] is True
        assert result["overCharLimitCount"] == 1
        assert result["maxLineLength"] == 26

    def test_diagnostics_empty_list(self):
        from app.video_lab.planners.subtitle_planner import analyze_subtitle_entries
        result = analyze_subtitle_entries([], max_chars=22, max_lines=2)
        assert result["subtitleCount"] == 0
        assert result["hasTooFastEntries"] is False
        assert result["tooFastCount"] == 0

    def test_diagnostics_avg_duration(self):
        from app.video_lab.planners.subtitle_planner import analyze_subtitle_entries
        subtitles = [
            {"startSec": 0.0, "endSec": 1.0, "text": "A", "subLines": ["A"]},
            {"startSec": 1.0, "endSec": 3.0, "text": "B", "subLines": ["B"]},
        ]
        result = analyze_subtitle_entries(subtitles, max_chars=22, max_lines=2)
        assert result["avgDurationSec"] == 1.5
        assert result["minDurationSec"] == 1.0
        assert result["maxDurationSec"] == 2.0


class TestSrtReturnsDiagnostics:
    """Test: generate_srt_from_segments returns subtitleDiagnostics."""

    def test_srt_result_contains_diagnostics(self):
        from app.video_lab.planners.subtitle_planner import generate_srt_from_segments
        segments = [
            {"text": "这是一个测试字幕。", "startSec": 0.0, "durationSec": 3.0},
        ]
        result = generate_srt_from_segments(segments)
        assert "subtitleDiagnostics" in result
        d = result["subtitleDiagnostics"]
        assert "subtitleCount" in d
        assert "tooFastCount" in d
        assert "overLineLimitCount" in d
        assert "overCharLimitCount" in d
        assert d["subtitleCount"] >= 1


class TestAssReturnsDiagnostics:
    """Test: generate_ass_from_segments returns subtitleDiagnostics."""

    def test_ass_result_contains_diagnostics(self):
        from app.video_lab.planners.subtitle_planner import generate_ass_from_segments
        segments = [
            {"text": "这是一个测试字幕。", "startSec": 0.0, "durationSec": 3.0},
        ]
        result = generate_ass_from_segments(segments)
        assert "subtitleDiagnostics" in result
        d = result["subtitleDiagnostics"]
        assert "subtitleCount" in d
        assert d["subtitleCount"] >= 1

    def test_ass_result_contains_style(self):
        from app.video_lab.planners.subtitle_planner import generate_ass_from_segments
        segments = [
            {"text": "测试", "startSec": 0.0, "durationSec": 2.0},
        ]
        result = generate_ass_from_segments(segments)
        assert "style" in result
        assert "font_size" in result["style"]


class TestP0NoRegression:
    """Test 6: P0 no-truncation behavior is preserved."""

    def test_long_text_still_splits_not_truncates(self):
        """Long sentences still split into multiple entries, never truncate."""
        from app.video_lab.planners.subtitle_planner import _segment_to_entries
        text = "人工智能技术正在快速改变我们的生活方式，从智能家居到自动驾驶，从医疗诊断到金融分析，各个领域都在经历深刻的变革和创新。"
        seg = make_seg(text, start=0.0, dur=10.0)
        entries = _segment_to_entries(seg, max_chars=20, max_lines=2)
        assert len(entries) >= 2, "Must create multiple entries, not truncate"

    def test_no_text_loss_after_resolve_style(self):
        """Text loss must not occur regardless of resolved style parameters."""
        from app.video_lab.planners.subtitle_planner import (
            resolve_ass_subtitle_style,
            generate_srt_from_segments,
            generate_ass_from_segments,
        )
        params = {"subtitleStyle": {"font_size": 50, "margin_v": 280, "max_chars": 28}}
        segments = [
            make_seg("短句。", start=0.0, dur=2.0),
            make_seg("这是一个非常长的句子，用来测试字幕拆分功能是否正常工作，确保没有任何字符被截断或遗漏。", start=2.0, dur=8.0),
            make_seg("最后一句。", start=10.0, dur=2.0),
        ]
        srt = generate_srt_from_segments(segments)
        ass = generate_ass_from_segments(
            segments,
            style=resolve_ass_subtitle_style(visual_route="ai_asset_then_compose", params=params),
        )
        srt_text = get_all_subtitle_text(srt["subtitles"])
        ass_text = get_all_subtitle_text(ass["subtitles"])
        original = "".join(s["text"] for s in segments)
        assert normalize_text(srt_text) == normalize_text(original)
        assert normalize_text(ass_text) == normalize_text(original)


