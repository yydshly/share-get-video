"""
Tests for V0.3.8.1 ASS subtitle planner.
- ASS file includes PlayResX/Y for proper FFmpeg/libass scaling
- ASS file includes Fontsize and MarginV in Style
- ASS Dialogue events correspond to segments
- Max chars per line is respected
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.video_lab.planners.subtitle_planner import (
    generate_ass_from_segments,
    DEFAULT_ASS_STYLE,
)


def test_ass_contains_playresx_and_playresy():
    """ASS file must declare PlayResX and PlayResY for proper scaling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "subtitles.ass"
        generate_ass_from_segments(
            [{"text": "你好世界", "startSec": 0, "durationSec": 2}],
            output_path=out,
            play_res_x=1080,
            play_res_y=1920,
        )
        content = out.read_text(encoding="utf-8")
        assert "PlayResX: 1080" in content
        assert "PlayResY: 1920" in content


def test_ass_style_has_fontsize_and_marginv():
    """ASS Style line must include FontSize and MarginV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "subtitles.ass"
        result = generate_ass_from_segments(
            [{"text": "测试", "startSec": 0, "durationSec": 2}],
            output_path=out,
        )
        content = out.read_text(encoding="utf-8")
        style_fontsize = str(result["style"]["font_size"])
        style_marginv = str(result["style"]["margin_v"])
        assert f"FontSize: {style_fontsize}" not in content  # note: it's "Fontsize" lowercase in ass Style line
        # The Style line format uses Fontsize (lowercase) per ASS spec
        assert f",{style_fontsize}," in content
        assert f",{style_marginv}," in content
        # Margins are at end: MarginL,MarginR,MarginV,Encoding
        assert "MarginV=" not in content  # we use ASS format, not force_style


def test_ass_events_match_segments():
    """ASS Dialogue events should be one per segment with start/end time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "subtitles.ass"
        segments = [
            {"text": "第一句", "startSec": 0, "durationSec": 2},
            {"text": "第二句", "startSec": 2, "durationSec": 3},
        ]
        generate_ass_from_segments(segments, output_path=out)
        content = out.read_text(encoding="utf-8")
        # Two Dialogue lines
        assert content.count("Dialogue:") == 2
        assert "第一句" in content
        assert "第二句" in content


def test_ass_respects_max_chars():
    """Long text should be split into multiple lines (max 2)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "subtitles.ass"
        long_text = "今天有非常多非常多非常多非常多非常多的内容需要分成多行"
        result = generate_ass_from_segments(
            [{"text": long_text, "startSec": 0, "durationSec": 5}],
            output_path=out,
            max_chars=10,
        )
        sub = result["subtitles"][0]
        # Should have at most 2 lines
        assert len(sub["subLines"]) <= 2
        # Each line should be <= 10 chars
        for line in sub["subLines"]:
            assert len(line) <= 10


def test_ass_url_is_returned():
    """assUrl should be a /runtime/... URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "subtitles.ass"
        result = generate_ass_from_segments(
            [{"text": "hi", "startSec": 0, "durationSec": 1}],
            output_path=out,
        )
        assert result["assPath"] == str(out)
        assert result["assUrl"].endswith("subtitles.ass")
        assert result["format"] == "ass"


def test_default_ass_style_has_safe_area():
    """Default ASS style must use bottom-center alignment with safe margins."""
    assert DEFAULT_ASS_STYLE["alignment"] == 2  # bottom center
    assert DEFAULT_ASS_STYLE["margin_v"] >= 200  # bottom safe area
    assert DEFAULT_ASS_STYLE["font_size"] <= 40  # not too big
    assert DEFAULT_ASS_STYLE["max_lines"] == 2
    assert DEFAULT_ASS_STYLE["outline"] >= 1


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
