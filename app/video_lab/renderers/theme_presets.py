"""
Theme Presets - 主题自适应样式

按每条新闻的语义基调（tone）自动配色 + 配图标，让卡片"一眼传达情绪"、天然差异化：
- positive（突破/提升/达成/增长）→ 绿色调 + 上升图标
- negative（短板/漏洞/落后/风险）→ 琥珀色调 + 警示圆环
- neutral （合作/发布/推出）      → 蓝色调 + 星亮图标

供 Pillow 渲染器与 Remotion props_builder 共用。
"""

from typing import Any

TONE_STYLES: dict[str, dict[str, str]] = {
    "positive": {"accent": "#22c55e", "highlight": "#86efac", "icon": "arrow"},
    "negative": {"accent": "#f59e0b", "highlight": "#fcd34d", "icon": "ring"},
    "neutral":  {"accent": "#3b82f6", "highlight": "#60a5fa", "icon": "spark"},
}

DEFAULT_TONE = "neutral"

_NEGATIVE_WORDS = (
    "短板", "不足", "落后", "漏洞", "风险", "下降", "失败", "问题", "挑战",
    "警示", "攻击", "缺陷", "差距", "受限", "瓶颈", "错误", "欺骗", "威胁",
)
_POSITIVE_WORDS = (
    "突破", "提升", "超越", "增长", "新范式", "领先", "成功", "加速", "提高",
    "达成", "创新", "优化", "改进", "首次", "最佳", "实现", "推动",
)


def infer_tone(text: str) -> str:
    """从文本启发式推断基调（LLM 未提供 tone 时的兜底）。"""
    t = text or ""
    neg = sum(1 for w in _NEGATIVE_WORDS if w in t)
    pos = sum(1 for w in _POSITIVE_WORDS if w in t)
    if neg > pos:
        return "negative"
    if pos > neg:
        return "positive"
    return DEFAULT_TONE


def tone_to_style(tone: str | None) -> dict[str, str]:
    """tone → 样式预设（accent/highlight/icon 的 hex/名称）。未知归 neutral。"""
    return TONE_STYLES.get((tone or "").strip().lower(), TONE_STYLES[DEFAULT_TONE])


def resolve_shot_tone(kp: dict[str, Any]) -> str:
    """取 keypoint 的 tone：优先 LLM 给的，否则按标题+正文推断。"""
    tone = (kp.get("tone") or "").strip().lower()
    if tone in TONE_STYLES:
        return tone
    text = f"{kp.get('headline') or kp.get('title') or ''} {kp.get('display') or kp.get('body') or ''}"
    return infer_tone(text)
