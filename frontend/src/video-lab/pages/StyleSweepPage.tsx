// Style Sweep - 样式对比台
// Path: /video-lab/style-sweep
// 选一条技术路线 → 用同一内容把它的每个预置样式各出一片 → 并排看"同技术不同样式"的效果差异。

import { useState } from "react";

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

  const activeRoute = ROUTES.find((r) => r.id === routeId)!;

  const runSweep = async () => {
    setRunning(true);
    setError("");
    setData(null);
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
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.25rem" }}>
            {data.results.map((s) => {
              const r = s.result;
              const q = r.quality?.overallScore;
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
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
