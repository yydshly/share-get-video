"""
LLM Content Planner - 用大模型把报告规划成"适合视频展示"的结构

产出 ShotPlan：
{
  "coverTitle": "今日AI前沿速览",
  "opening": "<口播开场，钩子>",
  "shots": [
     {"headline": "<短标题 6-12字>", "display": "<卡片展示文案 <=42字，保留关键数字>",
      "narration": "<口播文案 自然口语，保留关键数字>"},
     ...
  ],
  "closing": "<口播收尾>",
  "source": "llm" | "fallback"
}

设计目标（对应用户反馈）：
- 展示合理：headline 短、display 精炼可完整显示（不再截断）
- 信息准确：要求保留关键数字与主体，不编造
- 视频友好：narration 精炼，避免成片过长
LLM 不可用/失败时回退到确定性规划（基于现有 content_structurer）。
"""

from __future__ import annotations

import re
from typing import Any

from app.video_lab.providers.minimax import MiniMaxChatClient
from app.video_lab.planners.content_structurer import structure_content
from app.video_lab.renderers.text_layout import split_headline_and_detail


# V0.3.6-b1: Added opening hook requirement and emphasisTerms extraction
_SYSTEM_PROMPT = (
    "你是资深短视频编导，把信息密集的中文资讯改写成竖屏短视频脚本。"
    "最高原则：忠实、完整、不丢信息。必须逐条处理，禁止合并、删减或省略任何一条要点；"
    "每条都要完整保留其核心语义、关键数字/百分比、机构名与专有名词、核心结论；"
    "只做语言顺化和去冗余，不得为了简短而牺牲信息。不得编造或夸大。"
    "输出必须是严格的 JSON，不要任何额外解释或 markdown 代码块。"
    "\n"
    "重要：opening 必须是能引起好奇心的钩子句，不要写'今天为你梳理'这种流水账开头。"
    "opening 要表达冲突、趋势或判断，例如：'不是模型更强，而是AI正在落地'。"
    "\n"
    "重要：每条 shot 必须包含 emphasisTerms 数组，列出该条最值得在视频中突出的关键词（1-4个）。"
    "emphasisTerms 优先级：数字/百分比 > 英文模型/系统名 > 机构名 > 关键术语。"
    "emphasisTerms 必须来自原文/display/narration，不允许编造。"
)


def _build_user_prompt(lead: str, items: list[dict]) -> str:
    n = len(items)
    lines = []
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it.get('title', '').strip()}")
    items_block = "\n".join(lines)
    return (
        f"下面是一份 AI 资讯报告，共 {n} 条要点（总起：{lead}）。\n"
        f"请严格按顺序逐条改写，输出**恰好 {n} 条** shots，与下面编号一一对应，不要合并/增删/调序。\n"
        "每条输出四个字段：\n"
        "- headline: 6-14 字短标题，体现该条的具体主体（如系统名/机构名），不要写成笼统的大类\n"
        "- display: 卡片正文，用通顺的一句话**完整呈现该条核心信息**，必须包含关键数字/百分比/机构名/核心结论，"
        "不要为了短而省略关键事实（长度以信息完整为准，约 30-80 字）\n"
        "- narration: 口播文案，自然口语，完整传达该条信息（保留关键数字），可比 display 略详细\n"
        "- emphasisTerms: 数组，该条最值得突出的 1-4 个关键词，优先数字/百分比/模型名/系统名/机构名，如 []\n"
        "- tone: 该条的语义基调，只能取 positive（突破/提升/达成）/ negative（短板/漏洞/落后/风险）/ neutral（合作/发布/中性）之一\n"
        "再输出：coverTitle（<=16字封面标题）、opening（<=30字开场钩子句，要有观点/冲突/趋势，不要流水账）、closing（<=24字收尾口播）。\n"
        "严格输出 JSON：\n"
        '{"coverTitle":"...","opening":"...","shots":[{"headline":"...","display":"...","narration":"...","emphasisTerms":["..."],"tone":"positive"}],"closing":"..."}\n\n'
        f"待改写的 {n} 条要点：\n{items_block}"
    )


def _clamp(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


# V0.3.6-b1: emphasisTerms extraction
# Priority: percentages > number+unit > english model/system names > key terms
_KNOWN_MODELS = {
    "GPT", "GPT-5", "Claude", "Claude-4", "Gemini", "Llama", "Mistral",
    "Med-PaLM", "MedPaLM", "ProReviewer", "OpenMedQ", "BBVA", "OpenAI",
    "Anthropic", "DeepMind", "Google", "Meta", "Apple", "Microsoft",
}


def _extract_emphasis_terms(text: str, max_terms: int = 4) -> list[str]:
    """
    Extract up to max_terms emphasis keywords from text.
    Priority: percentages > number+unit > known model names > capitalized terms.
    Returns deduplicated, non-empty terms.
    """
    if not text:
        return []
    terms: list[str] = []
    seen: set[str] = set()

    # 1. Percentages: 88.9%, 72%, 39% etc.
    for m in re.findall(r"\d+\.?\d*%", text):
        if m not in seen:
            seen.add(m)
            terms.append(m)

    # 2. Number + unit: 10倍, 100万, 5620亿, 5x etc.
    for m in re.findall(r"\d+\.?\d*(?:倍|x|万|亿|千|[kmgKMG])", text):
        if m not in seen:
            seen.add(m)
            terms.append(m)

    # 3. Known model/system names (case-sensitive check)
    for model in _KNOWN_MODELS:
        # word-boundary match
        pattern = r"(?<![A-Za-z])" + re.escape(model) + r"(?![A-Za-z])"
        for m in re.findall(pattern, text):
            if m not in seen:
                seen.add(m)
                terms.append(m)

    if len(terms) < max_terms:
        # 4. Capitalized multi-word terms (potential proper nouns)
        for m in re.findall(r"[A-Z][a-z]+(?:[A-Z][a-z]+)+", text):
            if m not in seen:
                seen.add(m)
                terms.append(m)
                if len(terms) >= max_terms:
                    break

    return terms[:max_terms]


def _shot_from_item(item: dict) -> dict:
    """从单条源条目确定性生成 shot（用于回退或补全缺失条目，保证不丢信息）。
    V0.3.6-b1: includes emphasisTerms extracted from the content.
    """
    full = (item.get("title", "") or "").strip()
    headline, detail = split_headline_and_detail(full)
    body_text = detail or full
    return {
        "headline": _clamp(headline, 16),
        "display": body_text,   # 完整保留，不截断（卡片自适应字号承载）
        "narration": full,
        "emphasisTerms": _extract_emphasis_terms(f"{headline} {body_text}", max_terms=4),
    }


def plan_shots(
    raw_content: str,
    max_items: int = 6,
    test_case_id: str = "",
    use_llm: bool = True,
) -> dict[str, Any]:
    """把报告规划成 ShotPlan，逐条 1:1 处理，保证信息完整不丢条。"""
    structured = structure_content(raw_content, test_case_id or "ai_insight_summary")
    items = structured.get("items", [])[:max_items]
    lead = structured.get("lead", "")

    if use_llm and items:
        client = MiniMaxChatClient()
        if client.is_configured():
            result = client.chat_json(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(lead, items)},
                ],
                temperature=0.2,
                max_tokens=6000,
            )
            if result.get("success") and isinstance(result.get("json"), dict):
                plan = _normalize_plan(result["json"], items, lead)
                if plan["shots"]:
                    plan["source"] = "llm"
                    return plan

    # 回退：确定性规划
    return _fallback_plan(raw_content, max_items, test_case_id)


def _find_shot_list(raw: dict) -> list:
    """容错地找出要点数组（模型可能用 shots/items/subtitle/points 等不同键名）。"""
    for key in ("shots", "items", "subtitle", "subtitles", "points", "keyPoints", "list", "segments"):
        v = raw.get(key)
        if isinstance(v, list) and v:
            return v
    # 兜底：取第一个"元素是含 headline/display/title 的 dict"的列表
    for v in raw.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            if any(k in v[0] for k in ("headline", "display", "title", "narration", "body")):
                return v
    return []


def _normalize_plan(raw: dict, items: list[dict], lead: str) -> dict[str, Any]:
    """把 LLM 输出对齐到源条目（1:1，不丢条）。

    V0.3.6-b1:
    - 按编号对齐：第 i 条 shot 对应第 i 条源条目；
    - LLM 缺失/为空的条目，用源条目确定性补全（保证信息完整）；
    - display/narration 不做硬截断（卡片自适应字号承载完整文本），仅 headline 适度收敛。
    - emphasisTerms: 优先使用 LLM 返回的，否则从 headline+display 自动提取。
    """
    shots_in = _find_shot_list(raw)
    n = len(items)
    shots = []
    for i in range(n):
        src = items[i]
        s = shots_in[i] if i < len(shots_in) and isinstance(shots_in[i], dict) else {}
        headline = (s.get("headline") or s.get("title") or "").strip()
        display = (s.get("display") or s.get("body") or "").strip()
        narration = (s.get("narration") or s.get("voiceover") or "").strip()

        # V0.3.6-b1-fix: 先完成 fallback 补全，再提取 emphasisTerms
        det = _shot_from_item(src)
        if not headline:
            headline = det["headline"]
        if not display:
            display = det["display"]
        if not narration:
            narration = display or det["narration"]

        # V0.3.6-b1-fix: emphasisTerms - use LLM value or auto-extract from resolved text
        raw_emphasis = s.get("emphasisTerms")
        if isinstance(raw_emphasis, list) and raw_emphasis:
            # Deduplicate, remove empty strings, cap at 4
            emp = list(dict.fromkeys(e.strip() for e in raw_emphasis if isinstance(e, str) and e.strip()))[:4]
        else:
            # Auto-extract from resolved content (after fallback fill)
            emp = _extract_emphasis_terms(f"{headline} {display} {narration}", max_terms=4)

        tone = (s.get("tone") or "").strip().lower()
        if tone not in ("positive", "negative", "neutral"):
            tone = ""  # 留空，渲染器按文本推断
        shots.append({
            "headline": _clamp(headline, 18),
            "display": display,          # 不截断
            "narration": narration,      # 不截断
            "emphasisTerms": emp,
            "tone": tone,
        })

    cover_default, _ = split_headline_and_detail(lead)
    return {
        "coverTitle": _clamp(raw.get("coverTitle") or raw.get("title") or cover_default or "今日AI前沿速览", 18),
        "opening": (raw.get("opening") or "").strip() or "今天AI圈的重点，正在从能力走向落地。",
        "shots": shots,
        "closing": (raw.get("closing") or "").strip() or "以上就是今天的要点，感谢观看。",
    }


def _fallback_plan(raw_content: str, max_items: int, test_case_id: str) -> dict[str, Any]:
    """确定性兜底：用 content_structurer 拆分，标题/详情切分。"""
    structured = structure_content(raw_content, test_case_id or "ai_insight_summary")
    lead = structured.get("lead", "")
    cover_headline, _ = split_headline_and_detail(lead)
    shots = [_shot_from_item(item) for item in structured.get("items", [])[:max_items]]
    return {
        "coverTitle": _clamp(cover_headline or "今日AI前沿速览", 18),
        "opening": _clamp(lead, 50) if lead else "今天AI圈的重点，正在从能力走向落地。",
        "shots": shots,
        "closing": "以上就是今天的要点，感谢观看。",
        "source": "fallback",
    }
