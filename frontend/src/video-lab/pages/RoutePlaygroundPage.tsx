// RoutePlaygroundPage - V0.3.4.1: Complete video generation chain testing interface
// Path: /video-lab/route-playground

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const DEFAULT_CONTENT = `今天有三条 AI 动态值得关注。

第一，OpenAI 发布新的推理模型能力，重点提升复杂任务分解和工具调用稳定性。

第二，Anthropic 更新 Claude Code 相关能力，进一步强化开发者在代码审查，重构和自动化任务中的使用体验。

第三，HeyGen 推出 HyperFrames 能力，可以通过 HTML 生成视频，为程序化视频制作提供了新的路线。

这三条信息共同说明，AI 视频和 AI Agent 正在从单点能力走向可组合的工作流。`;

const CHAIN_INFO: Record<string, {
  name: string;
  generationMode: "auto" | "manual";
  description: string;
  visualSource: string;
  audioSource: string;
  subtitleMode: string;
  requiresTts: boolean;
  defaultSelected: boolean;
}> = {
  local_frame_tts_video: {
    name: "本地帧 TTS 视频",
    generationMode: "auto",
    description: "Pillow 画面 + MiniMax TTS + SRT 字幕 + FFmpeg 合成",
    visualSource: "Pillow 静态卡片帧",
    audioSource: "MiniMax TTS",
    subtitleMode: "SRT",
    requiresTts: true,
    defaultSelected: true,
  },
  remotion_tts_video: {
    name: "Remotion TTS 视频",
    generationMode: "auto",
    description: "Remotion 动态模板 + MiniMax TTS + SRT 字幕 + FFmpeg 合成",
    visualSource: "Remotion React 模板",
    audioSource: "MiniMax TTS",
    subtitleMode: "SRT",
    requiresTts: true,
    defaultSelected: true,
  },
  hyperframes_tts_video: {
    name: "HyperFrames HTML 视频",
    generationMode: "manual",
    description: "生成 HTML 页面，人工复制到 HeyGen HyperFrames 渲染",
    visualSource: "HyperFrames HTML",
    audioSource: "需人工指定",
    subtitleMode: "需人工指定",
    requiresTts: false,
    defaultSelected: true,
  },
};

const STATUS_COLOR: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  manual_required: "#8b5cf6",
  incomplete: "#f59e0b",
  skipped: "#94a3b8",
};

const SCORE_DIMENSIONS = [
  { key: "informationAccuracy", label: "信息准确性" },
  { key: "visualQuality", label: "画面质量" },
  { key: "audioNaturalness", label: "声音自然度" },
  { key: "readability", label: "字幕可读性" },
  { key: "pacing", label: "节奏感" },
  { key: "completeness", label: "完整度" },
  { key: "automationStability", label: "自动化稳定性" },
  { key: "costControllability", label: "成本可控性" },
  { key: "productizationPotential", label: "产品化潜力" },
];

interface ChainScore {
  chainId: string;
  scores: Record<string, number | null>;
  notes: string;
  conclusion: string;
}

interface ChainResult {
  chainId: string;
  chainName: string;
  status: string;
  finalVideoUrl: string;
  htmlUrl: string;
  hasVisual: boolean;
  hasAudio: boolean;
  hasReadableText: boolean;
  audioUrl: string;
  srtUrl: string;
  manifestUrl: string;
  failedStep: string;
  failedReason: string;
  visualSource: string;
  audioSource: string;
  subtitleMode: string;
  logs: string[];
  warnings: string[];
  elapsedMs: number;
  createdAt: string;
}

interface BenchmarkResult {
  chainId: string;
  status: string;
  finalVideoUrl: string;
  htmlUrl: string;
  hasVisual: boolean;
  hasAudio: boolean;
  hasReadableText: boolean;
  audioUrl: string;
  srtUrl: string;
  manifestUrl: string;
  failedStep: string;
  failedReason: string;
  visualSource: string;
  audioSource: string;
  subtitleMode: string;
  logs: string[];
  warnings: string[];
  elapsedMs: number;
}

export default function RoutePlaygroundPage() {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [selectedChains, setSelectedChains] = useState<string[]>(
    Object.entries(CHAIN_INFO)
      .filter(([, info]) => info.defaultSelected)
      .map(([id]) => id)
  );
  const [ttsConfirmed, setTtsConfirmed] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<BenchmarkResult[] | null>(null);
  const [benchmarkId, setBenchmarkId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [scores, setScores] = useState<Record<string, ChainScore>>({});

  const toggleChain = (id: string) => {
    setSelectedChains((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  };

  const hasTtsChainSelected = selectedChains.some(
    (id) => CHAIN_INFO[id]?.requiresTts
  );

  const canRun = selectedChains.length > 0 && (!hasTtsChainSelected || ttsConfirmed);

  const runSelected = async () => {
    if (!canRun) {
      if (!ttsConfirmed && hasTtsChainSelected) {
        setError("请先确认 TTS 成本提示，才能运行带 TTS 的链路");
      } else {
        setError("请至少选择一条链路");
      }
      return;
    }
    setIsRunning(true);
    setError("");
    setResults(null);

    try {
      const payload = {
        testCaseId: "case_ai_frontier_daily_001",
        title: "完整链路测试台 - " + new Date().toLocaleDateString("zh-CN"),
        inputPayload: { content },
        commonParams: {
          targetDuration: 45,
          aspectRatio: "9:16",
          keyPointCount: 3,
        },
        chainIds: selectedChains,
      };

      const resp = await fetch(`${API_BASE}/chain-benchmarks`, {
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
      const newScores: Record<string, ChainScore> = {};
      for (const r of data.results ?? []) {
        newScores[r.chainId] = {
          chainId: r.chainId,
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

  const updateScore = (chainId: string, dim: string, val: number | null) => {
    setScores((prev) => ({
      ...prev,
      [chainId]: {
        ...prev[chainId],
        scores: { ...prev[chainId].scores, [dim]: val },
      },
    }));
  };

  const statusLabel = (status: string) => {
    switch (status) {
      case "succeeded": return "✅ 成功";
      case "failed": return "❌ 失败";
      case "manual_required": return "⚠️ 需人工";
      case "incomplete": return "⏳ 不完整";
      case "skipped": return "⊘ 跳过";
      default: return status;
    }
  };

  const exportMarkdown = (): string => {
    if (!results) return "";
    const lines = [
      "# V0.3 完整视频生成链路对比报告",
      "",
      "## 测试输入",
      "",
      "```",
      content.slice(0, 200) + (content.length > 200 ? "..." : ""),
      "```",
      "",
      "## 参与链路",
      "",
      ...selectedChains.map((id) => `- ${CHAIN_INFO[id]?.name ?? id} (${id})`),
      "",
    ];

    for (const r of results) {
      const info = CHAIN_INFO[r.chainId];
      const score = scores[r.chainId];
      const ratedDims = score ? Object.entries(score.scores).filter(([, v]) => v !== null) : [];
      const avgScore = ratedDims.length > 0
        ? (ratedDims.reduce((a, [, v]) => a + (v as number), 0) / ratedDims.length).toFixed(1)
        : "待评分";

      lines.push(`## ${info?.name ?? r.chainId}`);
      lines.push(`- **chainId**: ${r.chainId}`);
      lines.push(`- **画面来源**: ${r.visualSource || info?.visualSource || "-"}`);
      lines.push(`- **音频来源**: ${r.audioSource || info?.audioSource || "-"}`);
      lines.push(`- **字幕方式**: ${r.subtitleMode || info?.subtitleMode || "-"}`);
      lines.push(`- **状态**: ${statusLabel(r.status)}`);
      lines.push(`- **是否生成最终视频**: ${r.status === "succeeded" ? "✅ 是" : r.status === "manual_required" ? "⚠️ 需人工" : r.status === "failed" ? "❌ 否" : "⏳ 待验证"}`);
      lines.push(`- **finalVideoUrl**: ${r.finalVideoUrl || "(无)"}`);
      if (r.status === "manual_required") lines.push(`- **htmlUrl**: ${r.htmlUrl || "-"}`);
      if (r.audioUrl) lines.push(`- **audioUrl**: ${r.audioUrl}`);
      if (r.srtUrl) lines.push(`- **srtUrl**: ${r.srtUrl}`);
      if (r.failedStep) lines.push(`- **failedStep**: ${r.failedStep}`);
      if (r.failedReason) lines.push(`- **失败原因**: ${r.failedReason}`);
      if (r.warnings?.length) lines.push(`- **warnings**: ${r.warnings.join("; ")}`);
      lines.push(`- **综合评分**: ${avgScore}`);
      if (score?.conclusion) lines.push(`- **结论**: ${score.conclusion}`);
      lines.push("");
    }

    lines.push("## 横向评分表");
    lines.push("");
    lines.push("| 链路 | " + SCORE_DIMENSIONS.map((d) => d.label).join(" | ") + " |");
    lines.push("|" + "---|".repeat(SCORE_DIMENSIONS.length + 1));
    for (const r of results) {
      const score = scores[r.chainId];
      const chainInfo = CHAIN_INFO[r.chainId];
      const row = [chainInfo?.name ?? r.chainId];
      for (const dim of SCORE_DIMENSIONS) {
        const val = score?.scores[dim.key];
        row.push(val != null ? String(val) : "-");
      }
      lines.push("| " + row.join(" | ") + " |");
    }
    lines.push("");
    lines.push("## 当前判断");
    lines.push("");
    lines.push("- 当前最佳完整链路：（待评分）");
    lines.push("- hyperframes_tts_video 需人工操作，暂不参与自动评分");
    lines.push("");
    lines.push("## 下一步建议");
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
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "0.5rem" }}>完整视频链路测试台</h1>
        <p style={{ color: "#64748b", fontSize: "0.9rem", marginTop: "0.25rem" }}>
          对比完整视频生成链路，每条链路必须以最终 MP4 成片为准
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

      {/* Chain selection */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "1rem" }}>选择要测试的完整链路</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem", marginBottom: "1rem" }}>
          {Object.entries(CHAIN_INFO).map(([id, info]) => {
            const checked = selectedChains.includes(id);
            const color = info.generationMode === "manual" ? "#8b5cf6" : "#10b981";
            return (
              <div
                key={id}
                onClick={() => toggleChain(id)}
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
                    {info.generationMode}
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: 1.6 }}>
                  <div>{info.description}</div>
                  <div style={{ marginTop: "0.25rem" }}>
                    <span style={{ color: "#94a3b8" }}>画面：</span>{info.visualSource}
                  </div>
                  <div>
                    <span style={{ color: "#94a3b8" }}>音频：</span>{info.audioSource}
                  </div>
                  <div>
                    <span style={{ color: "#94a3b8" }}>字幕：</span>{info.subtitleMode}
                  </div>
                  {info.requiresTts && (
                    <div style={{ color: "#f59e0b", marginTop: "0.25rem" }}>
                      🔊 调用 TTS
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* TTS Cost Confirmation */}
        {hasTtsChainSelected && (
          <div style={{
            background: "#fef3c7",
            border: "1px solid #fcd34d",
            borderRadius: "8px",
            padding: "0.75rem 1rem",
            fontSize: "0.8rem",
            color: "#92400e",
            marginBottom: "1rem",
          }}>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={ttsConfirmed}
                onChange={(e) => setTtsConfirmed(e.target.checked)}
                style={{ width: 16, height: 16 }}
              />
              本次会调用 MiniMax TTS，可能产生 API 成本。确认运行带 TTS 的完整成片链路。
            </label>
          </div>
        )}

        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <button
            onClick={runSelected}
            disabled={isRunning || !canRun}
            style={{
              background: isRunning ? "#93c5fd" : (!canRun ? "#cbd5e1" : "#3b82f6"),
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "0.6rem 1.5rem",
              fontSize: "0.9rem",
              cursor: isRunning || !canRun ? "not-allowed" : "pointer",
            }}
          >
            {isRunning ? "运行中..." : `运行已选链路 (${selectedChains.length} 条)`}
          </button>
          <button
            onClick={() => {
              setSelectedChains(
                Object.entries(CHAIN_INFO)
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

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
            {results.map((r) => {
              const info = CHAIN_INFO[r.chainId];
              const color = STATUS_COLOR[r.status] ?? "#94a3b8";
              const score = scores[r.chainId];
              const ratedDims = score ? Object.entries(score.scores).filter(([, v]) => v !== null) : [];
              const avgScore = ratedDims.length > 0
                ? (ratedDims.reduce((a, [, v]) => a + (v as number), 0) / ratedDims.length).toFixed(1)
                : null;

              return (
                <div key={r.chainId} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "1rem" }}>
                  {/* Header */}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem", flexWrap: "wrap" }}>
                    <span style={{
                      background: `${color}15`,
                      color,
                      borderRadius: "4px",
                      padding: "0.1rem 0.4rem",
                      fontSize: "0.7rem",
                      fontWeight: 600,
                    }}>
                      {statusLabel(r.status)}
                    </span>
                    <strong style={{ fontSize: "0.9rem" }}>{info?.name ?? r.chainId}</strong>
                    {avgScore && (
                      <span style={{ marginLeft: "auto", fontSize: "0.8rem", fontWeight: 600, color }}>
                        ⭐ {avgScore}
                      </span>
                    )}
                  </div>

                  {/* Chain metadata */}
                  <div style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: "0.75rem", lineHeight: 1.6 }}>
                    <div><span style={{ color: "#94a3b8" }}>画面：</span>{r.visualSource || info?.visualSource}</div>
                    <div><span style={{ color: "#94a3b8" }}>音频：</span>{r.audioSource || info?.audioSource}</div>
                    <div><span style={{ color: "#94a3b8" }}>字幕：</span>{r.subtitleMode || info?.subtitleMode}</div>
                    {r.failedStep && <div style={{ color: "#ef4444" }}>失败步骤：{r.failedStep}</div>}
                    {r.failedReason && <div style={{ color: "#ef4444", fontSize: "0.7rem" }}>{r.failedReason}</div>}
                  </div>

                  {/* Final video player */}
                  {r.status === "succeeded" && r.finalVideoUrl && (
                    <div style={{ marginBottom: "0.75rem" }}>
                      <div style={{ fontSize: "0.7rem", color: "#10b981", marginBottom: "0.25rem", fontWeight: 600 }}>最终成片</div>
                      <video
                        controls
                        src={r.finalVideoUrl}
                        style={{ width: "100%", maxHeight: "160px", borderRadius: "6px", background: "#0f172a", objectFit: "contain" }}
                      />
                    </div>
                  )}

                  {/* Manual required instructions */}
                  {r.status === "manual_required" && r.htmlUrl && (
                    <div style={{ background: "#f3e8ff", borderRadius: "6px", padding: "0.5rem 0.75rem", fontSize: "0.75rem", color: "#7c3aed", marginBottom: "0.75rem" }}>
                      ① 打开 HTML → ② 复制源码 → ③ 粘贴到 HeyGen HyperFrames → ④ 渲染视频
                      <br />
                      <a href={r.htmlUrl} target="_blank" rel="noopener noreferrer" style={{ color: "#8b5cf6" }}>
                        🔗 打开生成的 HTML
                      </a>
                    </div>
                  )}

                  {/* Intermediate artifact links */}
                  {(r.status === "succeeded" || r.status === "manual_required") && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
                      {r.audioUrl && (
                        <a href={r.audioUrl} target="_blank" rel="noopener noreferrer"
                          style={{ fontSize: "0.75rem", color: "#10b981", textDecoration: "none", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                          🔊 播放音频
                        </a>
                      )}
                      {r.srtUrl && (
                        <a href={r.srtUrl} target="_blank" rel="noopener noreferrer"
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

                  {/* Flags: hasVisual, hasAudio, hasReadableText */}
                  <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem", fontSize: "0.75rem" }}>
                    <span style={{ color: r.hasVisual ? "#10b981" : "#ef4444" }}>
                      {r.hasVisual ? "✅ 有画面" : "❌ 无画面"}
                    </span>
                    <span style={{ color: r.hasAudio ? "#10b981" : "#ef4444" }}>
                      {r.hasAudio ? "✅ 有音频" : "❌ 无音频"}
                    </span>
                    <span style={{ color: r.hasReadableText ? "#10b981" : "#ef4444" }}>
                      {r.hasReadableText ? "✅ 有字幕" : "❌ 无字幕"}
                    </span>
                  </div>

                  {/* Warnings */}
                  {r.warnings?.length > 0 && (
                    <div style={{ fontSize: "0.75rem", color: "#ef4444", marginBottom: "0.75rem" }}>
                      {r.warnings.map((w, i) => <div key={i}>⚠️ {w}</div>)}
                    </div>
                  )}

                  {/* Scoring */}
                  {(r.status === "succeeded" || r.status === "manual_required") && (
                    <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "0.75rem" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.5rem", color: "#475569" }}>评分</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
                        {SCORE_DIMENSIONS.map((dim) => (
                          <div key={dim.key} style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                            <span style={{ fontSize: "0.7rem", color: "#94a3b8", width: "4.5rem", flexShrink: 0, overflow: "hidden", textOverflow: "ellipsis" }}>{dim.label}</span>
                            <select
                              value={score?.scores[dim.key] ?? ""}
                              onChange={(e) => updateScore(r.chainId, dim.key, e.target.value ? Number(e.target.value) : null)}
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
                          [r.chainId]: { ...prev[r.chainId], conclusion: e.target.value },
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
            maxWidth: "900px",
            maxHeight: "80vh",
            display: "flex",
            flexDirection: "column",
          }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>Markdown 完整链路对比报告</h3>
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
