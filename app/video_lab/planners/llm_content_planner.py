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
# V0.3.6-quality-p0: Added metrics field
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
    "\n"
    "重要：每条 shot 可选包含 metrics 数组（最多2个），格式："
    "[{\"label\": \"质量提升\", \"value\": 39, \"unit\": \"%\"}] 或 "
    "[{\"label\": \"通过率\", \"value\": 77, \"min\": 57, \"max\": 77, \"unit\": \"%\"}]。"
    "metrics 必须来自原文，不允许编造数值。"
    "\n"
    # V0.8.3: coverTitle must NOT just be the first item's headline
    "重要：coverTitle 必须概括整组内容的共同主题或趋势，不得只使用第一条要点标题。"
    "如果内容包含多个方向，coverTitle 应表达整体趋势，例如「AI评估与落地加速」「AI应用走向真实场景」。"
)


def _build_user_prompt(lead: str, items: list[dict], target_duration_sec: float | None = None) -> str:
    n = len(items)
    lines = []
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it.get('title', '').strip()}")
    items_block = "\n".join(lines)

    # V0.8.3: 旁白时长预算。如果 target_duration_sec 未传，给一个保守默认 45。
    target = float(target_duration_sec) if target_duration_sec and target_duration_sec > 0 else 45.0
    # 按"约 3.5 字/秒"估一个保守的字符预算（中文 TTS 实测值）
    if target <= 45 and n <= 3:
        # 默认 / 紧凑预算
        opening_max = 18
        narration_max = 45
        closing_max = 16
    elif target <= 60 and n <= 4:
        opening_max = 22
        narration_max = 60
        closing_max = 18
    else:
        opening_max = 28
        narration_max = 75
        closing_max = 22
    budget_lines = [
        f"本视频目标总时长约 {target:.0f} 秒。",
        "opening + 所有 narration + closing 必须控制在目标时长内。",
        f"opening 不超过 {opening_max} 个中文字符。",
        f"每条 narration 不超过 {narration_max} 个中文字符。",
        f"closing 不超过 {closing_max} 个中文字符。",
        "display 可以相对完整，但 narration 必须更短、更适合口播。",
        "不要把所有细节都塞进口播，优先保留主体、关键数字、核心结论。",
    ]
    budget_block = "\n".join(budget_lines)

    return (
        f"下面是一份 AI 资讯报告，共 {n} 条要点（总起：{lead}）。\n"
        f"请严格按顺序逐条改写，输出**恰好 {n} 条** shots，与下面编号一一对应，不要合并/增删/调序。\n"
        f"【旁白时长预算】\n{budget_block}\n"
        "每条输出字段：\n"
        "- headline: 6-14 字短标题，体现该条的具体主体（如系统名/机构名），不要写成笼统的大类\n"
        "- display: 卡片正文，用通顺的一句话**完整呈现该条核心信息**，必须包含关键数字/百分比/机构名/核心结论，"
        "不要为了短而省略关键事实（长度以信息完整为准，约 30-80 字）\n"
        "- narration: 口播文案，自然口语，受字数预算限制（见上），完整传达该条信息（保留关键数字）\n"
        "- emphasisTerms: 数组，该条最值得突出的 1-4 个关键词，优先数字/百分比/模型名/系统名/机构名，如 []\n"
        "- tone: 该条的语义基调，只能取 positive（突破/提升/达成）/ negative（短板/漏洞/落后/风险）/ neutral（合作/发布/中性）之一\n"
        "- metrics: 数组，该条的关键数据可视化指标（最多2个），如 [{\"label\":\"质量提升\",\"value\":39,\"unit\":\"%\"}]；"
        "区间值用 {\"label\":\"通过率\",\"value\":77,\"min\":57,\"max\":77,\"unit\":\"%\"}；无数据则填 []\n"
        "再输出：coverTitle（**必须概括整组内容的共同主题或趋势，不得只使用第一条要点标题**；≤16字封面标题）、"
        "opening（见上字数上限，开场钩子句，要有观点/冲突/趋势，不要流水账）、"
        "closing（见上字数上限，收尾口播）。\n"
        "严格输出 JSON：\n"
        '{"coverTitle":"...","opening":"...","shots":[{"headline":"...","display":"...","narration":"...","emphasisTerms":["..."],"tone":"positive","metrics":[{"label":"...","value":0,"unit":"..."}]}],"closing":"..."}\n\n'
        f"待改写的 {n} 条要点：\n{items_block}"
    )


def _clamp(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


# V0.5.7: 关键点卡标题可换行、封面/总结列表宽度可容 ~30 字，
# 18 字上限会把"ProReviewer论文评审系统发布"这类常见标题截成"…"。
# 放宽到 24，让简洁标题完整呈现，仍足够短以适配各页排版。
HEADLINE_MAX = 24

# V0.8.3: 旁白时长预算硬保护（即使 LLM 不听话也要截断）。
# display 故意不截断，因为它用于画面展示；narration 必须更短以匹配音频时长。
NARRATION_MAX = 48
OPENING_MAX = 22
CLOSING_MAX = 18
# 保守兜底封面标题：当 LLM 返回的 coverTitle 不可靠或与第一条要点强绑定时使用。
COVER_TITLE_FALLBACK = "AI前沿趋势速览"


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


# V0.3.6-quality-p0: metrics extraction
_METRIC_UNIT_MAP = {
    "%": "%",
    "倍": "倍",
    "分": "分",
    "万": "万",
    "亿": "亿",
    "美元": "美元",
    "千万美元": "千万美元",
    "百万美元": "百万美元",
}


def _extract_metrics(text: str, max_metrics: int = 2) -> list[dict]:
    """
    Fallback regex-based metric extraction from text.
    Extracts up to max_metrics metrics, each with label/value/unit.
    Priority: percentages > numbers with units.
    """
    if not text:
        return []
    metrics: list[dict] = []
    seen_vals: set[str] = set()

    # 1. Percentages: 88.9%, 72%, 39%, 57-77%
    # Range: 57-77% (only one % at the end)
    for m in re.finditer(r"(\d+\.?\d*)-(\d+\.?\d*)%", text):
        min_val, max_val = m.group(1), m.group(2)
        key = f"{min_val}-{max_val}%"
        if key not in seen_vals:
            seen_vals.add(key)
            # Also block individual ends so they aren't re-captured
            seen_vals.add(f"{min_val}%")
            seen_vals.add(f"{max_val}%")
            metrics.append({
                "label": "区间",
                "value": float(max_val),
                "min": float(min_val),
                "max": float(max_val),
                "unit": "%",
            })
            if len(metrics) >= max_metrics:
                break
    if len(metrics) < max_metrics:
        for m in re.finditer(r"(?<!\d\.)(\d+(?:\.\d+)?)%", text):
            key = m.group(0)
            if key not in seen_vals:
                seen_vals.add(key)
                val = float(m.group(1))
                metrics.append({
                    "label": "比例",
                    "value": val,
                    "unit": "%",
                })
                if len(metrics) >= max_metrics:
                    break

    # 2. Numbers with units: 10倍, 100万, 5620亿, 5个, 千万美元
    # V0.3.6-quality-p0-fix: long currency units before short to prevent early capture
    if len(metrics) < max_metrics:
        for m in re.finditer(r"(\d+\.?\d*)\s*(千万美元|百万美元|万美元|亿美元|倍|x|万|亿|千|个|美元)", text):
            val_str, unit = m.group(1), m.group(2)
            key = f"{val_str}{unit}"
            if key not in seen_vals:
                seen_vals.add(key)
                val = float(val_str)
                if unit in ("千万美元", "百万美元", "万美元", "亿美元", "万", "亿"):
                    label = "金额"
                elif unit in ("倍", "x"):
                    label = "倍数"
                else:
                    label = "数量"
                metrics.append({
                    "label": label,
                    "value": val,
                    "unit": unit,
                })
                if len(metrics) >= max_metrics:
                    break

    return metrics[:max_metrics]


def _validate_metrics(raw: list) -> list[dict]:
    """Validate and normalize a list of raw metric dicts."""
    result = []
    for m in raw:
        if not isinstance(m, dict):
            continue
        val = m.get("value")
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue
        unit = str(m.get("unit", "")).strip() or ""
        label = str(m.get("label", "指标")).strip() or "指标"
        entry: dict[str, Any] = {"label": label, "value": val, "unit": unit}
        mn = m.get("min")
        mx = m.get("max")
        if mn is not None and mx is not None:
            try:
                entry["min"] = float(mn)
                entry["max"] = float(mx)
            except (TypeError, ValueError):
                pass
        result.append(entry)
    return result[:2]  # max 2 metrics per shot


def _shot_from_item(item: dict) -> dict:
    """从单条源条目确定性生成 shot（用于回退或补全缺失条目，保证不丢信息）。
    V0.3.6-b1: includes emphasisTerms extracted from the content.
    V0.3.6-quality-p0: includes metrics extracted from the content.
    """
    full = (item.get("title", "") or "").strip()
    headline, detail = split_headline_and_detail(full)
    body_text = detail or full
    return {
        "headline": _clamp(headline, 16),
        "display": body_text,   # 完整保留，不截断（卡片自适应字号承载）
        "narration": full,
        "emphasisTerms": _extract_emphasis_terms(f"{headline} {body_text}", max_terms=4),
        "metrics": _extract_metrics(f"{headline} {body_text}", max_metrics=2),
    }


def plan_shots(
    raw_content: str,
    max_items: int = 6,
    test_case_id: str = "",
    use_llm: bool = True,
    target_duration_sec: float | None = None,  # V0.8.3: 旁白时长预算
) -> dict[str, Any]:
    """把报告规划成 ShotPlan，逐条 1:1 处理，保证信息完整不丢条。

    V0.8.3: 新增 target_duration_sec 用于约束 opening/narration/closing 字符预算。
    """
    structured = structure_content(raw_content, test_case_id or "ai_insight_summary")
    items = structured.get("items", [])[:max_items]
    lead = structured.get("lead", "")

    if use_llm and items:
        client = MiniMaxChatClient()
        if client.is_configured():
            result = client.chat_json(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(lead, items, target_duration_sec)},
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
    return _fallback_plan(raw_content, max_items, test_case_id, target_duration_sec)


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

    V0.8.3:
    - 对 narration / opening / closing 做硬字数截断（保护音频时长）；
    - coverTitle 拒绝直接取 lead 的第一句或第一条要点 headline，
      优先 LLM 返回的概要式标题，否则用兜底 "AI前沿趋势速览"。
    """
    shots_in = _find_shot_list(raw)
    n = len(items)
    shots = []
    first_headline_norm = ""  # 用于 V0.8.3 coverTitle 与"第一条要点绑死"检测
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

        if i == 0:
            first_headline_norm = re.sub(r"\s+", "", headline or "")

        # V0.3.6-b1-fix: emphasisTerms - use LLM value or auto-extract from resolved text
        raw_emphasis = s.get("emphasisTerms")
        if isinstance(raw_emphasis, list) and raw_emphasis:
            # Deduplicate, remove empty strings, cap at 4
            emp = list(dict.fromkeys(e.strip() for e in raw_emphasis if isinstance(e, str) and e.strip()))[:4]
        else:
            # Auto-extract from resolved content (after fallback fill)
            emp = _extract_emphasis_terms(f"{headline} {display} {narration}", max_terms=4)

        # V0.3.6-quality-p0: metrics - use LLM value or fallback regex extraction
        raw_metrics = s.get("metrics")
        if isinstance(raw_metrics, list) and raw_metrics:
            metrics = _validate_metrics(raw_metrics)
        else:
            # Fallback: extract from resolved text
            metrics = _extract_metrics(f"{headline} {display} {narration}")

        tone = (s.get("tone") or "").strip().lower()
        if tone not in ("positive", "negative", "neutral"):
            tone = ""  # 留空，渲染器按文本推断

        # V0.8.3: narration 硬截断保护（决定 TTS 时长，不能太长）
        narration_clamped = _clamp(narration, NARRATION_MAX)

        shots.append({
            "headline": _clamp(headline, HEADLINE_MAX),
            "display": display,          # 不截断（用于画面展示）
            "narration": narration_clamped,  # V0.8.3: 硬截断保护
            "emphasisTerms": emp,
            "tone": tone,
            "metrics": metrics,          # V0.3.6-quality-p0
        })

    # V0.8.3: coverTitle 偏好"概要式"，避免被第一条要点绑死
    raw_cover = (raw.get("coverTitle") or raw.get("title") or "").strip()
    raw_cover_norm = re.sub(r"\s+", "", raw_cover)
    cover_default, _ = split_headline_and_detail(lead)
    cover_default_norm = re.sub(r"\s+", "", cover_default or "")
    if raw_cover:
        # 拒绝"完全等于第一条要点"的标题（典型 LLM 错误）
        if first_headline_norm and raw_cover_norm == first_headline_norm:
            cover_title = COVER_TITLE_FALLBACK
        else:
            cover_title = raw_cover
    elif cover_default_norm and first_headline_norm and cover_default_norm == first_headline_norm:
        cover_title = COVER_TITLE_FALLBACK
    elif cover_default:
        cover_title = cover_default
    else:
        cover_title = COVER_TITLE_FALLBACK
    # V0.8.3: opening / closing 同样做硬截断
    opening_raw = (raw.get("opening") or "").strip() or "今天AI圈的重点，正在从能力走向落地。"
    closing_raw = (raw.get("closing") or "").strip() or "以上就是今天的要点，感谢观看。"
    return {
        "coverTitle": _clamp(cover_title, 18),
        "opening": _clamp(opening_raw, OPENING_MAX),
        "shots": shots,
        "closing": _clamp(closing_raw, CLOSING_MAX),
    }


def _fallback_plan(
    raw_content: str,
    max_items: int,
    test_case_id: str,
    target_duration_sec: float | None = None,  # V0.8.3
) -> dict[str, Any]:
    """确定性兜底：用 content_structurer 拆分，标题/详情切分。

    V0.8.3: narration / opening / closing 也走硬截断；coverTitle 不再直接取第一条要点。
    """
    structured = structure_content(raw_content, test_case_id or "ai_insight_summary")
    lead = structured.get("lead", "")
    cover_headline, _ = split_headline_and_detail(lead)
    items = structured.get("items", [])[:max_items]

    # V0.8.3: 如果 lead 解析出的 cover_headline 与第一条 item 标题相同，强制用兜底
    first_item_title_norm = re.sub(r"\s+", "", (items[0].get("title", "") if items else "").strip())
    cover_headline_norm = re.sub(r"\s+", "", (cover_headline or ""))
    if cover_headline_norm and first_item_title_norm and cover_headline_norm == first_item_title_norm:
        cover_title = COVER_TITLE_FALLBACK
    elif cover_headline:
        cover_title = cover_headline
    else:
        cover_title = COVER_TITLE_FALLBACK

    shots = []
    for item in items:
        s = _shot_from_item(item)
        # V0.8.3: narration 硬截断保护
        s["narration"] = _clamp(s.get("narration", ""), NARRATION_MAX)
        shots.append(s)

    return {
        "coverTitle": _clamp(cover_title, 18),
        "opening": _clamp(lead or "今天AI圈的重点，正在从能力走向落地。", OPENING_MAX),
        "shots": shots,
        "closing": _clamp("以上就是今天的要点，感谢观看。", CLOSING_MAX),
        "source": "fallback",
    }
