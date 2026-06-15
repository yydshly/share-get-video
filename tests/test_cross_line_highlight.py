"""
tests/test_cross_line_highlight.py
V0.5.2: 关键词跨行也能高亮（如 "57-77%" 被换行拆成 "57-" / "77%"）
"""

from app.video_lab.renderers import frame_templates as ft

HL = (245, 158, 11)
BASE = (255, 255, 255)


class _FakeDraw:
    def __init__(self):
        self.calls = []  # (segment, fill)

    def text(self, pos, seg, font=None, fill=None):
        self.calls.append((seg, fill))

    def textbbox(self, pos, seg, font=None):
        return (0, 0, len(seg) * 10, 20)


def test_highlight_spans_across_line_break():
    """'57-77%' 被拆到两行，两部分都应高亮。"""
    fake = _FakeDraw()
    # 第一行以 '57-' 结尾，第二行以 '77%' 开头
    lines = ["通过率仅57-", "77%，多轮场景更差"]
    ft._draw_lines_with_highlights(
        fake, lines, 0, 0, font=None, line_h=30,
        base_color=BASE, highlight_color=HL, emphasis_terms=["57-77%"],
    )
    hl_text = "".join(seg for seg, fill in fake.calls if fill == HL)
    assert "57-" in hl_text and "77%" in hl_text, f"跨行高亮失败: {fake.calls}"
    # 非关键词部分应为基础色
    base_text = "".join(seg for seg, fill in fake.calls if fill == BASE)
    assert "多轮场景更差" in base_text


def test_no_highlight_when_no_terms():
    fake = _FakeDraw()
    ft._draw_lines_with_highlights(
        fake, ["纯文字没有数字"], 0, 0, font=None, line_h=30,
        base_color=BASE, highlight_color=HL, emphasis_terms=[],
    )
    # 全部基础色
    assert all(fill == BASE for _, fill in fake.calls)


def test_single_line_term_still_highlights():
    fake = _FakeDraw()
    ft._draw_lines_with_highlights(
        fake, ["提升了39%而已"], 0, 0, font=None, line_h=30,
        base_color=BASE, highlight_color=HL, emphasis_terms=["39%"],
    )
    hl_text = "".join(seg for seg, fill in fake.calls if fill == HL)
    assert "39%" in hl_text


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
