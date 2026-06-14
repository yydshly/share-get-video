"""
Video Quality Assessor - 视频质量自动评估

不只生成视频，还要"判定质量"。本模块对一次生成的产物做**确定性**质量检查，
覆盖用户关心的四个维度：

1. 信息准确 (information_accuracy)
   - 源报告条目覆盖率、关键点无重复
   - 关键数字（如 0.84 / 39% / 75.1%）是否在旁白/字幕中保留（信息无损）
2. 音画对应 (audio_visual_sync)
   - 字幕条数 == 旁白段数
   - 字幕时间轴总长 vs 实际音频时长是否同步（不漂移）
   - 画面规划时长 vs 音频时长是否匹配（避免大量静态填充）
3. 显示合理 (visual_rendering)
   - 渲染器是否报告文字溢出/截断
   - 帧数是否合理（封面 + 关键点）
4. 视频友好 (viewer_friendly)
   - 时长是否在短视频合理区间
   - 字幕是否已烧入、是否有封面

主观维度（画面美感、声音自然度）不在此自动判定，标记为 needs_human，
留给人工评分 / 视觉模型，不伪造分数。

每项检查返回 pass / warn / fail；维度分 = 平均(pass=5, warn=3, fail=1)；
overall = 各维度均分。
"""

import re
from dataclasses import dataclass, field
from typing import Any


PASS = "pass"
WARN = "warn"
FAIL = "fail"

_STATUS_SCORE = {PASS: 5.0, WARN: 3.0, FAIL: 1.0}

# 提取关键数字：百分比 / 小数 / 区间，如 39%  0.84  57-77%  75.1%
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?(?:[-~]\d+(?:\.\d+)?%?)?")


@dataclass
class QualityCheck:
    check_id: str
    dimension: str
    status: str           # pass / warn / fail
    message: str
    value: Any = None
    expected: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkId": self.check_id,
            "dimension": self.dimension,
            "status": self.status,
            "message": self.message,
            "value": self.value,
            "expected": self.expected,
        }


@dataclass
class QualityReport:
    checks: list[QualityCheck] = field(default_factory=list)
    needs_human: list[str] = field(default_factory=list)

    def dimension_scores(self) -> dict[str, float]:
        by_dim: dict[str, list[float]] = {}
        for c in self.checks:
            by_dim.setdefault(c.dimension, []).append(_STATUS_SCORE[c.status])
        return {d: round(sum(v) / len(v), 2) for d, v in by_dim.items()}

    def overall_score(self) -> float:
        dims = self.dimension_scores()
        if not dims:
            return 0.0
        return round(sum(dims.values()) / len(dims), 2)

    def counts(self) -> dict[str, int]:
        out = {PASS: 0, WARN: 0, FAIL: 0}
        for c in self.checks:
            out[c.status] += 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "overallScore": self.overall_score(),
            "dimensionScores": self.dimension_scores(),
            "counts": self.counts(),
            "checks": [c.to_dict() for c in self.checks],
            "needsHuman": self.needs_human,
        }


def _extract_numbers(text: str) -> set[str]:
    """从文本提取关键数字 token（归一化去掉空白）。"""
    return {m.group(0) for m in _NUMBER_RE.finditer(text or "")}


def assess_quality(
    source_content: str,
    structured: dict[str, Any],
    key_points: dict[str, Any],
    voiceover: dict[str, Any],
    *,
    audio_duration_sec: float,
    subtitle_count: int,
    subtitle_burned: bool,
    visual_duration_sec: float,
    has_cover: bool,
    frame_count: int,
    warnings: list[str] | None = None,
    target_duration_sec: float = 45.0,
) -> QualityReport:
    """对一次生成结果做确定性质量评估，返回 QualityReport。"""
    warnings = warnings or []
    checks: list[QualityCheck] = []

    kps = key_points.get("keyPoints") or key_points.get("key_points") or []
    total_items = int(structured.get("totalItems", 0))
    segments = voiceover.get("segments", [])
    voiceover_text = voiceover.get("voiceoverText", "")

    # ── 维度1：信息准确 ─────────────────────────────
    dim = "information_accuracy"

    # 覆盖率（关键点 / 源条目）
    covered = len(kps)
    if total_items == 0:
        checks.append(QualityCheck("coverage", dim, FAIL,
            "未解析到任何源条目", value=0, expected=">0"))
    else:
        ratio = covered / total_items
        status = PASS if ratio >= 1.0 else (WARN if ratio >= 0.5 else FAIL)
        checks.append(QualityCheck("coverage", dim, status,
            f"覆盖 {covered}/{total_items} 条源信息" + ("（按 keyPointCount 截断）" if status != PASS else ""),
            value=covered, expected=total_items))

    # 关键点无重复
    titles = [k.get("title", "") for k in kps]
    dup = len(titles) != len(set(titles))
    checks.append(QualityCheck("no_duplication", dim, FAIL if dup else PASS,
        "关键点存在重复标题" if dup else "关键点无重复",
        value=len(titles), expected=len(set(titles))))

    # 关键数字保留（覆盖条目里的数字是否进入旁白/字幕文本）
    source_numbers: set[str] = set()
    for k in kps:
        source_numbers |= _extract_numbers(k.get("title", ""))
        source_numbers |= _extract_numbers(k.get("source", ""))
    spoken_numbers = _extract_numbers(voiceover_text)
    missing = sorted(source_numbers - spoken_numbers)
    if not source_numbers:
        pass  # 无关键数字，不检查
    elif not missing:
        checks.append(QualityCheck("key_numbers_preserved", dim, PASS,
            f"关键数字全部保留 ({len(source_numbers)} 个)", value=[], expected=sorted(source_numbers)))
    else:
        ratio = 1 - len(missing) / len(source_numbers)
        status = WARN if ratio >= 0.5 else FAIL
        checks.append(QualityCheck("key_numbers_preserved", dim, status,
            f"旁白/字幕丢失关键数字: {missing}", value=missing, expected=sorted(source_numbers)))

    # ── 维度2：音画对应 ─────────────────────────────
    dim = "audio_visual_sync"

    # 字幕覆盖：每个旁白段至少有一条字幕（分块后字幕条数 >= 段数）
    seg_count = len(segments)
    if seg_count == 0:
        checks.append(QualityCheck("subtitle_segment_match", dim, FAIL,
            "无旁白段", value=subtitle_count, expected=0))
    else:
        ok = subtitle_count >= seg_count
        checks.append(QualityCheck("subtitle_segment_match", dim, PASS if ok else WARN,
            f"字幕条数={subtitle_count}，旁白段数={seg_count}" + ("" if ok else "（少于段数，可能漏字幕）"),
            value=subtitle_count, expected=f">={seg_count}"))

    # 字幕时间轴总长 vs 实际音频时长（漂移）
    if segments and audio_duration_sec > 0:
        last = segments[-1]
        sub_timeline_end = float(last.get("startSec", 0)) + float(last.get("durationSec", 0))
        drift = abs(sub_timeline_end - audio_duration_sec)
        drift_ratio = drift / audio_duration_sec
        status = PASS if drift_ratio <= 0.15 else (WARN if drift_ratio <= 0.4 else FAIL)
        checks.append(QualityCheck("subtitle_audio_drift", dim, status,
            f"字幕轴终点 {sub_timeline_end:.1f}s vs 音频 {audio_duration_sec:.1f}s，漂移 {drift:.1f}s",
            value=round(sub_timeline_end, 1), expected=round(audio_duration_sec, 1)))

    # 画面规划时长 vs 音频时长
    if visual_duration_sec > 0 and audio_duration_sec > 0:
        r = visual_duration_sec / audio_duration_sec
        status = PASS if 0.7 <= r <= 1.4 else WARN
        checks.append(QualityCheck("visual_audio_duration_match", dim, status,
            f"画面规划 {visual_duration_sec:.1f}s vs 音频 {audio_duration_sec:.1f}s (比 {r:.2f})",
            value=round(visual_duration_sec, 1), expected=round(audio_duration_sec, 1)))

    # ── 维度3：显示合理 ─────────────────────────────
    dim = "visual_rendering"

    overflow = [w for w in warnings if any(t in str(w).lower() for t in ("overflow", "truncat", "溢出", "截断"))]
    checks.append(QualityCheck("no_text_overflow", dim, WARN if overflow else PASS,
        f"检测到 {len(overflow)} 条溢出/截断告警" if overflow else "无文字溢出告警",
        value=overflow, expected=[]))

    # 帧数检查只适用于"帧合成类"路线；直出视频类路线（如 Remotion）不报帧数，跳过
    if frame_count > 0:
        expected_min_frames = max(1, covered) + (1 if has_cover else 0)
        checks.append(QualityCheck("frame_count_reasonable", dim,
            PASS if frame_count >= expected_min_frames else WARN,
            f"帧数 {frame_count}（期望 >= {expected_min_frames}）",
            value=frame_count, expected=expected_min_frames))

    # ── 维度4：视频友好 ─────────────────────────────
    dim = "viewer_friendly"

    if audio_duration_sec <= 0:
        checks.append(QualityCheck("duration_in_range", dim, FAIL,
            "无音频时长", value=0, expected="15-90s"))
    else:
        status = PASS if 15 <= audio_duration_sec <= 90 else WARN
        checks.append(QualityCheck("duration_in_range", dim, status,
            f"成片时长 {audio_duration_sec:.1f}s（短视频建议 15-90s）",
            value=round(audio_duration_sec, 1), expected="15-90s"))

    sub_ok = subtitle_burned and subtitle_count > 0
    checks.append(QualityCheck("subtitle_present", dim, PASS if sub_ok else WARN,
        "字幕已烧入" if sub_ok else "字幕缺失或未烧入",
        value={"burned": subtitle_burned, "count": subtitle_count}, expected={"burned": True, "count": ">0"}))

    checks.append(QualityCheck("has_cover", dim, PASS if has_cover else WARN,
        "有封面帧" if has_cover else "无封面帧", value=has_cover, expected=True))

    return QualityReport(
        checks=checks,
        needs_human=["visual_aesthetics", "voice_naturalness", "overall_shareability"],
    )
