// RoutePlaygroundPage - V0.3.4: Direct route testing interface
// Path: /video-lab/route-playground

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const DEFAULT_CONTENT = `今天有三条 AI 动态值得关注。

第一，OpenAI 发布新的推理模型能力，重点提升复杂任务分解和工具调用稳定性。

第二，Anthropic 更新 Claude Code 相关能力，进一步强化开发者在代码审查，重构和自动化任务中的使用体验。

第三，HeyGen 推出 HyperFrames 能力，可以通过 HTML 生成视频，为程序化视频制作提供了新的路线。

这三条信息共同说明，AI 视频和 AI Agent 正在从单点能力走向可组合的工作流。`;

const ROUTE_INFO: Record<string, {
  name: string;
  status: "real" | "manual" | "mock" | "reserved";
  description: string;
  condition: string;
  outputs: string;
  defaultSelected: boolean;
}> = {
  local_frame_compose: {
    name: "本地帧合成",
    status: "real",
    description: "Pillow 生成静态卡片帧，FFmpeg 合成视频",
    condition: "本地 FFmpeg",
    outputs: "MP4",
    defaultSelected: true,
  },
  template_programmatic_render: {
    name: "Remotion 模板",
    status: "real",
    description: "Remotion / React 动态模板渲染",
    condition: "Node.js + Remotion",
    outputs: "MP4",
    defaultSelected: true,
  },
  hyperframes_html_render: {
    name: "HyperFrames HTML",
    status: "manual",
    description: "生成 HTML，人工复制到 HeyGen HyperFrames 渲染",
    condition: "HeyGen HyperFrames 插件",
    outputs: "HTML → MP4（人工）",
    defaultSelected: true,
  },
  tts_subtitle_compose: {
    name: "TTS 旁白合成",
    status: "real",
    description: "MiniMax TTS 生成旁白，SRT 字幕，FFmpeg 合成有声视频",
    condition: "MINIMAX_API_KEY + FFmpeg",
    outputs: "MP4 + MP3 + SRT",
    defaultSelected: false,
  },
};

const STATUS_COLOR: Record<string, string> = {
  real: "#10b981",
  manual: "#8b5cf6",
  mock: "#f59e0b",
  reserved: "#94a3b8",
};

const SCORE_DIMENSIONS = [
  { key: "informationAccuracy", label: "信息准确性" },
  { key: "readability", label: "文字可读性" },
  { key: "visualQuality", label: "视觉质量" },
  { key: "dynamicPerformance", label: "动态表现" },
  { key: "generationStability", label: "生成稳定性" },
  { key: "automationLevel", label: "自动化程度" },
  { key: "costControl", label: "成本可控性" },
  { key: "productizationPotential", label: "产品化潜力" },
];

interface RouteScore {
  routeId: string;
  scores: Record<string, number | null>;
  notes: string;
  conclusion: string;
}

interface BenchmarkResult {
  routeId: string;
  status: string;
  videoUrl: string;
  coverUrl: string;
  manifestUrl: string;
  summary: string;
  artifacts: unknown[];
  metrics: Record<string, unknown>;
  warnings: string[];
}

export default function RoutePlaygroundPage() {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [selectedRoutes, setSelectedRoutes] = useState<string[]>(
    Object.entries(ROUTE_INFO)
      .filter(([, info]) => info.defaultSelected)
      .map(([id]) => id)
  );
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<BenchmarkResult[] | null>(null);
  const [benchmarkId, setBenchmarkId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [scores, setScores] = useState<Record<string, RouteScore>>({});

  const toggleRoute = (id: string) => {
    setSelectedRoutes((prev) =>
      prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]
    );
  };

  const runSelected = async () => {
    if (selectedRoutes.length === 0) {
      setError("请至少选择一条路线");
      return;
    }
    setIsRunning(true);
    setError("");
    setResults(null);

    try {
      const payload = {
        testCaseId: "case_ai_frontier_daily_001",
        title: "链路测试台 - " + new Date().toLocaleDateString("zh-CN"),
        inputPayload: { content },
        commonParams: {
          targetDuration: 45,
          aspectRatio: "9:16",
          keyPointCount: 3,
        },
        routeIds: selectedRoutes,
      };

      const resp = await fetch(`${API_BASE}/route-benchmarks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail ?? `${resp.status}`);
      }

      const data = await resp.json();
      setResults(data.results ?? []);
      setBenchmarkId(data.benchmarkId ?? null);

      // Initialize scores
      const newScores: Record<string, RouteScore> = {};
      for (const r of data.results ?? []) {
        newScores[r.routeId] = {
          routeId: r.routeId,
          scores: Object.fromEntries(SCORE_DIMENSIONS.map((d) => [d.key, null])),
          notes: "",
          conclusion: "",
        };
      }
      setScores(newScores);
    } catch (err) {
      setError(String(err));
    } finally {
      setIsRunning(false);
    }
  };

  const updateScore = (routeId: string, dim: string, val: number | null) => {
    setScores((prev) => ({
      ...prev,
      [routeId]: {
        ...prev[routeId],
        scores: { ...prev[routeId].scores, [dim]: val },
      },
    }));
  };

  const getArtifactUrl = (artifacts: unknown[], type: "htmlUrl" | "audioUrl" | "srtUrl" | "videoUrl") => {
    for (const art of artifacts as Array<{type?: string; payload?: Record<string, unknown>}>) {
      if (art?.type === "manifest" && art?.payload) {
        if (type === "htmlUrl") {
          const url = (art.payload as Record<string, unknown>).htmlUrl as string | undefined;
          if (url) return url;
        }
        if (type === "audioUrl") {
          const url = (art.payload as Record<string, unknown>).audioUrl as string | undefined;
          if (url) return url;
        }
        if (type === "srtUrl") {
          const url = (art.payload as Record<string, unknown>).srtUrl as string | undefined;
          if (url) return url;
        }
      }
    }
    return null;
  };

  const exportMarkdown = (): string => {
    if (!results) return "";
    const lines = [
      "# V0.3 视频生成链路对比报告",
      "",
      `## 1. 测试输入`,
      "",
      "```",
      content.slice(0, 200) + (content.length > 200 ? "..." : ""),
      "```",
      "",
      "## 2. 参与路线",
      "",
      ...selectedRoutes.map((id) => `- ${ROUTE_INFO[id]?.name ?? id} (${id})`),
      "",
      "## 3. 样片结果",
      "",
    ];

    for (const r of results) {
      const info = ROUTE_INFO[r.routeId];
      const score = scores[r.routeId];
      const ratedDims = score ? Object.entries(score.scores).filter(([, v]) => v !== null) : [];
      const avgScore = ratedDims.length > 0
        ? (ratedDims.reduce((a, [, v]) => a + (v as number), 0) / ratedDims.length).toFixed(1)
        : "待评分";

      lines.push(`### ${info?.name ?? r.routeId}`);
      lines.push(`- **是否生成**：${r.status === "succeeded" ? "✅ 是" : r.status === "failed" ? "❌ 否" : r.status === "manual" ? "⚠️ 人工" : "⏳ 待验证"}`);
      lines.push(`- **status**：${r.status}`);
      if (r.videoUrl) lines.push(`- **videoUrl**：${r.videoUrl}`);
      const htmlUrl = getArtifactUrl(r.artifacts, "htmlUrl");
      if (htmlUrl) lines.push(`- **htmlUrl**：${htmlUrl}`);
      const audioUrl = getArtifactUrl(r.artifacts, "audioUrl");
      if (audioUrl) lines.push(`- **audioUrl**：${audioUrl}`);
      const srtUrl = getArtifactUrl(r.artifacts, "srtUrl");
      if (srtUrl) lines.push(`- **srtUrl**：${srtUrl}`);
      if (r.warnings?.length) lines.push(`- **warnings**：${r.warnings.join("; ")}`);
      lines.push(`- **综合评分**：${avgScore}`);
      if (score?.conclusion) lines.push(`- **结论**：${score.conclusion}`);
      lines.push("");
    }

    lines.push("## 4. 横向评分表");
    lines.push("");
    lines.push("| 路线 | " + SCORE_DIMENSIONS.map((d) => d.label).join(" | ") + " |");
    lines.push("|" + "---|".repeat(SCORE_DIMENSIONS.length + 1));
    for (const r of results) {
      const score = scores[r.routeId];
      const routeInfo = ROUTE_INFO[r.routeId];
      const row = [routeInfo?.name ?? r.routeId];
      for (const dim of SCORE_DIMENSIONS) {
        const val = score?.scores[dim.key];
        row.push(val != null ? String(val) : "-");
      }
      lines.push("| " + row.join(" | ") + " |");
    }
    lines.push("");
    lines.push("## 5. 当前判断");
    lines.push("");
    lines.push("- 当前最佳画面路线：（待评分）");
    lines.push("- 当前最佳完整视频路线：（待评分）");
    lines.push("- 当前暂缓路线：hyperframes_html_render（需人工）");
    lines.push("");
    lines.push("## 6. 下一步建议");
    lines.push("");
    lines.push("（请根据评分填写）");

    return lines.join("\n");
  };

  const [exportText, setExportText] = useState("");
  const [showExport, setShowExport] = useState(false);

  return (
    <div style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <Link to="/video-lab" style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}>← 返回首页</Link>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "0.5rem" }}>视频生成链路测试台</h1>
        <p style={{ color: "#64748b", fontSize: "0.9rem", marginTop: "0.25rem" }}>
          用同一份样例测试各视频生成路线，查看结果并对比评分
        </p>
      </div>

      {/* Default content area */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
          <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>测试样例：AI 前沿日报</div>
          <button
            onClick={() => setContent(DEFAULT_CONTENT)}
            style={{ fontSize: "0.75rem", color: "#3b82f6", background: "none", border: "none", cursor: "pointer" }}
          >
            重置默认样例
          </button>
        </div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={6}
          style={{
            width: "100%",
            padding: "0.75rem",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            fontSize: "0.85rem",
            fontFamily: "monospace",
            resize: "vertical",
            boxSizing: "border-box",
          }}
        />
      </div>

      {/* Route selection */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "1rem" }}>选择要测试的路线</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "1rem", marginBottom: "1rem" }}>
          {Object.entries(ROUTE_INFO).map(([id, info]) => {
            const checked = selectedRoutes.includes(id);
            const color = STATUS_COLOR[info.status] ?? "#94a3b8";
            return (
              <div
                key={id}
                onClick={() => toggleRoute(id)}
                style={{
                  border: `2px solid ${checked ? color : "#e2e8f0"}`,
                  borderRadius: "10px",
                  padding: "1rem",
                  cursor: "pointer",
                  background: checked ? `${color}08` : "white",
                  transition: "all 0.15s",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
                  <div style={{
                    width: 18, height: 18,
                    border: `2px solid ${checked ? color : "#cbd5e1"}`,
                    borderRadius: 4,
                    background: checked ? color : "white",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0,
                  }}>
                    {checked && <span style={{ color: "white", fontSize: 12 }}>✓</span>}
                  </div>
                  <span style={{ fontWeight: 600, fontSize: "0.85rem" }}>{info.name}</span>
                  <span style={{
                    fontSize: "0.65rem",
                    color: "white",
                    background: color,
                    borderRadius: "999px",
                    padding: "0.1rem 0.4rem",
                    fontWeight: 600,
                    textTransform: "uppercase",
                  }}>
                    {info.status}
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: 1.5 }}>
                  <div>{info.description}</div>
                  <div style={{ marginTop: "0.25rem" }}>
                    <span style={{ color: "#94a3b8" }}>条件：</span>{info.condition}
                  </div>
                  <div>
                    <span style={{ color: "#94a3b8" }}>产物：</span>{info.outputs}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {selectedRoutes.includes("tts_subtitle_compose") && (
          <div style={{
            background: "#fef3c7",
            border: "1px solid #fcd34d",
            borderRadius: "8px",
            padding: "0.75rem 1rem",
            fontSize: "0.8rem",
            color: "#92400e",
            marginBottom: "1rem",
          }}>
            ⚠️ TTS 路线会调用 MiniMax API，可能产生费用。已确认配置了 <code>MINIMAX_API_KEY</code>。
          </div>
        )}

        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <button
            onClick={runSelected}
            disabled={isRunning || selectedRoutes.length === 0}
            style={{
              background: isRunning ? "#93c5fd" : "#3b82f6",
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "0.6rem 1.5rem",
              fontSize: "0.9rem",
              cursor: isRunning || selectedRoutes.length === 0 ? "not-allowed" : "pointer",
            }}
          >
            {isRunning ? "运行中..." : `运行已选路线 (${selectedRoutes.length} 条)`}
          </button>
          <button
            onClick={() => {
              setSelectedRoutes(
                Object.entries(ROUTE_INFO)
                  .filter(([, i]) => i.defaultSelected)
                  .map(([id]) => id)
              );
            }}
            style={{ background: "none", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "0.6rem 1rem", fontSize: "0.85rem", cursor: "pointer" }}
          >
            恢复默认选择
          </button>
        </div>

        {error && (
          <div style={{ marginTop: "1rem", color: "#ef4444", fontSize: "0.85rem" }}>错误：{error}</div>
        )}
      </div>

      {/* Results */}
      {results && (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>
              运行结果 {benchmarkId && <span style={{ fontWeight: 400, fontSize: "0.8rem", color: "#94a3b8" }}>#{benchmarkId}</span>}
            </h2>
            <button
              onClick={() => {
                setExportText(exportMarkdown());
                setShowExport(true);
              }}
              style={{ background: "#10b981", color: "white", border: "none", borderRadius: "8px", padding: "0.5rem 1rem", fontSize: "0.85rem", cursor: "pointer" }}
            >
              导出 Markdown 对比报告
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
            {results.map((r) => {
              const info = ROUTE_INFO[r.routeId];
              const color = STATUS_COLOR[info?.status ?? "mock"];
              const score = scores[r.routeId];
              const htmlUrl = getArtifactUrl(r.artifacts, "htmlUrl");
              const audioUrl = getArtifactUrl(r.artifacts, "audioUrl");
              const srtUrl = getArtifactUrl(r.artifacts, "srtUrl");
              const ratedDims = score ? Object.entries(score.scores).filter(([, v]) => v !== null) : [];
              const avgScore = ratedDims.length > 0
                ? (ratedDims.reduce((a, [, v]) => a + (v as number), 0) / ratedDims.length).toFixed(1)
                : null;

              return (
                <div key={r.routeId} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "1rem" }}>
                  {/* Header */}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                    <span style={{
                      background: `${color}15`,
                      color,
                      borderRadius: "4px",
                      padding: "0.1rem 0.4rem",
                      fontSize: "0.7rem",
                      fontWeight: 600,
                      textTransform: "uppercase",
                    }}>
                      {r.status}
                    </span>
                    <strong style={{ fontSize: "0.9rem" }}>{info?.name ?? r.routeId}</strong>
                    {avgScore && (
                      <span style={{ marginLeft: "auto", fontSize: "0.8rem", fontWeight: 600, color }}>
                        ⭐ {avgScore}
                      </span>
                    )}
                  </div>

                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.75rem", lineHeight: 1.5 }}>
                    {info?.description}
                  </div>

                  {/* Video player */}
                  {r.status === "succeeded" && r.videoUrl && (
                    <div style={{ marginBottom: "0.75rem" }}>
                      <video
                        controls
                        src={r.videoUrl}
                        style={{ width: "100%", maxHeight: "160px", borderRadius: "6px", background: "#0f172a", objectFit: "contain" }}
                      />
                    </div>
                  )}

                  {/* Artifact links */}
                  {(r.status === "manual" || r.status === "succeeded") && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
                      {htmlUrl && (
                        <a href={htmlUrl} target="_blank" rel="noopener noreferrer"
                          style={{ fontSize: "0.75rem", color: "#8b5cf6", textDecoration: "none", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                          🎬 打开 HTML
                        </a>
                      )}
                      {audioUrl && (
                        <a href={audioUrl} target="_blank" rel="noopener noreferrer"
                          style={{ fontSize: "0.75rem", color: "#10b981", textDecoration: "none", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                          🔊 播放音频
                        </a>
                      )}
                      {srtUrl && (
                        <a href={srtUrl} target="_blank" rel="noopener noreferrer"
                          style={{ fontSize: "0.75rem", color: "#f59e0b", textDecoration: "none", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                          📝 打开字幕
                        </a>
                      )}
                      {r.manifestUrl && (
                        <a href={r.manifestUrl} target="_blank" rel="noopener noreferrer"
                          style={{ fontSize: "0.75rem", color: "#3b82f6", textDecoration: "none" }}>
                          📋 manifest
                        </a>
                      )}
                    </div>
                  )}

                  {/* Manual instructions */}
                  {r.status === "manual" && htmlUrl && (
                    <div style={{ background: "#f3e8ff", borderRadius: "6px", padding: "0.5rem 0.75rem", fontSize: "0.75rem", color: "#7c3aed", marginBottom: "0.75rem" }}>
                      ① 打开 HTML → ② 复制源码 → ③ 粘贴到 HeyGen HyperFrames → ④ 渲染视频
                    </div>
                  )}

                  {/* Warnings / failures */}
                  {r.warnings?.length > 0 && (
                    <div style={{ fontSize: "0.75rem", color: "#ef4444", marginBottom: "0.75rem" }}>
                      {r.warnings.map((w, i) => <div key={i}>⚠️ {w}</div>)}
                    </div>
                  )}

                  {/* Scoring */}
                  {(r.status === "succeeded" || r.status === "manual") && (
                    <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "0.75rem" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.5rem", color: "#475569" }}>评分</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
                        {SCORE_DIMENSIONS.map((dim) => (
                          <div key={dim.key} style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                            <span style={{ fontSize: "0.7rem", color: "#94a3b8", width: "4rem", flexShrink: 0 }}>{dim.label}</span>
                            <select
                              value={score?.scores[dim.key] ?? ""}
                              onChange={(e) => updateScore(r.routeId, dim.key, e.target.value ? Number(e.target.value) : null)}
                              style={{ fontSize: "0.75rem", border: "1px solid #e2e8f0", borderRadius: "4px", padding: "0.1rem 0.25rem" }}
                            >
                              <option value="">-</option>
                              {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>{v}</option>)}
                            </select>
                          </div>
                        ))}
                      </div>
                      <textarea
                        placeholder="一句话结论..."
                        value={score?.conclusion ?? ""}
                        onChange={(e) => setScores((prev) => ({
                          ...prev,
                          [r.routeId]: { ...prev[r.routeId], conclusion: e.target.value },
                        }))}
                        rows={2}
                        style={{ width: "100%", marginTop: "0.5rem", fontSize: "0.75rem", border: "1px solid #e2e8f0", borderRadius: "6px", padding: "0.4rem", resize: "none" }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Markdown export modal */}
      {showExport && (
        <div style={{
          position: "fixed", inset: 0,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 100,
        }}
          onClick={() => setShowExport(false)}
        >
          <div style={{
            background: "white",
            borderRadius: "12px",
            padding: "1.5rem",
            width: "90%",
            maxWidth: "800px",
            maxHeight: "80vh",
            display: "flex",
            flexDirection: "column",
          }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>Markdown 对比报告</h3>
              <button onClick={() => {
                navigator.clipboard.writeText(exportText).then(() => alert("已复制到剪贴板"));
              }}
                style={{ background: "#3b82f6", color: "white", border: "none", borderRadius: "6px", padding: "0.4rem 1rem", fontSize: "0.85rem", cursor: "pointer" }}>
                复制到剪贴板
              </button>
            </div>
            <textarea
              value={exportText}
              readOnly
              style={{
                flex: 1,
                width: "100%",
                fontFamily: "monospace",
                fontSize: "0.8rem",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "0.75rem",
                resize: "none",
                boxSizing: "border-box",
              }}
            />
            <button
              onClick={() => setShowExport(false)}
              style={{ marginTop: "1rem", background: "#e2e8f0", border: "none", borderRadius: "6px", padding: "0.5rem", cursor: "pointer", fontSize: "0.85rem" }}
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
