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

