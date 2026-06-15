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
  { id: "template_programmatic_render", name: "Remotion 动效", styleCount: 6 },
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
];

interface Quality { overallScore?: number }

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
  const buildCheckJson = (s: StyleResult) => {
    const r = s.result;
    const mark = issueMarks[s.styleId] ?? { issues: [], note: "" };
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
      quality: { overallScore: r.quality?.overallScore },
      params: {
        targetDuration: duration,
        keyPointCount,
        useLlmPlan,
      },
      manualIssues: mark.issues,
      manualNote: mark.note,
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

  // 复制本轮 Markdown 排查报告
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
    lines.push("## 结果统计");
    lines.push("");
    lines.push(`- 总样式数：${data.styleCount}`);
    lines.push(`- 成功数：${data.succeededCount}`);
    ISSUE_OPTIONS.forEach((opt) => {
      lines.push(`- ${opt.label}：${stats[opt.id]}`);
    });
    lines.push("");
    lines.push("## 样式明细");
    data.results.forEach((s) => {
      const r = s.result;
      const mark = issueMarks[s.styleId] ?? { issues: [], note: "" };
      const q = r.quality?.overallScore;
      const issueLabels = mark.issues
        .map((id) => ISSUE_OPTIONS.find((o) => o.id === id)?.label ?? id)
        .join("、") || "（无）";
      lines.push("");
      lines.push(`### ${s.styleName}`);
      lines.push("");
      lines.push(`- styleId: ${s.styleId}`);
      lines.push(`- status: ${r.status}`);
      lines.push(`- quality: ${q !== undefined ? `${q}/5` : "无"}`);
      lines.push(`- finalVideoUrl: ${r.finalVideoUrl || "无"}`);
      lines.push(`- audioUrl: ${r.audioUrl || "无"}`);
      lines.push(`- srtUrl: ${r.srtUrl || "无"}`);
      lines.push(`- 人工问题：${issueLabels}`);
      lines.push(`- 人工备注：${mark.note || "（无）"}`);
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
