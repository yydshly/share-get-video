// Technique Probe - 最佳技术探测台（单入口）
// Path: /video-lab/technique-probe
// 一份内容 → 三技术各出整片 → 统一质量分排名 → 推荐最佳路线，并排看成片。

import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const resolveUrl = (u: string) =>
  u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u;

const DEFAULT_CONTENT = `今日AI前沿三条要点。
第一，ProReviewer论文评审系统发布，在五个质量维度上超越传统自动评审方法，平均提升39%，已在两千篇论文上验证。
第二，主流购物AI助手实测落后，在真实电商场景下主流模型任务通过率仅为57-77%，暴露多轮推理与工具调用短板。
第三，开源多模态模型再下一城，新模型以八十亿参数在多项基准上接近闭源旗舰，推理成本下降约六成。`;

interface Quality {
  overallScore?: number;
  dimensionScores?: Record<string, number>;
}

interface RankItem {
  rank: number;
  visualRoute: string;
  displayName: string;
  status: string;
  score: number | null;
  finalVideoUrl: string;
  coverUrl: string;
  failedReason: string;
}

interface RouteResult {
  visualRoute: string;
  status: string;
  finalVideoUrl: string;
  coverUrl: string;
  audioUrl?: string;
  srtUrl?: string;
  quality?: Quality;
  failedReason?: string;
  steps?: { name: string; status: string; output: string }[];
}

interface ProbeResponse {
  routesRun: string[];
  ranking: RankItem[];
  results: RouteResult[];
  recommendedRoute: string | null;
  recommendedDisplayName: string | null;
  succeededCount: number;
  totalCount: number;
}

// 操作指引步骤
const GUIDE_STEPS = [
  { n: 1, t: "粘贴内容", d: "把一段 AI 资讯/报告原文放进下面的输入框" },
  { n: 2, t: "确认参数", d: "时长、要点数、是否用 LLM 规划（默认即可）" },
  { n: 3, t: "开始探测", d: "勾选确认后点击——会依次为每条技术各出一支完整短视频" },
  { n: 4, t: "看排名与推荐", d: "系统按统一质量分排名，给出最适合这份内容的技术" },
  { n: 5, t: "并排比成片", d: "三支成片并排播放，亲眼对比哪种最优雅好用" },
];

export default function TechniqueProbePage() {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [duration, setDuration] = useState(45);
  const [keyPointCount, setKeyPointCount] = useState(3);
  const [useLlmPlan, setUseLlmPlan] = useState(true);
  const [confirmed, setConfirmed] = useState(false);
  const [running, setRunning] = useState(false);
  const [data, setData] = useState<ProbeResponse | null>(null);
  const [error, setError] = useState("");

  const runProbe = async () => {
    setRunning(true);
    setError("");
    setData(null);
    try {
      const resp = await fetch(`${API_BASE}/technique-probe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          routes: [],
          params: {
            targetDuration: duration,
            aspectRatio: "9:16",
            keyPointCount,
            useLlmPlan,
          },
        }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json: ProbeResponse = await resp.json();
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  const resultByRoute = (route: string) =>
    data?.results.find((r) => r.visualRoute === route);

  const medal = (rank: number) => (rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : `#${rank}`);

  return (
    <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ fontSize: "1.6rem", fontWeight: 700, marginBottom: "0.25rem" }}>🔎 最佳技术探测台</h1>
      <p style={{ color: "#64748b", marginBottom: "1.5rem" }}>
        投一份内容，自动让每种技术各出一支完整短视频，按统一质量分排名，告诉你哪种最适合。
      </p>

      {/* 操作指引 */}
      <div style={{ background: "#f0f9ff", border: "1px solid #bae6fd", borderRadius: 12, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <div style={{ fontWeight: 600, marginBottom: "0.75rem", color: "#0369a1" }}>操作指引</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem" }}>
          {GUIDE_STEPS.map((s) => (
            <div key={s.n} style={{ display: "flex", gap: "0.6rem", alignItems: "flex-start" }}>
              <div style={{ flexShrink: 0, width: 26, height: 26, borderRadius: "50%", background: "#0ea5e9", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem", fontWeight: 700 }}>{s.n}</div>
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>{s.t}</div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: 1.4 }}>{s.d}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 输入 */}
      <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem" }}>① 内容原文</label>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={6}
        style={{ width: "100%", padding: "0.75rem", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: "0.85rem", lineHeight: 1.6, fontFamily: "inherit", boxSizing: "border-box", marginBottom: "1rem" }}
      />

      {/* 参数 */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1.5rem", alignItems: "center", marginBottom: "1rem", fontSize: "0.85rem" }}>
        <label>② 时长(秒)：<input type="number" value={duration} min={15} max={90} onChange={(e) => setDuration(Number(e.target.value))} style={{ width: 64, padding: "0.3rem", border: "1px solid #cbd5e1", borderRadius: 6 }} /></label>
        <label>要点数：<input type="number" value={keyPointCount} min={1} max={6} onChange={(e) => setKeyPointCount(Number(e.target.value))} style={{ width: 56, padding: "0.3rem", border: "1px solid #cbd5e1", borderRadius: 6 }} /></label>
        <label><input type="checkbox" checked={useLlmPlan} onChange={(e) => setUseLlmPlan(e.target.checked)} /> 用 LLM 规划</label>
      </div>

      {/* 成本提示 + 确认 */}
      <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 8, padding: "0.75rem 1rem", marginBottom: "0.75rem", fontSize: "0.8rem", color: "#92400e" }}>
        ⚠️ 探测会依次为 3 种技术各跑一遍完整出片（含 TTS、AI 生图、合成），通常需要 <strong>3-8 分钟</strong> 并消耗 API 额度。
      </div>
      <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
        <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} /> 我已了解耗时与额度消耗
      </label>

      <button
        onClick={runProbe}
        disabled={running || !confirmed || !content.trim()}
        style={{
          padding: "0.7rem 1.5rem", borderRadius: 8, border: "none", fontSize: "0.95rem", fontWeight: 600,
          background: running || !confirmed || !content.trim() ? "#cbd5e1" : "#0ea5e9", color: "white",
          cursor: running || !confirmed || !content.trim() ? "not-allowed" : "pointer",
        }}
      >
        {running ? "⏳ 探测中…（请耐心等待，勿关闭）" : "🚀 开始探测"}
      </button>

      {error && <div style={{ marginTop: "1rem", color: "#ef4444", fontSize: "0.85rem" }}>出错：{error}</div>}

      {running && (
        <div style={{ marginTop: "1.5rem", color: "#64748b", fontSize: "0.85rem" }}>
          正在依次为每种技术出片，整个过程同步执行，完成后一次性展示排名与对比。
        </div>
      )}

      {/* 结果：推荐 + 排名 + 并排成片 */}
      {data && (
        <div style={{ marginTop: "2rem" }}>
          {/* 推荐横幅 */}
          <div style={{ background: data.recommendedRoute ? "linear-gradient(135deg,#059669,#10b981)" : "#64748b", color: "white", borderRadius: 12, padding: "1.25rem 1.5rem", marginBottom: "1.5rem" }}>
            <div style={{ fontSize: "0.8rem", opacity: 0.85 }}>探测结论（{data.succeededCount}/{data.totalCount} 成功）</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>
              {data.recommendedRoute ? `推荐技术：${data.recommendedDisplayName}` : "本次无成功路线，请检查 API 配置或内容"}
            </div>
          </div>

          {/* 排名 + 成片并排 */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.25rem" }}>
            {data.ranking.map((item) => {
              const r = resultByRoute(item.visualRoute);
              const isTop = item.rank === 1 && item.status === "succeeded";
              return (
                <div key={item.visualRoute} style={{ background: "white", border: isTop ? "2px solid #10b981" : "1px solid #e2e8f0", borderRadius: 12, padding: "1rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "0.75rem" }}>
                    <span style={{ fontSize: "1.2rem" }}>{medal(item.rank)}</span>
                    <strong style={{ fontSize: "0.95rem" }}>{item.displayName}</strong>
                    {item.score !== null && (
                      <span style={{ marginLeft: "auto", background: "#1f6feb", color: "white", borderRadius: 10, padding: "2px 10px", fontSize: "0.78rem" }}>
                        质量 {item.score}/5
                      </span>
                    )}
                  </div>

                  {item.status === "succeeded" && item.finalVideoUrl ? (
                    <>
                      <div style={{ background: "#0f172a", borderRadius: 10, padding: "0.75rem", display: "flex", justifyContent: "center", marginBottom: "0.5rem" }}>
                        <video controls playsInline src={resolveUrl(item.finalVideoUrl)}
                          style={{ width: "min(100%, 260px)", aspectRatio: "9/16", borderRadius: 8, background: "#020617" }} />
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", fontSize: "0.75rem", marginBottom: "0.5rem" }}>
                        <a href={resolveUrl(item.finalVideoUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "none" }}>▶ 新标签播放</a>
                        <a href={resolveUrl(item.finalVideoUrl)} download style={{ color: "#2563eb", textDecoration: "none" }}>⬇ 下载</a>
                        {r?.audioUrl && <a href={resolveUrl(r.audioUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#10b981", textDecoration: "none" }}>🔊 音频</a>}
                        {r?.srtUrl && <a href={resolveUrl(r.srtUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#f59e0b", textDecoration: "none" }}>📝 字幕</a>}
                      </div>
                    </>
                  ) : (
                    <div style={{ background: "#fef2f2", border: "1px dashed #ef4444", borderRadius: 8, padding: "1.25rem", textAlign: "center", color: "#ef4444", fontSize: "0.8rem" }}>
                      ❌ {item.status}<br />{item.failedReason}
                    </div>
                  )}

                  {/* 步骤明细 */}
                  {r?.steps && r.steps.length > 0 && (
                    <details style={{ marginTop: "0.5rem" }}>
                      <summary style={{ fontSize: "0.78rem", color: "#64748b", cursor: "pointer" }}>查看生成步骤（{r.steps.length}）</summary>
                      <div style={{ marginTop: "0.5rem", fontSize: "0.72rem", color: "#475569", lineHeight: 1.6 }}>
                        {r.steps.map((s, i) => (
                          <div key={i}>{s.status === "succeeded" ? "✅" : s.status === "failed" ? "❌" : "•"} {s.name}{s.output ? ` — ${s.output}` : ""}</div>
                        ))}
                      </div>
                    </details>
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
