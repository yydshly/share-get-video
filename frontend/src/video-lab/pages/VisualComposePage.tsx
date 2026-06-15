// VisualComposePage - 视频生成路线对比（投报告 → 多路线各出片 → 质量分对比）
// Path: /video-lab/visual-compose

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const DEFAULT_CONTENT = `今日AI前沿呈现多条并行进展线索：多语言NLP在低资源方言、科学事实检测等领域取得突破，阿尔及利亚方言谣言检测混合框架F1达0.84；AI评估体系向多维化和精细化演进，购物推理、长期搜索、立场复杂度等新基准揭示主流模型显著短板；安全对齐方面，主动调查评审、欺骗检测等新范式推动可扩展监督研究；企业级AI落地加速。

科学研究评审实现"主动调查"突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越提示工程方法39%。
依据： 依据 1
购物AI助手全面落后主流模型：Shopping Reasoning Bench测评发现GPT、Claude、Gemini系列通过率仅57-77%。
依据： 依据 1
企业级AI加速进入受监管行业：Anthropic与TCS、DXC建立全球联盟，DeepMind宣布千万美元多智能体安全研究投资。
依据： 依据 1`;

const DIM_LABELS: Record<string, string> = {
  information_accuracy: "信息准确",
  audio_visual_sync: "音画对应",
  visual_rendering: "显示合理",
  viewer_friendly: "视频友好",
};

const STATUS_COLOR: Record<string, string> = {
  pass: "#10b981",
  warn: "#f59e0b",
  fail: "#ef4444",
};

interface VisualRoute {
  routeId: string;
  displayName: string;
  available: boolean;
  availabilityMessage: string;
}

interface QualityCheck {
  checkId: string;
  dimension: string;
  status: string;
  message: string;
}

interface Quality {
  overallScore: number;
  dimensionScores: Record<string, number>;
  counts: Record<string, number>;
  checks: QualityCheck[];
  needsHuman: string[];
}

interface StepSummary {
  name: string;
  status: string;
  output: string;
}

interface RouteResult {
  visualRoute: string;
  status: string;
  params?: Record<string, unknown>;
  finalVideoUrl: string;
  coverUrl: string;
  audioUrl?: string;
  srtUrl?: string;
  manifestUrl?: string;
  audioDurationSec: number;
  subtitleCount: number;
  quality: Quality | Record<string, never>;
  failedReason: string;
  warnings: string[];
  steps?: StepSummary[];
  logs?: string[];
  _pending?: boolean;
}

export default function VisualComposePage() {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [routes, setRoutes] = useState<VisualRoute[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [duration, setDuration] = useState(45);
  const [keyPointCount, setKeyPointCount] = useState(6);
  const [useLlmPlan, setUseLlmPlan] = useState(true);
  const [styleJson, setStyleJson] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<Record<string, RouteResult>>({});
  const [judges, setJudges] = useState<Record<string, { loading?: boolean; success?: boolean; overall?: number; scores?: Record<string, number>; suggestions?: string[]; message?: string }>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/visual-routes`)
      .then((r) => r.json())
      .then((data: VisualRoute[]) => {
        setRoutes(data);
        setSelected(data.filter((d) => d.available).map((d) => d.routeId));
      })
      .catch((e) => setError("加载视觉路线失败：" + String(e)));
  }, []);

  const toggle = (id: string) =>
    setSelected((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  const runAll = async () => {
    if (selected.length === 0) {
      setError("请至少选择一条可用路线");
      return;
    }
    if (!confirmed) {
      setError("请先勾选下方「确认运行」（本次会调用大模型，可能产生成本）");
      return;
    }
    setError("");
    setRunning(true);
    setResults(Object.fromEntries(selected.map((r) => [r, { visualRoute: r, _pending: true } as RouteResult])));

    let parsedStyle: Record<string, unknown> = {};
    if (styleJson.trim()) {
      try { parsedStyle = JSON.parse(styleJson); } catch { setError("样式参数 JSON 格式错误，已忽略"); }
    }

    for (const route of selected) {
      try {
        const resp = await fetch(`${API_BASE}/visual-compose`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content,
            visualRoute: route,
            params: { targetDuration: duration, aspectRatio: "9:16", keyPointCount, useLlmPlan, ...parsedStyle },
          }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
        setResults((prev) => ({ ...prev, [route]: data }));
      } catch (e) {
        setResults((prev) => ({
          ...prev,
          [route]: { visualRoute: route, status: "failed", failedReason: String(e) } as RouteResult,
        }));
      }
    }
    setRunning(false);
  };

  const resolveUrl = (u: string) =>
    u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u;

  const JUDGE_DIMS: Record<string, string> = { layout: "排版", readability: "可读性", hierarchy: "层级", aesthetics: "美观", consistency: "一致性" };

  const judgeRoute = async (route: string) => {
    const r = results[route];
    const url = r?.finalVideoUrl || r?.coverUrl;  // 优先视频 → 多帧综合评分
    if (!url) return;
    setJudges((p) => ({ ...p, [route]: { loading: true } }));
    try {
      const resp = await fetch(`${API_BASE}/visual-judge`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imageUrl: url, route }),
      });
      const data = await resp.json();
      setJudges((p) => ({ ...p, [route]: { ...data, loading: false } }));
    } catch (e) {
      setJudges((p) => ({ ...p, [route]: { success: false, message: String(e), loading: false } }));
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1280px", margin: "0 auto" }}>
      <Link to="/video-lab" style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}>← 返回首页</Link>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "0.5rem" }}>视频生成路线对比</h1>
      <p style={{ color: "#64748b", fontSize: "0.9rem", marginTop: "0.25rem" }}>
        投入一份报告 → 多种技术各生成一个视频 → 自动质量评分对比（信息准确 / 音画对应 / 显示合理 / 视频友好）
      </p>

      {/* 报告输入 */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1.5rem", margin: "1.5rem 0" }}>
        <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem" }}>报告原文</div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={8}
          style={{ width: "100%", padding: "0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.85rem", fontFamily: "monospace", resize: "vertical", boxSizing: "border-box" }}
        />
        <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.75rem", flexWrap: "wrap", alignItems: "center", fontSize: "0.85rem" }}>
          <label>时长(s): <input type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value))} style={{ width: 60 }} /></label>
          <label>要点数: <input type="number" value={keyPointCount} onChange={(e) => setKeyPointCount(Number(e.target.value))} style={{ width: 50 }} /></label>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={useLlmPlan} onChange={(e) => setUseLlmPlan(e.target.checked)} /> 用大模型规划展示
          </label>
        </div>
        <details style={{ marginTop: "0.75rem" }}>
          <summary style={{ cursor: "pointer", fontSize: "0.8rem", color: "#475569", fontWeight: 600 }}>样式参数（可选，应用到所有路线）</summary>
          <div style={{ fontSize: "0.72rem", color: "#94a3b8", margin: "0.4rem 0" }}>
            把调试台调好的样式 JSON 贴这里，正式出片就会带上。例如：
            <code style={{ background: "#f1f5f9", padding: "1px 4px", borderRadius: 3 }}>{`{"highlightColor":"#22d3ee","contentAlign":"center","icon":"bars","remotionStyle":{"accentColor":"#22d3ee","fontScale":1.1,"showIcon":true}}`}</code>
          </div>
          <textarea value={styleJson} onChange={(e) => setStyleJson(e.target.value)} rows={3}
            placeholder='{"highlightColor":"#22d3ee", ...}' style={{ width: "100%", padding: "0.5rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.78rem", fontFamily: "monospace", boxSizing: "border-box" }} />
        </details>
      </div>

      {/* 路线选择 */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1.5rem", marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "1rem" }}>选择技术路线</div>
        {routes.length === 0 && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "0.75rem 1rem", fontSize: "0.82rem", color: "#b91c1c", marginBottom: "1rem" }}>
            未加载到任何视觉路线。请确认后端已启动：<code>uvicorn app.main:app --reload --port 8000</code>
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem", marginBottom: "1rem" }}>
          {routes.map((r) => {
            const checked = selected.includes(r.routeId);
            const color = r.available ? "#10b981" : "#94a3b8";
            return (
              <div key={r.routeId} onClick={() => r.available && toggle(r.routeId)}
                style={{ border: `2px solid ${checked ? color : "#e2e8f0"}`, borderRadius: 10, padding: "0.9rem", cursor: r.available ? "pointer" : "not-allowed", background: checked ? `${color}08` : "white", opacity: r.available ? 1 : 0.6 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <input type="checkbox" checked={checked} readOnly disabled={!r.available} />
                  <strong style={{ fontSize: "0.85rem" }}>{r.displayName}</strong>
                </div>
                <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 6, fontFamily: "monospace" }}>{r.routeId}</div>
                <div style={{ fontSize: "0.72rem", color: r.available ? "#10b981" : "#ef4444", marginTop: 4 }}>
                  {r.available ? "✓ 可用" : "✗ " + r.availabilityMessage}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ background: "#fef3c7", border: "1px solid #fcd34d", borderRadius: 8, padding: "0.75rem 1rem", fontSize: "0.8rem", color: "#92400e", marginBottom: "1rem" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
            本次会调用 MiniMax 大模型（LLM 规划 / TTS / 文生图），可能产生 API 成本，且渲染需要一定时间。确认运行。
          </label>
        </div>

        <button onClick={runAll} disabled={running}
          style={{ background: running ? "#93c5fd" : "#3b82f6", color: "white", border: "none", borderRadius: 8, padding: "0.6rem 1.5rem", fontSize: "0.9rem", cursor: running ? "wait" : "pointer" }}>
          {running ? "⏳ 生成中（逐条进行，每条约 1-3 分钟）..." : `生成并对比 (${selected.length} 条)`}
        </button>
        {error && <div style={{ marginTop: "1rem", color: "#ef4444", fontSize: "0.85rem" }}>⚠️ {error}</div>}
        {running && (
          <div style={{ marginTop: "1rem", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, padding: "0.6rem 1rem", fontSize: "0.82rem", color: "#1e40af" }}>
            正在依次生成：{selected.map((r) => {
              const st = results[r];
              const mark = !st ? "•" : st._pending ? "⏳" : st.status === "succeeded" ? "✅" : "❌";
              return `${mark} ${routes.find((x) => x.routeId === r)?.displayName ?? r}`;
            }).join("  ")}
          </div>
        )}
      </div>

      {/* 结果对比 */}
      {Object.keys(results).length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.25rem" }}>
          {selected.map((route) => {
            const r = results[route];
            if (!r) return null;
            const q = (r.quality && (r.quality as Quality).overallScore !== undefined) ? (r.quality as Quality) : null;
            const routeName = routes.find((x) => x.routeId === route)?.displayName ?? route;
            return (
              <div key={route} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "0.75rem" }}>
                  <strong style={{ fontSize: "0.9rem" }}>{routeName}</strong>
                  {q && <span style={{ marginLeft: "auto", background: "#1f6feb", color: "white", borderRadius: 10, padding: "2px 8px", fontSize: "0.75rem" }}>质量 {q.overallScore}/5</span>}
                </div>

                {r._pending && <div style={{ color: "#64748b", fontSize: "0.85rem", padding: "2rem 0", textAlign: "center" }}>⏳ 生成中...</div>}

                {!r._pending && r.status === "succeeded" && r.finalVideoUrl && (
                  <>
                    <div style={{ background: "#0f172a", borderRadius: 10, padding: "1rem", display: "flex", justifyContent: "center", marginBottom: "0.5rem" }}>
                      <video controls playsInline src={resolveUrl(r.finalVideoUrl)}
                        style={{ width: "min(100%, 300px)", aspectRatio: "9/16", borderRadius: 8, background: "#020617" }} />
                    </div>
                    {/* 播放/下载入口 + 中间产物 */}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBottom: "0.75rem", fontSize: "0.75rem" }}>
                      <a href={resolveUrl(r.finalVideoUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "none" }}>▶ 新标签播放</a>
                      <a href={resolveUrl(r.finalVideoUrl)} download style={{ color: "#2563eb", textDecoration: "none" }}>⬇ 下载视频</a>
                      {r.audioUrl && <a href={resolveUrl(r.audioUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#10b981", textDecoration: "none" }}>🔊 音频</a>}
                      {r.srtUrl && <a href={resolveUrl(r.srtUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#f59e0b", textDecoration: "none" }}>📝 字幕</a>}
                      {r.manifestUrl && <a href={resolveUrl(r.manifestUrl)} target="_blank" rel="noopener noreferrer" style={{ color: "#8b5cf6", textDecoration: "none" }}>📋 manifest</a>}
                    </div>
                  </>
                )}

                {!r._pending && r.status !== "succeeded" && (
                  <div style={{ background: "#fef2f2", border: "1px dashed #ef4444", borderRadius: 8, padding: "1.5rem", textAlign: "center", color: "#ef4444", fontSize: "0.8rem", marginBottom: "0.75rem" }}>
                    ❌ {r.status}<br />{r.failedReason}
                  </div>
                )}

                {q && (
                  <>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginBottom: "0.5rem" }}>
                      {Object.entries(q.dimensionScores).map(([k, v]) => (
                        <span key={k} style={{ fontSize: "0.72rem", background: "#f1f5f9", borderRadius: 6, padding: "2px 8px" }}>
                          {DIM_LABELS[k] ?? k}: <b>{v}</b>
                        </span>
                      ))}
                    </div>
                    {r.audioDurationSec > 0 && (
                      <div style={{ fontSize: "0.72rem", color: "#64748b", marginBottom: "0.5rem" }}>
                        时长 {Math.round(r.audioDurationSec)}s · 字幕 {r.subtitleCount} 条
                      </div>
                    )}
                    <div style={{ fontSize: "0.72rem", lineHeight: 1.7 }}>
                      {q.checks.filter((c) => c.status !== "pass").map((c, i) => (
                        <div key={i}>
                          <span style={{ color: STATUS_COLOR[c.status] }}>[{c.status}]</span> {c.message}
                        </div>
                      ))}
                      {q.checks.every((c) => c.status === "pass") && <div style={{ color: "#10b981" }}>全部检查通过 ✓</div>}
                    </div>
                  </>
                )}

                {/* AI 视觉评分（感知层：好不好看） */}
                {r.status === "succeeded" && (r.coverUrl || r.finalVideoUrl) && (
                  <div style={{ marginTop: "0.6rem", borderTop: "1px solid #f1f5f9", paddingTop: "0.6rem" }}>
                    {(() => {
                      const j = judges[route];
                      return (
                        <>
                          <button onClick={() => judgeRoute(route)} disabled={j?.loading}
                            style={{ background: j?.loading ? "#94a3b8" : "#10b981", color: "white", border: "none", borderRadius: 6, padding: "0.35rem 0.75rem", fontSize: "0.75rem", cursor: j?.loading ? "wait" : "pointer" }}>
                            {j?.loading ? "AI 评分中..." : "🤖 AI 视觉评分"}
                          </button>
                          {j && j.success && (
                            <div style={{ marginTop: "0.5rem" }}>
                              <div style={{ fontWeight: 700, fontSize: "0.85rem" }}>感知 {j.overall}/5</div>
                              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", margin: "0.3rem 0" }}>
                                {j.scores && Object.entries(j.scores).map(([k, v]) => (
                                  <span key={k} style={{ fontSize: "0.7rem", background: "#ecfdf5", color: "#065f46", borderRadius: 6, padding: "1px 7px" }}>
                                    {JUDGE_DIMS[k] ?? k}: <b>{v}</b>
                                  </span>
                                ))}
                              </div>
                              {j.suggestions && j.suggestions.length > 0 && (
                                <ul style={{ margin: 0, paddingLeft: 16, color: "#64748b", fontSize: "0.72rem", lineHeight: 1.6 }}>
                                  {j.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                                </ul>
                              )}
                            </div>
                          )}
                          {j && j.success === false && <div style={{ color: "#f59e0b", fontSize: "0.72rem", marginTop: "0.4rem" }}>{j.message}</div>}
                        </>
                      );
                    })()}
                  </div>
                )}

                {/* 交互参数 */}
                {!r._pending && r.params && (
                  <div style={{ marginTop: "0.6rem", fontSize: "0.7rem", color: "#64748b", background: "#f8fafc", borderRadius: 6, padding: "0.4rem 0.6rem", fontFamily: "monospace" }}>
                    参数：{Object.entries(r.params).map(([k, v]) => `${k}=${v}`).join("  ")}
                  </div>
                )}

                {/* 步骤 + 日志 */}
                {!r._pending && (r.steps?.length || r.logs?.length) ? (
                  <details style={{ marginTop: "0.5rem", fontSize: "0.72rem" }}>
                    <summary style={{ cursor: "pointer", color: "#475569", fontWeight: 600 }}>步骤与日志</summary>
                    {r.steps?.length ? (
                      <div style={{ marginTop: "0.4rem" }}>
                        {r.steps.map((s, i) => (
                          <div key={i} style={{ color: s.status === "failed" ? "#ef4444" : s.status === "succeeded" ? "#16a34a" : "#64748b" }}>
                            {s.status === "succeeded" ? "✅" : s.status === "failed" ? "❌" : "•"} {s.name}{s.output ? ` — ${s.output}` : ""}
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {r.logs?.length ? (
                      <pre style={{ marginTop: "0.4rem", maxHeight: 200, overflow: "auto", background: "#0f172a", color: "#cbd5e1", padding: "0.6rem", borderRadius: 6, fontSize: "0.68rem", whiteSpace: "pre-wrap" }}>
                        {r.logs.join("\n")}
                      </pre>
                    ) : null}
                  </details>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
