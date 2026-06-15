// FramePreviewPage - 调试台：单帧快速预览（秒级），调版式/参数/强调词
// Path: /video-lab/frame-preview

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

interface VisualRoute {
  routeId: string;
  displayName: string;
  available: boolean;
}

interface PreviewResult {
  success: boolean;
  imageUrl?: string;
  message?: string;
  warnings?: string[];
  elapsedMs?: number;
  resolution?: string;
}

export default function FramePreviewPage() {
  const [routes, setRoutes] = useState<VisualRoute[]>([]);
  const [route, setRoute] = useState("local_frame_compose");
  const [frameType, setFrameType] = useState<"keypoint" | "cover">("keypoint");
  const [headline, setHeadline] = useState("ProReviewer突破评审质量");
  const [display, setDisplay] = useState("ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%，为AI学术评审提供新范式。");
  const [emphasis, setEmphasis] = useState("39%, ProReviewer");
  const [coverTitle, setCoverTitle] = useState("今日AI前沿速览");
  const [aspect, setAspect] = useState("9:16");
  const [index, setIndex] = useState(1);
  const [total, setTotal] = useState(6);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PreviewResult | null>(null);
  const [error, setError] = useState("");
  // Remotion 片段模式
  const [content, setContent] = useState("科学研究评审实现突破：ProReviewer系统超越传统方法39%。\n依据： 依据 1\n购物AI助手落后：主流模型通过率仅57-77%。\n依据： 依据 1\n企业级AI加速：Anthropic与TCS合作，DeepMind投资千万美元。\n依据： 依据 1");
  const [clip, setClip] = useState<{ success: boolean; clipUrl?: string; message?: string; elapsedMs?: number } | null>(null);
  const isRemotion = route === "template_programmatic_render";
  const isAiAsset = route === "ai_asset_then_compose";
  // 渲染参数
  const [category, setCategory] = useState("");
  const [imageStyle, setImageStyle] = useState("深蓝科技风格抽象背景，未来感，极简，无文字，电影质感，柔和景深");
  const [clipSeconds, setClipSeconds] = useState(3);
  const [useLlmPlan, setUseLlmPlan] = useState(true);
  const [advancedJson, setAdvancedJson] = useState("");
  // 样式参数（对应 AI 建议：颜色区分 / 留白平衡）
  const [titleColor, setTitleColor] = useState("#f8fafc");
  const [bodyColor, setBodyColor] = useState("#94a3b8");
  const [highlightColor, setHighlightColor] = useState("#f59e0b");
  const [contentAlign, setContentAlign] = useState<"top" | "center">("top");
  const [icon, setIcon] = useState("none");
  const styleParams = { titleColor, bodyColor, highlightColor, contentAlign, icon };
  // Remotion 样式
  const [accentColor, setAccentColor] = useState("#3b82f6");
  const [fontScale, setFontScale] = useState(1);
  const [showIcon, setShowIcon] = useState(false);
  const remotionStyle = { accentColor, highlightColor, fontScale, showIcon };
  // 视觉模型评分
  const [judge, setJudge] = useState<{ success: boolean; scores?: Record<string, number>; overall?: number; suggestions?: string[]; message?: string } | null>(null);
  const [judging, setJudging] = useState(false);

  // 合并所有参数（含高级 JSON）
  const buildParams = (base: Record<string, unknown>): Record<string, unknown> => {
    let extra: Record<string, unknown> = {};
    if (advancedJson.trim()) {
      try { extra = JSON.parse(advancedJson); } catch { /* ignore invalid json */ }
    }
    return { ...base, ...extra };
  };

  useEffect(() => {
    fetch(`${API_BASE}/visual-routes`)
      .then((r) => r.json())
      .then(setRoutes)
      .catch(() => {});
  }, []);

  const JUDGE_DIMS: Record<string, string> = { layout: "排版", readability: "可读性", hierarchy: "层级", aesthetics: "美观", consistency: "一致性" };

  const runJudge = async () => {
    const url = clip?.success ? clip.clipUrl : result?.imageUrl;
    if (!url) return;
    setJudging(true);
    setError("");
    try {
      const resp = await fetch(`${API_BASE}/visual-judge`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imageUrl: url }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setJudge(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setJudging(false);
    }
  };

  const resolveUrl = (u?: string) =>
    u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u || "";

  const render = async () => {
    setLoading(true);
    setError("");
    setClip(null);
    setJudge(null);
    try {
      const resp = await fetch(`${API_BASE}/frame-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          visualRoute: route,
          frameType,
          coverTitle,
          shot: {
            headline,
            display,
            emphasisTerms: emphasis.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
          },
          params: buildParams({ aspectRatio: aspect, index, total, category, imageStyle, ...styleParams }),
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setResult(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const renderClip = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    setJudge(null);
    try {
      const body = isRemotion
        ? { visualRoute: route, content, params: buildParams({ aspectRatio: aspect, keyPointCount: total, clipSeconds, useLlmPlan, remotionStyle }) }
        : {
            visualRoute: route, frameType, coverTitle,
            shot: { headline, display, emphasisTerms: emphasis.split(/[,，]/).map((s) => s.trim()).filter(Boolean) },
            params: buildParams({ aspectRatio: aspect, index, total, category, imageStyle, clipSeconds, ...styleParams }),
          };
      const resp = await fetch(`${API_BASE}/clip-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setClip(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = { width: "100%", padding: "0.5rem", border: "1px solid #e2e8f0", borderRadius: 6, fontSize: "0.85rem", boxSizing: "border-box" as const };
  const labelStyle = { fontSize: "0.78rem", fontWeight: 600, color: "#475569", marginBottom: 4, display: "block" };

  return (
    <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <Link to="/video-lab" style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}>← 返回首页</Link>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "0.5rem" }}>调试台 · 单帧快速预览</h1>
      <p style={{ color: "#64748b", fontSize: "0.9rem", marginTop: "0.25rem" }}>
        秒级渲染一张帧，实时调版式、参数、强调词——不跑 TTS、不合成整片，用于摸清每条技术的表现特点。
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "1.5rem", marginTop: "1.5rem", alignItems: "start" }}>
        {/* 控制面板 */}
        <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.9rem" }}>
          <div style={{ display: "flex", gap: "1rem" }}>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>技术路线</label>
              <select value={route} onChange={(e) => setRoute(e.target.value)} style={inputStyle}>
                {routes.map((r) => (
                  <option key={r.routeId} value={r.routeId} disabled={!r.available}>
                    {r.displayName}{r.available ? "" : "（不可用）"}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>帧类型</label>
              <select value={frameType} onChange={(e) => setFrameType(e.target.value as "keypoint" | "cover")} style={inputStyle}>
                <option value="keypoint">关键点卡</option>
                <option value="cover">封面</option>
              </select>
            </div>
          </div>

          {isRemotion ? (
            <>
              <div>
                <label style={labelStyle}>报告内容（渲染 3 秒动效片段：封面 + 首卡入场）</label>
                <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={6} style={{ ...inputStyle, fontFamily: "monospace" }} />
              </div>
              <div style={{ display: "flex", gap: "1rem" }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>比例</label>
                  <select value={aspect} onChange={(e) => setAspect(e.target.value)} style={inputStyle}>
                    <option value="9:16">9:16</option>
                    <option value="16:9">16:9</option>
                    <option value="1:1">1:1</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>要点数</label>
                  <input type="number" value={total} onChange={(e) => setTotal(Number(e.target.value))} style={inputStyle} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>片段秒数</label>
                  <select value={clipSeconds} onChange={(e) => setClipSeconds(Number(e.target.value))} style={inputStyle}>
                    <option value={2}>2s</option>
                    <option value={3}>3s</option>
                    <option value={5}>5s</option>
                  </select>
                </div>
              </div>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.8rem", color: "#475569" }}>
                <input type="checkbox" checked={useLlmPlan} onChange={(e) => setUseLlmPlan(e.target.checked)} /> 用大模型规划内容（关闭则用确定性切分，更快）
              </label>
              {/* Remotion 样式（对应 AI 建议：配色/排版/视觉元素） */}
              <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "0.6rem" }}>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#8b5cf6", marginBottom: "0.4rem" }}>Remotion 样式（对应 AI 建议）</div>
                <div style={{ display: "flex", gap: "0.9rem", alignItems: "center", flexWrap: "wrap" }}>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                    主题色 <input type="color" value={accentColor} onChange={(e) => setAccentColor(e.target.value)} style={{ width: 28, height: 24, padding: 0, border: "none" }} />
                  </label>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                    高亮 <input type="color" value={highlightColor} onChange={(e) => setHighlightColor(e.target.value)} style={{ width: 28, height: 24, padding: 0, border: "none" }} />
                  </label>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                    字号 ×<input type="number" step="0.05" min="0.8" max="1.5" value={fontScale} onChange={(e) => setFontScale(Number(e.target.value))} style={{ width: 52, fontSize: "0.75rem", borderRadius: 4, border: "1px solid #e2e8f0", padding: "2px 4px" }} />
                  </label>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                    <input type="checkbox" checked={showIcon} onChange={(e) => setShowIcon(e.target.checked)} /> 视觉图标
                  </label>
                </div>
              </div>
              <details>
                <summary style={{ cursor: "pointer", fontSize: "0.74rem", color: "#64748b" }}>高级：其他参数 (JSON)</summary>
                <textarea value={advancedJson} onChange={(e) => setAdvancedJson(e.target.value)} rows={2}
                  placeholder='{"stylePreset": "..."}' style={{ ...inputStyle, marginTop: "0.4rem", fontFamily: "monospace", fontSize: "0.75rem" }} />
              </details>
              <button onClick={renderClip} disabled={loading}
                style={{ background: loading ? "#93c5fd" : "#8b5cf6", color: "white", border: "none", borderRadius: 8, padding: "0.6rem", fontSize: "0.9rem", cursor: loading ? "wait" : "pointer", marginTop: "0.25rem" }}>
                {loading ? "渲染片段中（约 20-40 秒）..." : "渲染 3 秒动效片段"}
              </button>
              <div style={{ fontSize: "0.72rem", color: "#8b5cf6" }}>Remotion 是动效路线，单帧看不出特点；片段预览比整片快约 6 倍。</div>
              {error && <div style={{ color: "#ef4444", fontSize: "0.8rem" }}>{error}</div>}
            </>
          ) : (
            <>
              {frameType === "cover" && (
                <div>
                  <label style={labelStyle}>封面标题</label>
                  <input value={coverTitle} onChange={(e) => setCoverTitle(e.target.value)} style={inputStyle} />
                </div>
              )}

              <div>
                <label style={labelStyle}>标题 headline</label>
                <input value={headline} onChange={(e) => setHeadline(e.target.value)} style={inputStyle} />
              </div>

              {frameType === "keypoint" && (
                <div>
                  <label style={labelStyle}>正文 display</label>
                  <textarea value={display} onChange={(e) => setDisplay(e.target.value)} rows={3} style={inputStyle} />
                </div>
              )}

              <div>
                <label style={labelStyle}>强调词 emphasisTerms（逗号分隔，会高亮）</label>
                <input value={emphasis} onChange={(e) => setEmphasis(e.target.value)} style={inputStyle} placeholder="39%, ProReviewer" />
              </div>

              <div style={{ display: "flex", gap: "1rem" }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>比例</label>
                  <select value={aspect} onChange={(e) => setAspect(e.target.value)} style={inputStyle}>
                    <option value="9:16">9:16</option>
                    <option value="16:9">16:9</option>
                    <option value="1:1">1:1</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>序号</label>
                  <input type="number" value={index} onChange={(e) => setIndex(Number(e.target.value))} style={inputStyle} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>总数</label>
                  <input type="number" value={total} onChange={(e) => setTotal(Number(e.target.value))} style={inputStyle} />
                </div>
              </div>

              {/* 渲染参数面板 */}
              <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "0.75rem" }}>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0ea5e9", marginBottom: "0.5rem" }}>渲染参数</div>
                {frameType === "keypoint" && (
                  <div style={{ marginBottom: "0.6rem" }}>
                    <label style={labelStyle}>分类标签 category（留空则隐藏）</label>
                    <input value={category} onChange={(e) => setCategory(e.target.value)} style={inputStyle} placeholder="如：安全 / 评测 / 落地" />
                  </div>
                )}
                {isAiAsset && (
                  <div style={{ marginBottom: "0.6rem" }}>
                    <label style={labelStyle}>AI 背景风格提示词 imageStyle</label>
                    <textarea value={imageStyle} onChange={(e) => setImageStyle(e.target.value)} rows={2} style={inputStyle} />
                  </div>
                )}
                {frameType === "keypoint" && (
                  <div style={{ marginBottom: "0.6rem" }}>
                    <label style={labelStyle}>样式（对应 AI 建议：配色区分 / 留白）</label>
                    <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
                      <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                        标题 <input type="color" value={titleColor} onChange={(e) => setTitleColor(e.target.value)} style={{ width: 28, height: 24, padding: 0, border: "none" }} />
                      </label>
                      <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                        正文 <input type="color" value={bodyColor} onChange={(e) => setBodyColor(e.target.value)} style={{ width: 28, height: 24, padding: 0, border: "none" }} />
                      </label>
                      <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                        重点 <input type="color" value={highlightColor} onChange={(e) => setHighlightColor(e.target.value)} style={{ width: 28, height: 24, padding: 0, border: "none" }} />
                      </label>
                      <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                        对齐
                        <select value={contentAlign} onChange={(e) => setContentAlign(e.target.value as "top" | "center")} style={{ fontSize: "0.75rem", borderRadius: 4, border: "1px solid #e2e8f0", padding: "2px 4px" }}>
                          <option value="top">顶部</option>
                          <option value="center">居中</option>
                        </select>
                      </label>
                      <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                        图标
                        <select value={icon} onChange={(e) => setIcon(e.target.value)} style={{ fontSize: "0.75rem", borderRadius: 4, border: "1px solid #e2e8f0", padding: "2px 4px" }}>
                          <option value="none">无</option>
                          <option value="bars">数据条</option>
                          <option value="arrow">上升箭头</option>
                          <option value="ring">圆环</option>
                          <option value="spark">星亮</option>
                          <option value="dots">圆点</option>
                        </select>
                      </label>
                    </div>
                    <div style={{ fontSize: "0.68rem", color: "#94a3b8", marginTop: 4 }}>图标显示在卡片右上（无分类标签时）。</div>
                  </div>
                )}
                <details>
                  <summary style={{ cursor: "pointer", fontSize: "0.74rem", color: "#64748b" }}>高级：其他参数 (JSON)</summary>
                  <textarea value={advancedJson} onChange={(e) => setAdvancedJson(e.target.value)} rows={2}
                    placeholder='{"subtitle": "..."}' style={{ ...inputStyle, marginTop: "0.4rem", fontFamily: "monospace", fontSize: "0.75rem" }} />
                </details>
              </div>

              <div style={{ display: "flex", gap: "0.6rem", marginTop: "0.25rem" }}>
                <button onClick={render} disabled={loading}
                  style={{ flex: 1, background: loading ? "#93c5fd" : "#3b82f6", color: "white", border: "none", borderRadius: 8, padding: "0.6rem", fontSize: "0.88rem", cursor: loading ? "wait" : "pointer" }}>
                  {loading ? "..." : "渲染单帧"}
                </button>
                <button onClick={renderClip} disabled={loading}
                  style={{ flex: 1, background: loading ? "#a5b4fc" : "#0ea5e9", color: "white", border: "none", borderRadius: 8, padding: "0.6rem", fontSize: "0.88rem", cursor: loading ? "wait" : "pointer" }}>
                  {loading ? "..." : "渲染动效片段"}
                </button>
              </div>
              <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                动效片段 = Ken Burns（缓慢缩放 + 淡入），让静态卡也"动"起来{isAiAsset ? "（AI 背景约需 5-10 秒）" : ""}。
              </div>
              {error && <div style={{ color: "#ef4444", fontSize: "0.8rem" }}>{error}</div>}
            </>
          )}
        </div>

        {/* 预览区 */}
        <div style={{ background: "#0f172a", borderRadius: 12, padding: "1rem", position: "sticky", top: "1rem" }}>
          {isRemotion ? (
            <>
              {!clip && <div style={{ color: "#64748b", textAlign: "center", padding: "3rem 0", fontSize: "0.85rem" }}>点击「渲染 3 秒动效片段」查看动态效果</div>}
              {clip && clip.success && clip.clipUrl && (
                <>
                  <video controls autoPlay loop muted playsInline src={resolveUrl(clip.clipUrl)}
                    style={{ width: "100%", borderRadius: 8, display: "block", background: "#020617" }} />
                  <div style={{ color: "#94a3b8", fontSize: "0.72rem", marginTop: "0.5rem", textAlign: "center" }}>
                    3 秒片段 · {clip.elapsedMs}ms · 循环播放
                  </div>
                </>
              )}
              {clip && !clip.success && (
                <div style={{ color: "#fbbf24", fontSize: "0.82rem", padding: "1.5rem", lineHeight: 1.6 }}>{clip.message || "渲染失败"}</div>
              )}
            </>
          ) : (
            <>
              {clip && clip.success && clip.clipUrl && (
                <>
                  <video controls autoPlay loop muted playsInline src={resolveUrl(clip.clipUrl)}
                    style={{ width: "100%", borderRadius: 8, display: "block", background: "#020617" }} />
                  <div style={{ color: "#94a3b8", fontSize: "0.72rem", marginTop: "0.5rem", textAlign: "center" }}>
                    Ken Burns 动效 · {clip.elapsedMs}ms · 循环播放
                  </div>
                </>
              )}
              {clip && !clip.success && (
                <div style={{ color: "#fbbf24", fontSize: "0.82rem", padding: "1.5rem", lineHeight: 1.6 }}>{clip.message || "动效片段渲染失败"}</div>
              )}
              {!clip && !result && <div style={{ color: "#64748b", textAlign: "center", padding: "3rem 0", fontSize: "0.85rem" }}>渲染单帧调版式，或渲染动效片段看 Ken Burns</div>}
              {!clip && result && result.success && result.imageUrl && (
                <>
                  <img src={resolveUrl(result.imageUrl)} alt="preview"
                    style={{ width: "100%", borderRadius: 8, display: "block" }} />
                  <div style={{ color: "#94a3b8", fontSize: "0.72rem", marginTop: "0.5rem", textAlign: "center" }}>
                    {result.resolution} · {result.elapsedMs}ms
                  </div>
                </>
              )}
              {result && !result.success && (
                <div style={{ color: "#fbbf24", fontSize: "0.82rem", padding: "1.5rem", lineHeight: 1.6 }}>
                  {result.message || "渲染失败"}
                </div>
              )}
              {result?.warnings && result.warnings.length > 0 && (
                <div style={{ color: "#fbbf24", fontSize: "0.7rem", marginTop: "0.5rem" }}>
                  {result.warnings.map((w, i) => <div key={i}>⚠️ {w}</div>)}
                </div>
              )}
            </>
          )}

          {/* AI 视觉评分 */}
          {((result && result.success) || (clip && clip.success)) && (
            <div style={{ marginTop: "0.75rem", borderTop: "1px solid #1e293b", paddingTop: "0.75rem" }}>
              <button onClick={runJudge} disabled={judging}
                style={{ width: "100%", background: judging ? "#64748b" : "#10b981", color: "white", border: "none", borderRadius: 8, padding: "0.5rem", fontSize: "0.82rem", cursor: judging ? "wait" : "pointer" }}>
                {judging ? "AI 评分中..." : "🤖 AI 视觉评分（排版/可读性/层级/美观）"}
              </button>
              {judge && judge.success && (
                <div style={{ marginTop: "0.6rem" }}>
                  <div style={{ color: "#f8fafc", fontSize: "0.9rem", fontWeight: 700, marginBottom: "0.4rem" }}>
                    综合 {judge.overall}/5
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginBottom: "0.5rem" }}>
                    {judge.scores && Object.entries(judge.scores).map(([k, v]) => (
                      <span key={k} style={{ fontSize: "0.72rem", background: "#1e293b", color: "#cbd5e1", borderRadius: 6, padding: "2px 8px" }}>
                        {JUDGE_DIMS[k] ?? k}: <b>{v}</b>
                      </span>
                    ))}
                  </div>
                  {judge.suggestions && judge.suggestions.length > 0 && (
                    <ul style={{ margin: 0, paddingLeft: 18, color: "#94a3b8", fontSize: "0.74rem", lineHeight: 1.7 }}>
                      {judge.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  )}
                </div>
              )}
              {judge && !judge.success && (
                <div style={{ color: "#fbbf24", fontSize: "0.76rem", marginTop: "0.5rem" }}>{judge.message || "评分失败"}</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
