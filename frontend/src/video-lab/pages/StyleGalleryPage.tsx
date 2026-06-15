/**
 * StyleGalleryPage.tsx - 路线风格样片库
 * Path: /video-lab/style-gallery
 * V0.3.7: 风格样片库 — 每条路线独立风格探索，无数据库，JSONL 存储
 */

import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

// ─── 类型 ────────────────────────────────────────────────────────────────────

interface PresetStyle {
  route_id: string;
  route_name: string;
  style_id: string;
  style_name: string;
  description: string;
  capabilities: string[];
  tags: string[];
  params: Record<string, unknown>;
}

interface SampleOutput {
  type: string;
  path: string;
  poster: string;
  audio_url: string;
  srt_url: string;
  manifest_url: string;
}

interface SampleUrls {
  video_url: string;
  poster_url: string;
  audio_url: string;
  srt_url: string;
  manifest_url: string;
}

interface Evaluation {
  readability: number | null;
  motion: number | null;
  visual_impact: number | null;
  stability: number | null;
  cost: number | null;
  notes: string;
}

interface VisualJudgement {
  score: number;
  grade: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  judged_at: string;
  dimensions: Record<string, number>;
}

interface StyleSample {
  id: string;
  route_id: string;
  route_name: string;
  style_name: string;
  description: string;
  status: string;
  params: Record<string, unknown>;
  output: SampleOutput;
  urls: SampleUrls;
  evaluation: Evaluation;
  tags: string[];
  content_preview: string;
  duration_sec: number;
  audio_duration_sec: number;
  created_at: string;
  visual_judgement: VisualJudgement | null;
}

interface GenerateResult {
  sample_id: string;
  route_id: string;
  style_name: string;
  description: string;
  status: string;
  params: Record<string, unknown>;
  output: SampleOutput;
  duration_sec: number;
  audio_duration_sec: number;
  content_preview: string;
  final_video_url: string;
  cover_url: string;
  audio_url: string;
  srt_url: string;
  manifest_url: string;
  failed: boolean;
  failed_reason: string;
}

// V0.4.2: Style Template
interface RouteScoreSummary {
  routeName: string;
  latest: number | null;
  previous: number | null;
  delta: number | null;
  average: number | null;
  count: number;
}

interface StyleTemplate {
  id: string;
  name: string;
  route_id: string;
  route_name: string;
  style_name: string;
  description: string;
  params: Record<string, unknown>;
  source_sample_id: string;
  source_sample_score: number | null;
  visual_judgement: VisualJudgement | null;
  tags: string[];
  created_at: string;
  warnings?: string[];
}

// ─── 工具 ────────────────────────────────────────────────────────────────────

const resolveUrl = (u: string) =>
  u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u;

interface BgmInfo {
  enabled: boolean;
  mode: string;
  volume: number;
}

const getBgmInfo = (params: Record<string, unknown>): BgmInfo => {
  const bgm = params.bgm as Record<string, unknown> | undefined;
  if (bgm && typeof bgm === "object") {
    const mode = String(bgm.mode || "none");
    return {
      enabled: mode !== "none",
      mode,
      volume: Number(bgm.volume || 0.06),
    };
  }
  // Flat format compatibility
  const mode = String(params.bgmMode || "none");
  return {
    enabled: mode !== "none",
    mode,
    volume: Number(params.bgmVolume || 0.06),
  };
};

// V0.4.1: Extract key params summary by route
function getKeyParamsSummary(params: Record<string, unknown>, routeId: string): string[] {
  const summaries: string[] = [];
  if (routeId === "local_frame_compose") {
    if (params.showDataViz !== undefined) summaries.push(`数据可视化: ${params.showDataViz ? "开" : "关"}`);
    if (params.highlightMode) summaries.push(`高亮模式: ${params.highlightMode}`);
    if (params.contentAlign) summaries.push(`内容对齐: ${params.contentAlign}`);
    if (params.transitionEnabled !== undefined) summaries.push(`转场: ${params.transitionEnabled ? "开" : "关"}`);
    if (params.themeAdaptive !== undefined) summaries.push(`主题自适应: ${params.themeAdaptive ? "是" : "否"}`);
  } else if (routeId === "template_programmatic_render") {
    if (params.motionIntensity) summaries.push(`动效强度: ${params.motionIntensity}`);
    if (params.coverStyle) summaries.push(`封面风格: ${params.coverStyle}`);
    if (params.overviewStyle) summaries.push(`概览风格: ${params.overviewStyle}`);
    if (params.metricAnimation) summaries.push(`指标动画: ${params.metricAnimation}`);
    if (params.transitionStyle) summaries.push(`转场: ${params.transitionStyle}`);
    const bgm = getBgmInfo(params);
    if (bgm.enabled) summaries.push(`BGM: ${bgm.mode}`);
  } else if (routeId === "ai_asset_then_compose") {
    if (params.imageStyle) summaries.push(`图像风格: ${params.imageStyle}`);
    if (params.backgroundDarken !== undefined) summaries.push(`背景减暗: ${params.backgroundDarken}`);
    if (params.cardOpacity !== undefined) summaries.push(`卡片透明度: ${params.cardOpacity}`);
    if (params.kenBurns !== undefined) summaries.push(`Ken Burns: ${params.kenBurns ? "开" : "关"}`);
    const bgm = getBgmInfo(params);
    if (bgm.enabled) summaries.push(`BGM: ${bgm.mode}`);
  }
  return summaries;
}

const ROUTE_COLORS: Record<string, string> = {
  local_frame_compose: "#0ea5e9",
  template_programmatic_render: "#8b5cf6",
  ai_asset_then_compose: "#10b981",
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  candidate: { label: "候选中", color: "#f59e0b" },
  approved: { label: "已确认", color: "#10b981" },
  rejected: { label: "已放弃", color: "#ef4444" },
  comparing: { label: "对比中", color: "#3b82f6" },
};

const EVAL_KEYS = ["readability", "motion", "visual_impact", "stability", "cost"] as const;
type EvalKey = typeof EVAL_KEYS[number];

const EVAL_LABELS: Record<EvalKey, string> = {
  readability: "可读性",
  motion: "动态感",
  visual_impact: "视觉冲击",
  stability: "稳定性",
  cost: "成本",
};

// ─── 星级组件 ────────────────────────────────────────────────────────────────

function StarRating({ value, onChange }: { value: number | null; onChange: (v: number) => void }) {
  return (
    <div style={{ display: "flex", gap: 2 }}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          onClick={() => onChange(n)}
          style={{
            cursor: "pointer",
            fontSize: "1rem",
            color: n <= (value ?? 0) ? "#f59e0b" : "#e2e8f0",
          }}
        >
          ★
        </span>
      ))}
    </div>
  );
}

// ─── 预置风格卡片 ────────────────────────────────────────────────────────────

function PresetStyleCard({
  preset,
  onGenerate,
  generating,
}: {
  preset: PresetStyle;
  onGenerate: (p: PresetStyle) => void;
  generating: boolean;
}) {
  const color = ROUTE_COLORS[preset.route_id] ?? "#64748b";
  return (
    <div
      style={{
        background: "white",
        border: `1px solid ${color}30`,
        borderRadius: 12,
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.5rem" }}>
        <div>
          <div style={{ fontSize: "0.8rem", fontWeight: 700, color: color }}>{preset.style_name}</div>
          <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: 2 }}>{preset.route_name}</div>
        </div>
        <span style={{
          fontSize: "0.65rem",
          background: `${color}15`,
          color: color,
          borderRadius: 10,
          padding: "2px 8px",
          whiteSpace: "nowrap",
        }}>
          {preset.route_id === "local_frame_compose" ? "Pillow" : preset.route_id === "template_programmatic_render" ? "Remotion" : "AI素材"}
        </span>
      </div>

      <p style={{ fontSize: "0.72rem", color: "#475569", margin: 0, lineHeight: 1.5 }}>
        {preset.description}
      </p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
        {preset.capabilities.map((c) => (
          <span key={c} style={{
            fontSize: "0.62rem",
            background: "#f1f5f9",
            color: "#475569",
            borderRadius: 6,
            padding: "1px 6px",
          }}>
            {c}
          </span>
        ))}
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", marginTop: "auto", paddingTop: "0.5rem" }}>
        {preset.tags.map((t) => (
          <span key={t} style={{
            fontSize: "0.62rem",
            background: `${color}10`,
            color: color,
            borderRadius: 6,
            padding: "1px 6px",
          }}>
            #{t}
          </span>
        ))}
      </div>

      <button
        onClick={() => onGenerate(preset)}
        disabled={generating}
        style={{
          background: generating ? "#94a3b8" : color,
          color: "white",
          border: "none",
          borderRadius: 8,
          padding: "0.45rem",
          fontSize: "0.8rem",
          cursor: generating ? "wait" : "pointer",
          marginTop: "0.25rem",
        }}
      >
        {generating ? "生成中..." : "▶ 生成样片"}
      </button>
      {!generating && (
        <div style={{ fontSize: "0.6rem", color: "#94a3b8", marginTop: "0.2rem" }}>
          生成完整样片，可能耗时较长，并消耗 TTS / AI 图像额度
        </div>
      )}
    </div>
  );
}

// ─── 样片卡片 ────────────────────────────────────────────────────────────────

function SampleCard({
  sample,
  onDelete,
  onCompare,
  onSave,
  selectedForCompare,
  onJudge,
  judging,
  onPromote,
}: {
  sample: StyleSample;
  onDelete: (id: string) => void;
  onCompare: (id: string) => void;
  onSave: (s: StyleSample) => void;
  selectedForCompare: boolean;
  onJudge: (id: string) => void;
  judging: boolean;
  onPromote: (id: string) => void;
}) {
  const color = ROUTE_COLORS[sample.route_id] ?? "#64748b";
  const statusInfo = STATUS_LABELS[sample.status] ?? STATUS_LABELS.candidate;
  const videoSrc = resolveUrl(sample.urls.video_url || sample.output.path);
  const posterSrc = resolveUrl(sample.urls.poster_url || sample.output.poster);

  return (
    <div
      style={{
        background: "white",
        border: `1px solid ${selectedForCompare ? "#3b82f6" : "#e2e8f0"}`,
        borderRadius: 12,
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.6rem",
      }}
    >
      {/* 头部 */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
        <div>
          <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b" }}>{sample.style_name}</div>
          <div style={{ fontSize: "0.68rem", color: "#64748b" }}>{sample.route_name}</div>
        </div>
        <span style={{
          fontSize: "0.65rem",
          background: `${statusInfo.color}15`,
          color: statusInfo.color,
          borderRadius: 10,
          padding: "2px 8px",
        }}>
          {statusInfo.label}
        </span>
      </div>

      {/* 预览 */}
      {videoSrc ? (
        <div style={{ background: "#0f172a", borderRadius: 8, overflow: "hidden" }}>
          <video
            controls
            playsInline
            muted
            src={videoSrc}
            poster={posterSrc}
            style={{ width: "100%", display: "block", maxHeight: 200, objectFit: "cover" }}
          />
        </div>
      ) : posterSrc ? (
        <img src={posterSrc} alt={sample.style_name} style={{ width: "100%", borderRadius: 8 }} />
      ) : (
        <div style={{ background: "#f1f5f9", borderRadius: 8, height: 120, display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8", fontSize: "0.8rem" }}>
          暂无预览
        </div>
      )}

      {/* 描述 */}
      {sample.description && (
        <p style={{ fontSize: "0.72rem", color: "#475569", margin: 0, lineHeight: 1.5 }}>
          {sample.description}
        </p>
      )}

      {/* 评价分 */}
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "#475569", marginBottom: "0.3rem" }}>人工评价</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.25rem" }}>
          {EVAL_KEYS.map((k) => {
            const v = sample.evaluation[k];
            return (
              <div key={k} style={{ fontSize: "0.68rem", color: "#64748b" }}>
                {EVAL_LABELS[k]}: <b style={{ color: v ? "#f59e0b" : "#cbd5e1" }}>{v ?? "-"}</b>
              </div>
            );
          })}
        </div>
        {sample.evaluation.notes && (
          <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "0.25rem", fontStyle: "italic" }}>
            "{sample.evaluation.notes}"
          </div>
        )}
      </div>

      {/* V0.4.0: 视觉评分 */}
      {sample.visual_judgement ? (
        <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.6rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.3rem" }}>
            <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "#475569" }}>视觉评分</div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                color: sample.visual_judgement.score >= 70 ? "#10b981" : sample.visual_judgement.score >= 55 ? "#f59e0b" : "#ef4444",
              }}>
                {sample.visual_judgement.score} / {sample.visual_judgement.grade}
              </span>
            </div>
          </div>
          <div style={{ fontSize: "0.68rem", color: "#64748b", marginBottom: "0.3rem" }}>
            {sample.visual_judgement.summary}
          </div>
          {sample.visual_judgement.strengths.length > 0 && (
            <div style={{ fontSize: "0.65rem", color: "#10b981", marginBottom: "0.15rem" }}>
              ✓ {sample.visual_judgement.strengths.slice(0, 2).join(" · ")}
            </div>
          )}
          {sample.visual_judgement.weaknesses.length > 0 && (
            <div style={{ fontSize: "0.65rem", color: "#ef4444" }}>
              ✗ {sample.visual_judgement.weaknesses.slice(0, 2).join(" · ")}
            </div>
          )}
        </div>
      ) : (
        <button
          onClick={() => onJudge(sample.id)}
          disabled={judging}
          style={{
            background: judging ? "#94a3b8" : "#f0fdf4",
            color: judging ? "#cbd5e1" : "#16a34a",
            border: "1px solid",
            borderColor: judging ? "#e2e8f0" : "#bbf7d0",
            borderRadius: 6,
            padding: "0.4rem 0.75rem",
            fontSize: "0.72rem",
            cursor: judging ? "wait" : "pointer",
            width: "100%",
          }}
        >
          {judging ? "评分中..." : "🔍 视觉评分"}
        </button>
      )}

      {/* 标签 */}
      {(sample.tags.length > 0 || (() => { const b = getBgmInfo(sample.params); return b.enabled; })()) && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
          {sample.tags.map((t) => (
            <span key={t} style={{
              fontSize: "0.62rem",
              background: `${color}10`,
              color: color,
              borderRadius: 6,
              padding: "1px 6px",
            }}>
              #{t}
            </span>
          ))}
          {(() => { const b = getBgmInfo(sample.params); return b.enabled ? (
            <span style={{
              fontSize: "0.62rem",
              background: "#f0fdf4",
              color: "#16a34a",
              borderRadius: 6,
              padding: "1px 6px",
            }}>
              🎵 BGM · {b.mode === "generated_ambient" ? "环境音" : b.mode}
            </span>
          ) : null; })()}
        </div>
      )}

      {/* 参数摘要 */}
      <details>
        <summary style={{ cursor: "pointer", fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>
          查看参数 ({Object.keys(sample.params).length})
        </summary>
        <pre style={{
          fontSize: "0.65rem",
          background: "#f8fafc",
          borderRadius: 6,
          padding: "0.5rem",
          overflow: "auto",
          maxHeight: 150,
          marginTop: "0.4rem",
          color: "#475569",
          fontFamily: "monospace",
        }}>
          {JSON.stringify(sample.params, null, 2)}
        </pre>
      </details>

      {/* 时长 */}
      {sample.duration_sec > 0 && (
        <div style={{ fontSize: "0.68rem", color: "#64748b" }}>
          时长: {Math.round(sample.duration_sec)}s · 音频: {Math.round(sample.audio_duration_sec)}s
        </div>
      )}

      {/* 操作按钮 */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "auto" }}>
        <button
          onClick={() => navigator.clipboard.writeText(JSON.stringify(sample.params, null, 2))}
          style={{
            background: "#f1f5f9",
            color: "#475569",
            border: "none",
            borderRadius: 6,
            padding: "0.35rem 0.75rem",
            fontSize: "0.72rem",
            cursor: "pointer",
          }}
        >
          📋 复制参数
        </button>
        <button
          onClick={() => onCompare(sample.id)}
          style={{
            background: selectedForCompare ? "#3b82f6" : "#f1f5f9",
            color: selectedForCompare ? "white" : "#475569",
            border: "none",
            borderRadius: 6,
            padding: "0.35rem 0.75rem",
            fontSize: "0.72rem",
            cursor: "pointer",
          }}
        >
          {selectedForCompare ? "✓ 已加入对比" : "⚖ 加入对比"}
        </button>
        {/* V0.4.2: 升级为模板按钮 */}
        <button
          onClick={() => onPromote(sample.id)}
          style={{
            background: sample.visual_judgement && sample.visual_judgement.score >= 70 ? "#fef3c7" : "#f1f5f9",
            color: sample.visual_judgement && sample.visual_judgement.score >= 70 ? "#92400e" : "#475569",
            border: sample.visual_judgement && sample.visual_judgement.score >= 70 ? "1px solid #f59e0b" : "none",
            borderRadius: 6,
            padding: "0.35rem 0.75rem",
            fontSize: "0.72rem",
            cursor: "pointer",
          }}
        >
          ⭐ 升级为模板
        </button>
        <button
          onClick={() => onDelete(sample.id)}
          style={{
            background: "#fef2f2",
            color: "#ef4444",
            border: "1px solid #fecaca",
            borderRadius: 6,
            padding: "0.35rem 0.75rem",
            fontSize: "0.72rem",
            cursor: "pointer",
          }}
        >
          🗑 删除记录
        </button>
      </div>
    </div>
  );
}

// V0.4.1: Compare Board Card ────────────────────────────────────────────────

function CompareCard({
  sample,
  onRemove,
  isTopScore,
  onPromote,
}: {
  sample: StyleSample;
  onRemove: (id: string) => void;
  isTopScore: boolean;
  onPromote: (id: string) => void;
}) {
  const color = ROUTE_COLORS[sample.route_id] ?? "#64748b";
  const videoSrc = resolveUrl(sample.urls.video_url || sample.output.path);
  const posterSrc = resolveUrl(sample.urls.poster_url || sample.output.poster);
  const bgmInfo = getBgmInfo(sample.params);
  const keyParams = getKeyParamsSummary(sample.params, sample.route_id);

  return (
    <div
      style={{
        background: isTopScore ? "#fffbeb" : "white",
        border: `2px solid ${isTopScore ? "#f59e0b" : "#e2e8f0"}`,
        borderRadius: 12,
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.6rem",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
        <div>
          <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b" }}>{sample.style_name}</div>
          <div style={{ fontSize: "0.68rem", color: "#64748b" }}>{sample.route_name}</div>
        </div>
        <span style={{
          fontSize: "0.65rem",
          background: `${STATUS_LABELS.comparing.color}15`,
          color: STATUS_LABELS.comparing.color,
          borderRadius: 10,
          padding: "2px 8px",
        }}>
          {STATUS_LABELS.comparing.label}
        </span>
      </div>

      {/* Top score badge */}
      {isTopScore && (
        <div style={{
          background: "#fef3c7",
          border: "1px solid #f59e0b",
          borderRadius: 6,
          padding: "0.3rem 0.6rem",
          fontSize: "0.72rem",
          fontWeight: 700,
          color: "#92400e",
          textAlign: "center",
        }}>
          🏆 当前最高分
        </div>
      )}

      {/* Preview */}
      {videoSrc ? (
        <div style={{ background: "#0f172a", borderRadius: 8, overflow: "hidden" }}>
          <video
            controls
            playsInline
            muted
            src={videoSrc}
            poster={posterSrc}
            style={{ width: "100%", display: "block", maxHeight: 180, objectFit: "cover" }}
          />
        </div>
      ) : posterSrc ? (
        <img src={posterSrc} alt={sample.style_name} style={{ width: "100%", borderRadius: 8 }} />
      ) : (
        <div style={{ background: "#f1f5f9", borderRadius: 8, height: 100, display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8", fontSize: "0.8rem" }}>
          暂无预览
        </div>
      )}

      {/* Visual judgement score */}
      {sample.visual_judgement ? (
        <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.6rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.25rem" }}>
            <span style={{ fontSize: "0.7rem", fontWeight: 600, color: "#475569" }}>视觉评分</span>
            <span style={{
              fontSize: "0.8rem",
              fontWeight: 800,
              color: sample.visual_judgement.score >= 70 ? "#10b981" : sample.visual_judgement.score >= 55 ? "#f59e0b" : "#ef4444",
            }}>
              {sample.visual_judgement.score} / {sample.visual_judgement.grade}
            </span>
          </div>
          <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: "0.25rem" }}>
            {sample.visual_judgement.summary}
          </div>
          {sample.visual_judgement.strengths.length > 0 && (
            <div style={{ fontSize: "0.62rem", color: "#10b981", marginBottom: "0.1rem" }}>
              ✓ {sample.visual_judgement.strengths.slice(0, 2).join(" · ")}
            </div>
          )}
          {sample.visual_judgement.weaknesses.length > 0 && (
            <div style={{ fontSize: "0.62rem", color: "#ef4444" }}>
              ✗ {sample.visual_judgement.weaknesses.slice(0, 2).join(" · ")}
            </div>
          )}
        </div>
      ) : (
        <div style={{ fontSize: "0.68rem", color: "#94a3b8", fontStyle: "italic" }}>
          暂无视觉评分
        </div>
      )}

      {/* Key params summary */}
      {keyParams.length > 0 ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
          {keyParams.map((p) => (
            <span key={p} style={{
              fontSize: "0.6rem",
              background: `${color}10`,
              color: color,
              borderRadius: 4,
              padding: "1px 5px",
            }}>
              {p}
            </span>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: "0.65rem", color: "#94a3b8" }}>暂无关键参数</div>
      )}

      {/* BGM badge */}
      {bgmInfo.enabled && (
        <span style={{
          fontSize: "0.62rem",
          background: "#f0fdf4",
          color: "#16a34a",
          borderRadius: 6,
          padding: "1px 6px",
          width: "fit-content",
        }}>
          🎵 BGM · {bgmInfo.mode === "generated_ambient" ? "环境音" : bgmInfo.mode}
        </span>
      )}

      {/* Action buttons */}
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "auto" }}>
        {/* V0.4.2: 升级为模板 */}
        <button
          onClick={() => onPromote(sample.id)}
          style={{
            background: sample.visual_judgement && sample.visual_judgement.score >= 70 ? "#fef3c7" : "#f1f5f9",
            color: sample.visual_judgement && sample.visual_judgement.score >= 70 ? "#92400e" : "#475569",
            border: sample.visual_judgement && sample.visual_judgement.score >= 70 ? "1px solid #f59e0b" : "none",
            borderRadius: 6,
            padding: "0.35rem 0.75rem",
            fontSize: "0.72rem",
            cursor: "pointer",
            flex: 1,
          }}
        >
          ⭐ 升级为模板
        </button>
        <button
          onClick={() => onRemove(sample.id)}
          style={{
            background: "#fef2f2",
            color: "#ef4444",
            border: "1px solid #fecaca",
            borderRadius: 6,
            padding: "0.35rem 0.75rem",
            fontSize: "0.72rem",
            cursor: "pointer",
            flex: 1,
          }}
        >
          移出对比
        </button>
      </div>
    </div>
  );
}

// ─── 主页面 ──────────────────────────────────────────────────────────────────

export default function StyleGalleryPage() {
  const [presets, setPresets] = useState<PresetStyle[]>([]);
  const [samples, setSamples] = useState<StyleSample[]>([]);
  const [templates, setTemplates] = useState<StyleTemplate[]>([]);
  const [filterRoute, setFilterRoute] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [generating, setGenerating] = useState<string | null>(null);
  const [compareSet, setCompareSet] = useState<Set<string>>(new Set());
  const [judgingSet, setJudgingSet] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [activeTab, setActiveTab] = useState<"presets" | "gallery" | "compare" | "templates">("presets");
  const [scoreSummary, setScoreSummary] = useState<Record<string, RouteScoreSummary>>({});

  const loadPresets = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/style-gallery/preset-styles`);
      if (!resp.ok) throw new Error(`${resp.status}`);
      const data: PresetStyle[] = await resp.json();
      setPresets(data);
    } catch (e) {
      setError("加载预置风格失败: " + String(e));
    }
  }, []);

  const loadSamples = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterRoute) params.set("route_id", filterRoute);
      if (filterStatus) params.set("status", filterStatus);
      const resp = await fetch(`${API_BASE}/style-samples?${params}`);
      if (!resp.ok) throw new Error(`${resp.status}`);
      const data: StyleSample[] = await resp.json();
      setSamples(data);
      // 同步后端 comparing 状态到本地 compareSet
      setCompareSet(new Set(data.filter((s) => s.status === "comparing").map((s) => s.id)));
    } catch (e) {
      setError("加载样片库失败: " + String(e));
    }
  }, [filterRoute, filterStatus]);

  const loadScoreHistory = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/style-gallery/score-history`);
      const data = await resp.json();
      setScoreSummary(data.byRoute ?? {});
    } catch { /* ignore */ }
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/style-templates`);
      if (!resp.ok) throw new Error(`${resp.status}`);
      const data: StyleTemplate[] = await resp.json();
      setTemplates(data);
    } catch (e) {
      setError("加载模板库失败: " + String(e));
    }
  }, []);

  useEffect(() => { loadPresets(); }, [loadPresets]);
  useEffect(() => { loadSamples(); }, [loadSamples]);
  useEffect(() => { loadTemplates(); }, [loadTemplates]);
  useEffect(() => { loadScoreHistory(); }, [loadScoreHistory]);

  // 通用：生成一条样片并自动保存到样片库（预置风格 / 模板复用共用，避免复制粘贴）
  const generateAndSaveSample = async (opts: {
    key: string;            // 用于 generating loading 态
    route_id: string;
    route_name: string;
    style_name: string;
    description: string;
    params: Record<string, unknown>;
    tags: string[];
    successMsg?: string;
  }): Promise<boolean> => {
    setGenerating(opts.key);
    setError("");
    setSuccessMsg("");
    try {
      const resp = await fetch(`${API_BASE}/style-samples/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          style_name: opts.style_name,
          description: opts.description,
          route_id: opts.route_id,
          content: "",
          params: opts.params,
          tags: opts.tags,
        }),
      });
      const data: GenerateResult = await resp.json();
      if (!resp.ok) throw new Error(data.failed_reason || `${resp.status}`);

      // 自动保存到样片库
      await fetch(`${API_BASE}/style-samples`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: data.sample_id,
          route_id: data.route_id,
          route_name: opts.route_name,
          style_name: data.style_name,
          description: data.description,
          status: "candidate",
          params: data.params,
          output_type: data.output.type,
          output_path: data.output.path,
          poster_path: data.output.poster,
          audio_url: data.audio_url,
          srt_url: data.srt_url,
          manifest_url: data.manifest_url,
          content_preview: data.content_preview,
          duration_sec: data.duration_sec,
          audio_duration_sec: data.audio_duration_sec,
          tags: opts.tags,
        }),
      });
      loadSamples();
      setActiveTab("gallery");
      if (opts.successMsg) setSuccessMsg(opts.successMsg);
      return true;
    } catch (e) {
      setError("生成失败: " + String(e));
      return false;
    } finally {
      setGenerating(null);
    }
  };

  const handleGenerate = (preset: PresetStyle) =>
    generateAndSaveSample({
      key: preset.style_id,
      route_id: preset.route_id,
      route_name: preset.route_name,
      style_name: preset.style_name,
      description: preset.description,
      params: preset.params,
      tags: preset.tags,
    });

  // V0.4.3: 用模板一键生成新样片 → 形成「样片 → 模板 → 新样片」闭环
  const handleUseTemplate = (t: StyleTemplate) =>
    generateAndSaveSample({
      key: t.id,
      route_id: t.route_id,
      route_name: t.route_name,
      style_name: t.style_name || t.name,
      description: t.description || "",
      params: t.params,
      tags: t.tags,
      successMsg: `已用模板「${t.name}」生成新样片`,
    });

  const handleDelete = async (id: string) => {
    if (!confirm("确认删除该记录？文件不受影响。")) return;
    try {
      await fetch(`${API_BASE}/style-samples/${id}`, { method: "DELETE" });
      loadSamples();
    } catch (e) {
      setError("删除失败: " + String(e));
    }
  };

  const handleCompare = async (id: string) => {
    const next = new Set(compareSet);
    if (next.has(id)) {
      // 取消对比：调用 status 接口改回 candidate
      next.delete(id);
      try {
        await fetch(`${API_BASE}/style-samples/${id}/status`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "candidate" }),
        });
      } catch { /* ignore */ }
    } else {
      // 加入对比
      next.add(id);
      try {
        await fetch(`${API_BASE}/style-samples/${id}/compare`, { method: "POST" });
      } catch { /* ignore */ }
    }
    setCompareSet(next);
    loadSamples();
  };

  const handleJudge = async (id: string) => {
    setJudgingSet((prev) => new Set(prev).add(id));
    setError("");
    try {
      const resp = await fetch(`${API_BASE}/style-samples/${id}/judge`, { method: "POST" });
      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      loadSamples();
      loadScoreHistory();
    } catch (e) {
      setError("评分失败: " + String(e));
    } finally {
      setJudgingSet((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  // V0.4.2: 升级样片为模板
  const handlePromote = async (sampleId: string) => {
    setError("");
    setSuccessMsg("");
    try {
      const resp = await fetch(`${API_BASE}/style-samples/${sampleId}/promote-template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      if (data.warnings && data.warnings.length > 0) {
        setSuccessMsg(`已升级为模板（${data.warnings.join(" ")}）`);
      } else {
        setSuccessMsg("已升级为模板");
      }
      loadTemplates();
      setActiveTab("templates");
    } catch (e) {
      setError("升级失败: " + String(e));
    }
  };

  // V0.4.2: 删除模板
  const handleDeleteTemplate = async (templateId: string) => {
    if (!confirm("确认删除该模板？原样片不受影响。")) return;
    try {
      await fetch(`${API_BASE}/style-templates/${templateId}`, { method: "DELETE" });
      loadTemplates();
    } catch (e) {
      setError("删除模板失败: " + String(e));
    }
  };

  const routeOptions = [
    { value: "", label: "全部路线" },
    { value: "local_frame_compose", label: "Pillow 信息卡" },
    { value: "template_programmatic_render", label: "Remotion 动态模板" },
    { value: "ai_asset_then_compose", label: "AI 素材氛围" },
  ];

  const filteredPresets = filterRoute ? presets.filter((p) => p.route_id === filterRoute) : presets;
  const groupedPresets = filteredPresets.reduce((acc, p) => {
    if (!acc[p.route_id]) acc[p.route_id] = [];
    acc[p.route_id].push(p);
    return acc;
  }, {} as Record<string, PresetStyle[]>);

  const routeNames: Record<string, string> = {
    local_frame_compose: "Pillow 信息卡路线",
    template_programmatic_render: "Remotion 动态模板路线",
    ai_asset_then_compose: "AI 素材氛围路线",
  };

  return (
    <div style={{ padding: "2rem", maxWidth: 1280, margin: "0 auto" }}>
      <Link to="/video-lab" style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}>← 返回首页</Link>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "0.5rem" }}>路线风格样片库</h1>
      <p style={{ color: "#64748b", fontSize: "0.9rem", marginTop: "0.25rem" }}>
        V0.4.2 · 无数据库 · 风格探索 · 视觉评分 · 对比选优 · 模板沉淀
      </p>

      {/* Tab 切换 */}
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
        <button
          onClick={() => setActiveTab("presets")}
          style={{
            background: activeTab === "presets" ? "#3b82f6" : "#f1f5f9",
            color: activeTab === "presets" ? "white" : "#475569",
            border: "none",
            borderRadius: 8,
            padding: "0.5rem 1.25rem",
            fontSize: "0.85rem",
            cursor: "pointer",
          }}
        >
          预置风格 ({presets.length})
        </button>
        <button
          onClick={() => setActiveTab("gallery")}
          style={{
            background: activeTab === "gallery" ? "#3b82f6" : "#f1f5f9",
            color: activeTab === "gallery" ? "white" : "#475569",
            border: "none",
            borderRadius: 8,
            padding: "0.5rem 1.25rem",
            fontSize: "0.85rem",
            cursor: "pointer",
          }}
        >
          样片库 ({samples.length})
        </button>
        <button
          onClick={() => setActiveTab("compare")}
          style={{
            background: activeTab === "compare" ? "#3b82f6" : "#f1f5f9",
            color: activeTab === "compare" ? "white" : "#475569",
            border: "none",
            borderRadius: 8,
            padding: "0.5rem 1.25rem",
            fontSize: "0.85rem",
            cursor: "pointer",
          }}
        >
          对比面板 ({compareSet.size})
        </button>
        <button
          onClick={() => setActiveTab("templates")}
          style={{
            background: activeTab === "templates" ? "#3b82f6" : "#f1f5f9",
            color: activeTab === "templates" ? "white" : "#475569",
            border: "none",
            borderRadius: 8,
            padding: "0.5rem 1.25rem",
            fontSize: "0.85rem",
            cursor: "pointer",
          }}
        >
          模板库 ({templates.length})
        </button>
      </div>

      {/* 筛选 */}
      <div style={{ display: "flex", gap: "1rem", marginTop: "1rem", flexWrap: "wrap" }}>
        <select
          value={filterRoute}
          onChange={(e) => setFilterRoute(e.target.value)}
          style={{ padding: "0.4rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.8rem" }}
        >
          {routeOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          style={{ padding: "0.4rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.8rem" }}
        >
          <option value="">全部状态</option>
          <option value="candidate">候选中</option>
          <option value="approved">已确认</option>
          <option value="rejected">已放弃</option>
          <option value="comparing">对比中</option>
        </select>
        <button
          onClick={() => { if (activeTab === "gallery") loadSamples(); else loadPresets(); }}
          style={{
            background: "#f1f5f9",
            color: "#475569",
            border: "1px solid #e2e8f0",
            borderRadius: 8,
            padding: "0.4rem 0.75rem",
            fontSize: "0.8rem",
            cursor: "pointer",
          }}
        >
          🔄 刷新
        </button>
      </div>

      {error && (
        <div style={{ marginTop: "1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "0.75rem", fontSize: "0.82rem", color: "#b91c1c" }}>
          ⚠️ {error}
        </div>
      )}
      {successMsg && (
        <div style={{ marginTop: "1rem", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "0.75rem", fontSize: "0.82rem", color: "#166534" }}>
          ✓ {successMsg}
        </div>
      )}

      {/* 预置风格 Tab */}
      {activeTab === "presets" && (
        <div style={{ marginTop: "1rem" }}>
          {Object.entries(groupedPresets).map(([routeId, routePresets]) => {
            const color = ROUTE_COLORS[routeId] ?? "#64748b";
            return (
              <div key={routeId} style={{ marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                  <div style={{ width: 4, height: 20, background: color, borderRadius: 2 }} />
                  <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
                    {routeNames[routeId] ?? routeId}
                  </h2>
                  <span style={{ fontSize: "0.72rem", color: "#94a3b8" }}>({routePresets.length} 个风格)</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem" }}>
                  {routePresets.map((p) => (
                    <PresetStyleCard
                      key={p.style_id}
                      preset={p}
                      onGenerate={handleGenerate}
                      generating={generating === p.style_id}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 样片库 Tab */}
      {activeTab === "gallery" && (
        <div style={{ marginTop: "1rem" }}>
          {samples.length === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem 0", color: "#94a3b8", fontSize: "0.9rem" }}>
              暂无样片，请先在「预置风格」中生成
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem" }}>
              {samples.map((s) => (
                <SampleCard
                  key={s.id}
                  sample={s}
                  onDelete={handleDelete}
                  onCompare={handleCompare}
                  onSave={() => {}}
                  selectedForCompare={compareSet.has(s.id)}
                  onJudge={handleJudge}
                  judging={judgingSet.has(s.id)}
                  onPromote={handlePromote}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* V0.4.1: 对比面板 Tab */}
      {activeTab === "compare" && (
        <div style={{ marginTop: "1rem" }}>
          {/* V0.4.4: 各路线评分趋势（历史可分析）*/}
          {Object.keys(scoreSummary).length > 0 && (
            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "0.75rem 1rem", marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>📈 各路线评分趋势（感知分 0-100）</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
                {Object.entries(scoreSummary).map(([rid, s]) => {
                  const color = ROUTE_COLORS[rid] ?? "#64748b";
                  const deltaText = s.delta === null ? "—" : s.delta > 0 ? `▲ +${s.delta}` : s.delta < 0 ? `▼ ${s.delta}` : "＝0";
                  const deltaColor = s.delta === null ? "#94a3b8" : s.delta > 0 ? "#10b981" : s.delta < 0 ? "#ef4444" : "#94a3b8";
                  return (
                    <div key={rid} style={{ border: `1px solid ${color}33`, borderRadius: 8, padding: "0.4rem 0.7rem", minWidth: 150 }}>
                      <div style={{ fontSize: "0.7rem", color: "#64748b" }}>{s.routeName}</div>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                        <span style={{ fontSize: "1.1rem", fontWeight: 700, color }}>{s.latest ?? "—"}</span>
                        <span style={{ fontSize: "0.72rem", color: deltaColor }}>{deltaText}</span>
                      </div>
                      <div style={{ fontSize: "0.62rem", color: "#94a3b8" }}>均 {s.average ?? "—"} · {s.count} 次</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {compareSet.size === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem 0", color: "#94a3b8", fontSize: "0.9rem" }}>
              <div style={{ marginBottom: "1rem" }}>暂无对比样片，请先在样片库中点击「加入对比」</div>
              <button
                onClick={() => setActiveTab("gallery")}
                style={{
                  background: "#3b82f6",
                  color: "white",
                  border: "none",
                  borderRadius: 8,
                  padding: "0.5rem 1rem",
                  fontSize: "0.85rem",
                  cursor: "pointer",
                }}
              >
                去样片库
              </button>
            </div>
          ) : (
            <div>
              {/* No score warning */}
              {samples.filter(s => s.status === "comparing" && !s.visual_judgement).length > 0 && (
                <div style={{
                  background: "#fef3c7",
                  border: "1px solid #f59e0b",
                  borderRadius: 8,
                  padding: "0.6rem 1rem",
                  fontSize: "0.78rem",
                  color: "#92400e",
                  marginBottom: "1rem",
                }}>
                  ⚠️ 暂无视觉评分，请先对样片进行评分后再比较。
                </div>
              )}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
                {samples
                  .filter((s) => s.status === "comparing")
                  .sort((a, b) => {
                    // Has score first
                    if (a.visual_judgement && !b.visual_judgement) return -1;
                    if (!a.visual_judgement && b.visual_judgement) return 1;
                    // Higher score first
                    if (a.visual_judgement && b.visual_judgement) {
                      return b.visual_judgement.score - a.visual_judgement.score;
                    }
                    // No score: newer first
                    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
                  })
                  .map((s) => {
                    const comparingSamples = samples.filter(s => s.status === "comparing" && s.visual_judgement);
                    const maxScore = comparingSamples.length > 0
                      ? Math.max(...comparingSamples.map(cs => cs.visual_judgement!.score))
                      : -1;
                    const isTopScore = !!s.visual_judgement && s.visual_judgement.score >= maxScore;
                    return (
                      <CompareCard
                        key={s.id}
                        sample={s}
                        onRemove={handleCompare}
                        isTopScore={isTopScore}
                        onPromote={handlePromote}
                      />
                    );
                  })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* V0.4.2: 模板库 Tab */}
      {activeTab === "templates" && (
        <div style={{ marginTop: "1rem" }}>
          {templates.length === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem 0", color: "#94a3b8", fontSize: "0.9rem" }}>
              暂无模板，请先从高分样片或对比面板中升级
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
              {templates.map((t) => {
                const color = ROUTE_COLORS[t.route_id] ?? "#64748b";
                const keyParams = getKeyParamsSummary(t.params, t.route_id);
                return (
                  <div
                    key={t.id}
                    style={{
                      background: "white",
                      border: "1px solid #e2e8f0",
                      borderRadius: 12,
                      padding: "1rem",
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.5rem",
                    }}
                  >
                    {/* Header */}
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.5rem" }}>
                      <div>
                        <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#1e293b" }}>{t.name}</div>
                        <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: 2 }}>{t.route_name}</div>
                      </div>
                      {t.visual_judgement && (
                        <span style={{
                          fontSize: "0.7rem",
                          fontWeight: 700,
                          color: t.visual_judgement.score >= 70 ? "#10b981" : t.visual_judgement.score >= 55 ? "#f59e0b" : "#ef4444",
                        }}>
                          {t.visual_judgement.score}
                        </span>
                      )}
                    </div>

                    {/* Source info */}
                    <div style={{ fontSize: "0.65rem", color: "#94a3b8" }}>
                      来源: {t.source_sample_id} {t.source_sample_score !== null ? `(${t.source_sample_score}分)` : ""}
                    </div>

                    {/* Tags */}
                    {t.tags.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
                        {t.tags.map((tag) => (
                          <span key={tag} style={{
                            fontSize: "0.6rem",
                            background: `${color}10`,
                            color: color,
                            borderRadius: 4,
                            padding: "1px 5px",
                          }}>
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Key params */}
                    {keyParams.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
                        {keyParams.map((p) => (
                          <span key={p} style={{
                            fontSize: "0.6rem",
                            background: "#f1f5f9",
                            color: "#475569",
                            borderRadius: 4,
                            padding: "1px 5px",
                          }}>
                            {p}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Actions */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginTop: "auto" }}>
                      {/* V0.4.3: 用模板生成新样片 */}
                      <button
                        onClick={() => handleUseTemplate(t)}
                        disabled={generating === t.id}
                        style={{
                          background: generating === t.id ? "#93c5fd" : color,
                          color: "white",
                          border: "none",
                          borderRadius: 6,
                          padding: "0.45rem 0.75rem",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          cursor: generating === t.id ? "wait" : "pointer",
                          width: "100%",
                        }}
                      >
                        {generating === t.id ? "生成中…（约 1-2 分钟）" : "✨ 使用此模板生成样片"}
                      </button>
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                          onClick={() => navigator.clipboard.writeText(JSON.stringify(t.params, null, 2))}
                          style={{
                            background: "#f1f5f9",
                            color: "#475569",
                            border: "none",
                            borderRadius: 6,
                            padding: "0.35rem 0.75rem",
                            fontSize: "0.72rem",
                            cursor: "pointer",
                            flex: 1,
                          }}
                        >
                          📋 复制参数
                        </button>
                        <button
                          onClick={() => handleDeleteTemplate(t.id)}
                          style={{
                            background: "#fef2f2",
                            color: "#ef4444",
                            border: "1px solid #fecaca",
                            borderRadius: 6,
                            padding: "0.35rem 0.75rem",
                            fontSize: "0.72rem",
                            cursor: "pointer",
                            flex: 1,
                          }}
                        >
                          🗑 删除
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
