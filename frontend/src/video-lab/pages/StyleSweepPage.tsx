// Style Sweep - 样式对比台（V0.8.0 加入人工质量排查）
// Path: /video-lab/style-sweep
// 选一条技术路线 → 用同一内容把它的每个预置样式各出一片 → 并排看"同技术不同样式"的效果差异。
// V0.8.0 起：每个结果卡片支持人工问题标签 + 备注 + 排查信息导出。
// 注意：人工标注当前只在前端 state，不持久化；刷新页面后丢失。

import { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const resolveUrl = (u: string) =>
  u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u;

const DEFAULT_CONTENT = `今日AI前沿三条要点。
第一，ProReviewer论文评审系统发布，在五个质量维度上超越传统自动评审方法，平均提升39%，已在两千篇论文上验证。
第二，主流购物AI助手实测落后，在真实电商场景下主流模型任务通过率仅为57-77%，暴露多轮推理与工具调用短板。
第三，开源多模态模型再下一城，新模型以八十亿参数在多项基准上接近闭源旗舰，推理成本下降约六成。`;

// 三条技术路线（含各自样式数，用于成本提示）
const ROUTES = [
  { id: "local_frame_compose", name: "Pillow 静态卡", styleCount: 5 },
  { id: "template_programmatic_render", name: "Remotion 动效", styleCount: 7 },
  { id: "ai_asset_then_compose", name: "AI 素材 + 合成", styleCount: 5 },
];

const GUIDE_STEPS = [
  { n: 1, t: "选技术路线", d: "选一条技术，对比它内部的不同样式" },
  { n: 2, t: "粘贴内容", d: "同一份内容会用每个样式各出一支片" },
  { n: 3, t: "开始对比", d: "勾选确认后点击——逐样式出完整短视频" },
  { n: 4, t: "并排看差异", d: "亲眼对比同技术下哪种样式更适合这份内容" },
  { n: 5, t: "人工标注", d: "逐个播放后标记问题 / 备注 / 导出排查报告" },
];

// 人工问题标签（V0.8.0 接入）
// "可用" 与其他问题互斥：选「可用」会清空其他；选其他会自动移除「可用」。
const ISSUE_OPTIONS = [
  { id: "ok", label: "可用" },
  { id: "missing_visual", label: "缺图片/素材" },
  { id: "audio_visual_mismatch", label: "音画不对应" },
  { id: "subtitle_mismatch", label: "字幕不同步" },
  { id: "empty_frame", label: "画面太空" },
  { id: "text_too_small", label: "文字太小" },
  { id: "text_overflow", label: "文字溢出/重叠" },
  { id: "rhythm_bad", label: "节奏不对" },
  { id: "content_missing", label: "内容遗漏" },
  { id: "style_too_similar", label: "样式差异小" },
  { id: "style_not_suitable", label: "风格不适合" },
  // V0.8.4: explicit "render failed" tag — surfaces in stats so a failed
  // style can't hide inside the "可用=0, 各类问题=0" trap when user only
  // typed a note. Mutually exclusive with "ok" via the existing toggle logic.
  { id: "render_failed", label: "生成失败" },
];

interface Quality { overallScore?: number }

// V0.8.2: extended with manifestUrl / audioDurationSec / subtitleCount /
// warnings / steps / params / logs so the inspection JSON / Markdown report
// can carry forward the cheap diagnostic surface (see docs/OPEN_ISSUES_VIDEO_LAB.md).
interface StyleResult {
  styleId: string;
  styleName: string;
  description: string;
  tags: string[];
  result: {
    status: string;
    finalVideoUrl: string;
    coverUrl: string;
    audioUrl?: string;
    srtUrl?: string;
    quality?: Quality;
    failedReason?: string;
    manifestUrl?: string;
    audioDurationSec?: number;
    subtitleCount?: number;
    warnings?: string[];
    steps?: { name: string; status: string; output?: string }[];
    params?: Record<string, unknown>;
    logs?: string[];
  };
}

interface SweepResponse {
  routeId: string;
  routeName: string;
  styleCount: number;
  succeededCount: number;
  results: StyleResult[];
}

// 人工标注：key = styleId
interface IssueMark {
  issues: string[];
  note: string;
}

// 复制反馈
type CopyState = "" | "copied" | "failed";

// V0.8.4: 备注关键词 → 建议问题标签。仅做提示，不自动写入用户标注。
// 返回 id 数组（与 ISSUE_OPTIONS 中的 id 对齐），不含 "ok" / "render_failed"。
function inferIssueHintsFromNote(note: string, status?: string): string[] {
  const text = note || "";
  const hints: string[] = [];

  // status === failed 时强烈建议"生成失败"，同时备注里包含"失败"也建议
  if (status === "failed" || text.includes("失败")) hints.push("render_failed");
  if (text.includes("黑屏") || text.includes("缺少") || text.includes("缺图") || text.includes("图片有问题") || text.includes("没出图")) hints.push("missing_visual");
  // "音画不对应" 同时出现 "音画"/"音频"+"图片"/"画面"
  if (text.includes("音画") || (text.includes("音频") && (text.includes("图片") || text.includes("画面")))) hints.push("audio_visual_mismatch");
  if (text.includes("字幕") && (text.includes("截断") || text.includes("缺失") || text.includes("不同步") || text.includes("丢失"))) hints.push("subtitle_mismatch");
  if (text.includes("最后一句") || text.includes("内容遗漏") || text.includes("内容缺失")) hints.push("content_missing");
  if ((text.includes("文字") || text.includes("文本")) && (text.includes("重叠") || text.includes("溢出"))) hints.push("text_overflow");

  return [...new Set(hints)];
}

// 把 id 列表翻译成人类可读 label（用于提示文案）
function hintsToLabels(ids: string[]): string[] {
  return ids
    .map((id) => ISSUE_OPTIONS.find((o) => o.id === id)?.label ?? id)
    .filter(Boolean);
}

export default function StyleSweepPage() {
  const [routeId, setRouteId] = useState(ROUTES[0].id);
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [duration, setDuration] = useState(45);
  const [keyPointCount, setKeyPointCount] = useState(3);
  const [useLlmPlan, setUseLlmPlan] = useState(true);
  const [confirmed, setConfirmed] = useState(false);
  const [running, setRunning] = useState(false);
  const [data, setData] = useState<SweepResponse | null>(null);
  const [error, setError] = useState("");

  // V0.8.0：人工标注 state（仅前端，刷新即丢）
  const [issueMarks, setIssueMarks] = useState<Record<string, IssueMark>>({});
  // 展开排查信息的卡片集合
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  // 复制按钮反馈
  const [reportCopyState, setReportCopyState] = useState<CopyState>("");
  // 每个卡片"复制 JSON" 反馈
  const [jsonCopyState, setJsonCopyState] = useState<Record<string, CopyState>>({});

  const activeRoute = ROUTES.find((r) => r.id === routeId)!;

  const runSweep = async () => {
    setRunning(true);
    setError("");
    setData(null);
    // 重置标注（新一轮排查从零开始）
    setIssueMarks({});
    setExpanded({});
    setReportCopyState("");
    setJsonCopyState({});
    try {
      const resp = await fetch(`${API_BASE}/style-sweep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          routeId,
          params: { targetDuration: duration, aspectRatio: "9:16", keyPointCount, useLlmPlan },
        }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      setData(await resp.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  // 切换问题标签
  // "可用" 与其他互斥；其他问题之间可多选；再次点击取消。
  const toggleIssue = (styleId: string, issueId: string) => {
    setIssueMarks((prev) => {
      const current = prev[styleId] ?? { issues: [], note: "" };
      let nextIssues: string[];
      if (issueId === "ok") {
        // 点 "可用"：仅保留 "ok"
        nextIssues = current.issues.includes("ok") ? [] : ["ok"];
      } else {
        // 点其他：先去掉 "ok"，再 toggle 该项
        const withoutOk = current.issues.filter((i) => i !== "ok");
        nextIssues = withoutOk.includes(issueId)
          ? withoutOk.filter((i) => i !== issueId)
          : [...withoutOk, issueId];
      }
      return { ...prev, [styleId]: { ...current, issues: nextIssues } };
    });
  };

  // 更新备注
  const updateNote = (styleId: string, note: string) => {
    setIssueMarks((prev) => {
      const current = prev[styleId] ?? { issues: [], note: "" };
      return { ...prev, [styleId]: { ...current, note } };
    });
  };

  // 切换排查信息展开
  const toggleExpanded = (styleId: string) => {
    setExpanded((prev) => ({ ...prev, [styleId]: !prev[styleId] }));
  };

  // 计算单个样式的"排查 JSON"对象
  // V0.8.2: enrich with manifestUrl / audioDurationSec / subtitleCount /
  // warnings / steps / params / logsTail (last 30 lines of logs only) so
  // the inspection report can carry forward the cheap diagnostic surface.
  // V0.8.4: also include suggestedIssues (from note keyword hints) +
  // markingWarning ("备注中包含问题描述，但人工问题标签为空" / "样式生成失败，但未标记生成失败").
  const buildCheckJson = (s: StyleResult) => {
    const r = s.result;
    const mark = issueMarks[s.styleId] ?? { issues: [], note: "" };
    const fullLogs = Array.isArray(r.logs) ? r.logs : [];
    const logsTail = fullLogs.slice(-30);
    const suggestedIssues = inferIssueHintsFromNote(mark.note, r.status);
    let markingWarning = "";
    if (mark.note.trim() && mark.issues.length === 0) {
      markingWarning = "备注中包含问题描述，但人工问题标签为空";
    } else if (r.status === "failed" && !mark.issues.includes("render_failed")) {
      markingWarning = "样式生成失败，但未标记生成失败";
    }
    return {
      routeId: data?.routeId,
      routeName: data?.routeName,
      styleId: s.styleId,
      styleName: s.styleName,
      description: s.description,
      status: r.status,
      finalVideoUrl: r.finalVideoUrl,
      coverUrl: r.coverUrl,
      audioUrl: r.audioUrl,
      srtUrl: r.srtUrl,
      manifestUrl: r.manifestUrl || "",
      audioDurationSec: r.audioDurationSec ?? 0,
      subtitleCount: r.subtitleCount ?? 0,
      warnings: Array.isArray(r.warnings) ? r.warnings : [],
      steps: Array.isArray(r.steps) ? r.steps : [],
      params: r.params ?? {
        targetDuration: duration,
        keyPointCount,
        useLlmPlan,
      },
      logsTail,
      quality: { overallScore: r.quality?.overallScore },
      manualIssues: mark.issues,
      manualNote: mark.note,
      suggestedIssues,
      markingWarning,
    };
  };

  // 复制单个样式的排查 JSON
  const copyJson = async (s: StyleResult) => {
    const payload = JSON.stringify(buildCheckJson(s), null, 2);
    try {
      await navigator.clipboard.writeText(payload);
      setJsonCopyState((prev) => ({ ...prev, [s.styleId]: "copied" }));
      setTimeout(
        () => setJsonCopyState((prev) => ({ ...prev, [s.styleId]: "" })),
        1500,
      );
    } catch {
      setJsonCopyState((prev) => ({ ...prev, [s.styleId]: "failed" }));
      setTimeout(
        () => setJsonCopyState((prev) => ({ ...prev, [s.styleId]: "" })),
        2000,
      );
    }
  };

  // 统计
  const stats = useMemo(() => {
    const init: Record<string, number> = {};
    ISSUE_OPTIONS.forEach((opt) => (init[opt.id] = 0));
    Object.values(issueMarks).forEach((m) => {
      m.issues.forEach((id) => {
        if (id in init) init[id] += 1;
      });
    });
    return init;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [issueMarks]);

  const hasAnyMark = Object.keys(issueMarks).length > 0;

  // V0.8.4: 标注完整性检查。统计 3 类问题：
  // 1. 有备注但 issues 为空（用户写了"字幕截断"等但没勾任何标签）
  // 2. status === failed 但没勾 "生成失败"
  // 3. 备注关键词推断出建议标签但用户一个都没勾
  const integrityStats = useMemo(() => {
    let noteButNoTag = 0;
    let failedButNotMarked = 0;
    let hasSuggested = 0;
    if (data) {
      for (const s of data.results) {
        const r = s.result;
        const mark = issueMarks[s.styleId] ?? { issues: [], note: "" };
        const suggested = inferIssueHintsFromNote(mark.note, r.status);
        const noteNonEmpty = mark.note.trim().length > 0;
        if (noteNonEmpty && mark.issues.length === 0) noteButNoTag += 1;
        if (r.status === "failed" && !mark.issues.includes("render_failed")) failedButNotMarked += 1;
        if (suggested.length > 0 && mark.issues.length === 0) hasSuggested += 1;
      }
    }
    return { noteButNoTag, failedButNotMarked, hasSuggested };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [issueMarks, data]);

  // 复制本轮 Markdown 排查报告
  // V0.8.2: enrich per-style section with manifestUrl / audioDurationSec /
  // subtitleCount / warnings / steps / params; add "如何继续排查" section.
  const copyReport = async () => {
    if (!data) return;
    const lines: string[] = [];
    lines.push("# Style Sweep 成片排查报告");
    lines.push("");
    lines.push(`路线：${data.routeName}`);
    lines.push(`routeId: ${data.routeId}`);
    lines.push("");
    lines.push("参数：");
    lines.push(`- targetDuration: ${duration}`);
    lines.push(`- keyPointCount: ${keyPointCount}`);
    lines.push(`- useLlmPlan: ${useLlmPlan}`);
    lines.push("");
    lines.push("## 如何继续排查");
    lines.push("");
    lines.push("1. 先打开 manifestUrl，检查 planDebug.coverTitle / opening / closing / budgetDebug 是否符合内容。");
    lines.push("2. 再打开对应实验目录下 remotion_props.json，检查 contentDebug.title / keyPointTitles / metricsByKeyPoint / timelineDebug。");
    lines.push("3. 如果标题不对，优先查 plan_shots / coverTitle。");
    lines.push("4. 如果数字图缺失，优先查 metricsByKeyPoint 是否为空或单位异常，并检查下方「样式参数说明」。");
    lines.push("5. 如果音画不同步，优先查 timelineDebug 与 voiceoverSegments。");
    lines.push("6. 如果数字图或横线没显示，先检查 params.showDataViz 和 params.metricAnimation：");
    lines.push("   - showDataViz=false：该样式本来不显示数据图");
    lines.push("   - metricAnimation=countup_number：只显示数字，不显示进度条");
    lines.push("   - metricAnimation=countup_bar：显示数字 + 进度条");
    lines.push("7. 如果实际音频时长明显超过 targetDuration，检查 manifest.planDebug.budgetDebug 是否标记 overBudget=true。");
    lines.push("");
    lines.push("## 结果统计");
    lines.push("");
    lines.push(`- 总样式数：${data.styleCount}`);
    lines.push(`- 成功数：${data.succeededCount}`);
    ISSUE_OPTIONS.forEach((opt) => {
      lines.push(`- ${opt.label}：${stats[opt.id]}`);
    });
    lines.push("");
    // V0.8.4: 标注完整性检查（先于样式明细，方便用户一眼看到）
    lines.push("## 标注完整性检查");
    lines.push("");
    lines.push(`- 有备注但未勾标签：${integrityStats.noteButNoTag}`);
    lines.push(`- 失败但未标生成失败：${integrityStats.failedButNotMarked}`);
    lines.push(`- 有建议标签待确认：${integrityStats.hasSuggested}`);
    const needsAttention = data.results
      .map((s) => {
        const r = s.result;
        const mark = issueMarks[s.styleId] ?? { issues: [], note: "" };
        const suggested = inferIssueHintsFromNote(mark.note, r.status);
        const noteNonEmpty = mark.note.trim().length > 0;
        const reasonParts: string[] = [];
        if (r.status === "failed" && !mark.issues.includes("render_failed")) {
          reasonParts.push("status=failed，建议标签：生成失败");
        }
        if (noteNonEmpty && mark.issues.length === 0) {
          const labelList = hintsToLabels(suggested.filter((id) => id !== "render_failed" || r.status === "failed"));
          reasonParts.push(
            labelList.length > 0
              ? `备注包含问题关键词，建议标签：${labelList.join("、")}`
              : "备注包含问题描述",
          );
        } else if (suggested.length > 0) {
          // 即使勾了标签，如果建议标签里有未被勾的，也提示
          const unchosen = suggested.filter((id) => !mark.issues.includes(id));
          if (unchosen.length > 0) {
            reasonParts.push(`仍有未勾建议标签：${hintsToLabels(unchosen).join("、")}`);
          }
        }
        return reasonParts.length > 0 ? { name: s.styleName, reasons: reasonParts } : null;
      })
      .filter(Boolean) as { name: string; reasons: string[] }[];
    if (needsAttention.length > 0) {
      lines.push("");
      lines.push("### 待补充标注");
      needsAttention.forEach((n) => {
        lines.push(`- ${n.name}：${n.reasons.join("；")}`);
      });
    }
    lines.push("");
    lines.push("## 样式明细");
    data.results.forEach((s) => {
      const r = s.result;
      const mark = issueMarks[s.styleId] ?? { issues: [], note: "" };
      const q = r.quality?.overallScore;
      const issueLabels = mark.issues
        .map((id) => ISSUE_OPTIONS.find((o) => o.id === id)?.label ?? id)
        .join("、") || "（无）";
      const warnings = Array.isArray(r.warnings) && r.warnings.length > 0
        ? r.warnings.join("； ")
        : "（无）";
      const steps = Array.isArray(r.steps) && r.steps.length > 0
        ? r.steps.map((st) => `${st.name}[${st.status}]`).join(" → ")
        : "（无）";
      const paramsStr = r.params && Object.keys(r.params).length > 0
        ? Object.entries(r.params).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join("; ")
        : "（无）";
      lines.push("");
      lines.push(`### ${s.styleName}`);
      lines.push("");
      lines.push(`- styleId: ${s.styleId}`);
      lines.push(`- status: ${r.status}`);
      lines.push(`- quality: ${q !== undefined ? `${q}/5` : "无"}`);
      lines.push(`- finalVideoUrl: ${r.finalVideoUrl || "无"}`);
      lines.push(`- audioUrl: ${r.audioUrl || "无"}`);
      lines.push(`- srtUrl: ${r.srtUrl || "无"}`);
      lines.push(`- manifestUrl: ${r.manifestUrl || "无"}`);
      lines.push(`- audioDurationSec: ${r.audioDurationSec ?? 0}`);
      lines.push(`- subtitleCount: ${r.subtitleCount ?? 0}`);
      lines.push(`- warnings: ${warnings}`);
      lines.push(`- steps: ${steps}`);
      lines.push(`- params: ${paramsStr}`);
      lines.push(`- 人工问题：${issueLabels}`);
      lines.push(`- 人工备注：${mark.note || "（无）"}`);
      // V0.8.3: failedReason + logsTail (last 10 lines only) for failed renders
      lines.push(`- failedReason: ${r.failedReason || "无"}`);
      const fullLogs = Array.isArray(r.logs) ? r.logs : [];
      const lastLogs = fullLogs.slice(-10);
      lines.push(`- logsTail: ${lastLogs.length > 0 ? lastLogs.join(" | ") : "（无）"}`);
      // V0.8.4: 备注关键词推断的建议标签 + 标注警告
      const suggested = inferIssueHintsFromNote(mark.note, r.status);
      let markingWarning = "";
      if (mark.note.trim() && mark.issues.length === 0) {
        markingWarning = "备注中包含问题描述，但人工问题标签为空";
      } else if (r.status === "failed" && !mark.issues.includes("render_failed")) {
        markingWarning = "样式生成失败，但未标记生成失败";
      }
      const suggestedLabels = hintsToLabels(suggested).join("、") || "（无）";
      lines.push(`- suggestedIssues: ${suggestedLabels}`);
      lines.push(`- markingWarning: ${markingWarning || "（无）"}`);
    });
    lines.push("");
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setReportCopyState("copied");
      setTimeout(() => setReportCopyState(""), 1500);
    } catch {
      setReportCopyState("failed");
      setTimeout(() => setReportCopyState(""), 2000);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ fontSize: "1.6rem", fontWeight: 700, marginBottom: "0.25rem" }}>🎨 样式对比台</h1>
      <p style={{ color: "#64748b", marginBottom: "1.5rem" }}>
        选一条技术路线，用同一份内容把它的每个预置样式各出一支片，并排看「同技术、不同样式」的效果差异。
      </p>

      {/* 操作指引 */}
      <div style={{ background: "#fdf4ff", border: "1px solid #f0abfc", borderRadius: 12, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <div style={{ fontWeight: 600, marginBottom: "0.75rem", color: "#a21caf" }}>操作指引</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "0.75rem" }}>
          {GUIDE_STEPS.map((s) => (
            <div key={s.n} style={{ display: "flex", gap: "0.6rem", alignItems: "flex-start" }}>
              <div style={{ flexShrink: 0, width: 26, height: 26, borderRadius: "50%", background: "#c026d3", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem", fontWeight: 700 }}>{s.n}</div>
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>{s.t}</div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: 1.4 }}>{s.d}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ① 选路线 */}
      <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem" }}>① 技术路线</label>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        {ROUTES.map((r) => (
          <button key={r.id} onClick={() => setRouteId(r.id)}
            style={{
              padding: "0.5rem 1rem", borderRadius: 8, fontSize: "0.85rem", cursor: "pointer",
              border: routeId === r.id ? "2px solid #c026d3" : "1px solid #cbd5e1",
              background: routeId === r.id ? "#fdf4ff" : "white", fontWeight: routeId === r.id ? 600 : 400,
            }}>
            {r.name} <span style={{ color: "#94a3b8" }}>· {r.styleCount} 样式</span>
          </button>
        ))}
      </div>

      {/* ② 内容 */}
      <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem" }}>② 内容原文</label>
      <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={6}
        style={{ width: "100%", padding: "0.75rem", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: "0.85rem", lineHeight: 1.6, fontFamily: "inherit", boxSizing: "border-box", marginBottom: "1rem" }} />

      {/* ③ 参数 */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1.5rem", alignItems: "center", marginBottom: "1rem", fontSize: "0.85rem" }}>
        <label>③ 时长(秒)：<input type="number" value={duration} min={15} max={90} onChange={(e) => setDuration(Number(e.target.value))} style={{ width: 64, padding: "0.3rem", border: "1px solid #cbd5e1", borderRadius: 6 }} /></label>
        <label>要点数：<input type="number" value={keyPointCount} min={1} max={6} onChange={(e) => setKeyPointCount(Number(e.target.value))} style={{ width: 56, padding: "0.3rem", border: "1px solid #cbd5e1", borderRadius: 6 }} /></label>
        <label><input type="checkbox" checked={useLlmPlan} onChange={(e) => setUseLlmPlan(e.target.checked)} /> 用 LLM 规划</label>
      </div>

      {/* 成本提示 + 确认 */}
      <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 8, padding: "0.75rem 1rem", marginBottom: "0.75rem", fontSize: "0.8rem", color: "#92400e" }}>
        ⚠️ 将为「{activeRoute.name}」的 <strong>{activeRoute.styleCount}</strong> 个样式各跑一遍完整出片（含 TTS{routeId === "ai_asset_then_compose" ? "、AI 生图" : ""}、合成），约 <strong>{activeRoute.styleCount * 2}-{activeRoute.styleCount * 3} 分钟</strong> 并消耗 API 额度。
      </div>
      <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
        <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} /> 我已了解耗时与额度消耗
      </label>

      <button onClick={runSweep} disabled={running || !confirmed || !content.trim()}
        style={{
          padding: "0.7rem 1.5rem", borderRadius: 8, border: "none", fontSize: "0.95rem", fontWeight: 600,
          background: running || !confirmed || !content.trim() ? "#cbd5e1" : "#c026d3", color: "white",
          cursor: running || !confirmed || !content.trim() ? "not-allowed" : "pointer",
        }}>
        {running ? "⏳ 出片中…（请耐心等待，勿关闭）" : "🎨 开始对比样式"}
      </button>

      {error && <div style={{ marginTop: "1rem", color: "#ef4444", fontSize: "0.85rem" }}>出错：{error}</div>}
      {running && (
        <div style={{ marginTop: "1.5rem", color: "#64748b", fontSize: "0.85rem" }}>
          正在逐样式出片，完成后一次性并排展示。
        </div>
      )}

      {/* 结果：各样式并排 */}
      {data && (
        <div style={{ marginTop: "2rem" }}>
          <div style={{ marginBottom: "1rem", fontSize: "0.9rem", color: "#475569" }}>
            「{data.routeName}」共 {data.styleCount} 个样式，成功 {data.succeededCount} 个 — 同一内容，下面是各样式的成片：
          </div>

          {/* 任务六：关键提示 banner */}
          <div style={{
            background: "#fef3c7", border: "1px solid #f59e0b", borderRadius: 8,
            padding: "0.85rem 1rem", marginBottom: "1rem", fontSize: "0.85rem", color: "#78350f",
          }}>
            ⚠️ <strong>结构评分只代表程序化结构质量，不代表人工观看质量。</strong>
            请逐个播放并标记缺图、音画不同步、字幕错位、文本溢出、样式差异小等问题。
          </div>

          {/* V0.8.2: 诊断信息暴露提示 */}
          <div style={{
            background: "#eff6ff", border: "1px solid #93c5fd", borderRadius: 8,
            padding: "0.85rem 1rem", marginBottom: "1rem", fontSize: "0.85rem", color: "#1e3a8a",
          }}>
            🔍 定位标题错误、数字图缺失、音画不同步时，请复制排查 JSON 或 Markdown 报告，并检查 <code>manifestUrl</code> / <code>remotion_props.json</code> 中的 <strong>planDebug</strong>、<strong>contentDebug</strong>、<strong>timelineDebug</strong>。
            <div style={{ marginTop: "0.4rem" }}>
              💡 <strong>数字图缺失不一定是生成失败</strong>，也可能是当前样式参数关闭了数据可视化（<code>showDataViz=false</code> 或 <code>metricAnimation=countup_number</code>）。
            </div>
          </div>

          {/* 任务四：标注统计 + 任务五：复制报告按钮 */}
          <div style={{
            background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10,
            padding: "1rem", marginBottom: "1.25rem", display: "flex",
            justifyContent: "space-between", gap: "1rem", flexWrap: "wrap", alignItems: "flex-start",
          }}>
            <div style={{ flex: 1, minWidth: 260 }}>
              <div style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.5rem", color: "#334155" }}>
                人工标注统计：
              </div>
              {!hasAnyMark ? (
                <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                  尚未标注，请逐个播放视频后标记问题。
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "0.35rem 1rem", fontSize: "0.78rem", color: "#475569" }}>
                  {ISSUE_OPTIONS.map((opt) => (
                    <div key={opt.id}>
                      {opt.label} <strong style={{ color: opt.id === "ok" ? "#16a34a" : "#dc2626" }}>{stats[opt.id]}</strong>
                    </div>
                  ))}
                </div>
              )}
              {/* V0.8.4: 标注完整性检查 */}
              {hasAnyMark && (
                <div style={{ marginTop: "0.6rem", paddingTop: "0.6rem", borderTop: "1px dashed #cbd5e1" }}>
                  <div style={{ fontWeight: 600, fontSize: "0.78rem", marginBottom: "0.3rem", color: "#334155" }}>
                    标注完整性检查：
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.25rem 0.8rem", fontSize: "0.75rem", color: "#475569" }}>
                    <div>有备注但未勾标签：<strong style={{ color: integrityStats.noteButNoTag > 0 ? "#dc2626" : "#16a34a" }}>{integrityStats.noteButNoTag}</strong></div>
                    <div>失败但未标生成失败：<strong style={{ color: integrityStats.failedButNotMarked > 0 ? "#dc2626" : "#16a34a" }}>{integrityStats.failedButNotMarked}</strong></div>
                    <div>有建议标签待确认：<strong style={{ color: integrityStats.hasSuggested > 0 ? "#d97706" : "#16a34a" }}>{integrityStats.hasSuggested}</strong></div>
                  </div>
                </div>
              )}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              {reportCopyState === "copied" && (
                <span style={{ fontSize: "0.78rem", color: "#16a34a" }}>已复制排查报告</span>
              )}
              {reportCopyState === "failed" && (
                <span style={{ fontSize: "0.78rem", color: "#dc2626" }}>复制失败</span>
              )}
              <button
                onClick={copyReport}
                disabled={!data}
                style={{
                  padding: "0.5rem 1rem", borderRadius: 8, fontSize: "0.8rem", fontWeight: 600,
                  border: "1px solid #c026d3", background: "white", color: "#c026d3",
                  cursor: data ? "pointer" : "not-allowed",
                  opacity: data ? 1 : 0.5,
                }}
              >
                📋 复制本轮排查报告
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.25rem" }}>
            {data.results.map((s) => {
              const r = s.result;
              const q = r.quality?.overallScore;
              const mark = issueMarks[s.styleId] ?? { issues: [], note: "" };
              const isExpanded = !!expanded[s.styleId];
              const jsonState = jsonCopyState[s.styleId] ?? "";
              return (
                <div key={s.styleId} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "0.3rem" }}>
                    <strong style={{ fontSize: "0.95rem" }}>{s.styleName}</strong>
                    {q !== undefined && (
                      <span style={{ marginLeft: "auto", background: "#1f6feb", color: "white", borderRadius: 10, padding: "2px 10px", fontSize: "0.78rem" }}>结构 {q}/5</span>
                    )}
                  </div>
                  <div style={{ fontSize: "0.74rem", color: "#94a3b8", marginBottom: "0.6rem" }}>{s.description}</div>

                  {r.status === "succeeded" && r.finalVideoUrl ? (
                    <>
                      <div style={{ background: "#0f172a", borderRadius: 10, padding: "0.75rem", display: "flex", justifyContent: "center", marginBottom: "0.5rem" }}>
                        <video controls playsInline src={resolveUrl(r.finalVideoUrl)}
                          style={{ width: "min(100%, 260px)", aspectRatio: "9/16", borderRadius: 8, background: "#020617" }} />
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", fontSize: "0.75rem" }}>
                        <a href={resolveUrl(r.finalVideoUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "none" }}>▶ 新标签播放</a>
                        <a href={resolveUrl(r.finalVideoUrl)} download style={{ color: "#2563eb", textDecoration: "none" }}>⬇ 下载</a>
                        {r.srtUrl && <a href={resolveUrl(r.srtUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#f59e0b", textDecoration: "none" }}>📝 字幕</a>}
                      </div>
                    </>
                  ) : (
                    <div style={{ background: "#fef2f2", border: "1px dashed #ef4444", borderRadius: 8, padding: "1.25rem", textAlign: "center", color: "#ef4444", fontSize: "0.8rem" }}>
                      ❌ {r.status}<br />{r.failedReason}
                    </div>
                  )}

                  {/* V0.8.4: 标注提醒块 —— 备注/失败 → 建议标签 */}
                  {(() => {
                    const noteNonEmpty = mark.note.trim().length > 0;
                    const isFailed = r.status === "failed";
                    const noteButNoTag = noteNonEmpty && mark.issues.length === 0;
                    const failedNotMarked = isFailed && !mark.issues.includes("render_failed");
                    const suggested = inferIssueHintsFromNote(mark.note, r.status);
                    const suggestedLabels = hintsToLabels(suggested.filter((id) => id !== "render_failed"));
                    if (!noteButNoTag && !failedNotMarked) return null;
                    return (
                      <div style={{
                        marginTop: "0.75rem",
                        background: noteButNoTag ? "#fff7ed" : "#fef2f2",
                        border: noteButNoTag ? "1px solid #fdba74" : "1px solid #fca5a5",
                        borderRadius: 8,
                        padding: "0.55rem 0.7rem",
                        fontSize: "0.74rem",
                        color: noteButNoTag ? "#9a3412" : "#991b1b",
                      }}>
                        {failedNotMarked && (
                          <div style={{ marginBottom: noteButNoTag ? "0.35rem" : 0 }}>
                            ⚠️ 该样式生成失败，建议勾选「<strong>生成失败</strong>」，并查看 <code>failedReason</code> / <code>logsTail</code>。
                          </div>
                        )}
                        {noteButNoTag && (
                          <div>
                            🟠 检测到备注中可能包含问题，但尚未勾选标签。
                            {suggestedLabels.length > 0 && (
                              <> 建议补充：<strong>{suggestedLabels.join("、")}</strong>。</>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })()}

                  {/* 任务一：人工问题标签 */}
                  <div style={{ marginTop: "0.85rem" }}>
                    <div style={{ fontSize: "0.74rem", fontWeight: 600, color: "#475569", marginBottom: "0.4rem" }}>
                      人工问题：
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                      {ISSUE_OPTIONS.map((opt) => {
                        const active = mark.issues.includes(opt.id);
                        const isOk = opt.id === "ok";
                        return (
                          <button
                            key={opt.id}
                            onClick={() => toggleIssue(s.styleId, opt.id)}
                            title={isOk ? "与其他问题互斥" : "可多选，再次点击取消"}
                            style={{
                              padding: "0.25rem 0.6rem", borderRadius: 14, fontSize: "0.72rem",
                              cursor: "pointer", transition: "all 0.15s",
                              border: active
                                ? (isOk ? "1px solid #16a34a" : "1px solid #dc2626")
                                : "1px solid #cbd5e1",
                              background: active
                                ? (isOk ? "#dcfce7" : "#fee2e2")
                                : "white",
                              color: active
                                ? (isOk ? "#166534" : "#991b1b")
                                : "#475569",
                              fontWeight: active ? 600 : 400,
                            }}
                          >
                            {active ? "✓ " : ""}{opt.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* 任务二：人工备注 */}
                  <div style={{ marginTop: "0.85rem" }}>
                    <div style={{ fontSize: "0.74rem", fontWeight: 600, color: "#475569", marginBottom: "0.3rem" }}>
                      人工备注
                    </div>
                    <textarea
                      value={mark.note}
                      onChange={(e) => updateNote(s.styleId, e.target.value)}
                      placeholder="例如：旁白在讲购物 AI，但画面还停在论文评审；字幕晚了约 2 秒；标题文字重叠。"
                      rows={2}
                      style={{
                        width: "100%", padding: "0.5rem", border: "1px solid #cbd5e1",
                        borderRadius: 6, fontSize: "0.75rem", lineHeight: 1.5,
                        fontFamily: "inherit", boxSizing: "border-box", resize: "vertical",
                      }}
                    />
                  </div>

                  {/* 任务三：排查信息折叠区 */}
                  <div style={{ marginTop: "0.85rem" }}>
                    <button
                      onClick={() => toggleExpanded(s.styleId)}
                      style={{
                        width: "100%", padding: "0.45rem", borderRadius: 6, fontSize: "0.78rem",
                        border: "1px solid #e2e8f0", background: "#f8fafc", color: "#475569",
                        cursor: "pointer", textAlign: "left", fontWeight: 600,
                        display: "flex", justifyContent: "space-between", alignItems: "center",
                      }}
                    >
                      <span>🔍 查看排查信息</span>
                      <span>{isExpanded ? "▲" : "▼"}</span>
                    </button>
                    {isExpanded && (
                      <div style={{
                        marginTop: "0.5rem", padding: "0.75rem",
                        background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 6,
                        fontSize: "0.72rem", color: "#334155", lineHeight: 1.6,
                      }}>
                        <div><strong>routeId:</strong> {data.routeId}</div>
                        <div><strong>routeName:</strong> {data.routeName}</div>
                        <div><strong>styleId:</strong> {s.styleId}</div>
                        <div><strong>styleName:</strong> {s.styleName}</div>
                        <div><strong>description:</strong> {s.description}</div>
                        <div><strong>status:</strong> {r.status}</div>
                        <div><strong>finalVideoUrl:</strong> {r.finalVideoUrl || "无"}</div>
                        <div><strong>coverUrl:</strong> {r.coverUrl || "无"}</div>
                        <div><strong>audioUrl:</strong> {r.audioUrl || "无"}</div>
                        <div><strong>srtUrl:</strong> {r.srtUrl || "无"}</div>
                        <div><strong>quality.overallScore:</strong> {q !== undefined ? `${q}` : "无"}</div>
                        <div><strong>targetDuration:</strong> {duration}</div>
                        <div><strong>keyPointCount:</strong> {keyPointCount}</div>
                        <div><strong>useLlmPlan:</strong> {String(useLlmPlan)}</div>
                        <div><strong>manualIssues:</strong> {mark.issues.join(", ") || "（无）"}</div>
                        <div><strong>manualNote:</strong> {mark.note || "（无）"}</div>

                        <div style={{ marginTop: "0.6rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <button
                            onClick={() => copyJson(s)}
                            style={{
                              padding: "0.3rem 0.75rem", borderRadius: 6, fontSize: "0.72rem",
                              border: "1px solid #2563eb", background: "white", color: "#2563eb",
                              cursor: "pointer", fontWeight: 600,
                            }}
                          >
                            📋 复制排查 JSON
                          </button>
                          {jsonState === "copied" && (
                            <span style={{ fontSize: "0.7rem", color: "#16a34a" }}>已复制</span>
                          )}
                          {jsonState === "failed" && (
                            <span style={{ fontSize: "0.7rem", color: "#dc2626" }}>复制失败</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
