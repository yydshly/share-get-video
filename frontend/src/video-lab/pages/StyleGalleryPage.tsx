/**
 * StyleGalleryPage.tsx - 路线风格样片库
 * Path: /video-lab/style-gallery
 * V0.3.7: 风格样片库 — 每条路线独立风格探索，无数据库，JSONL 存储
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { resolveUrl } from "../utils/url";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

// ─── V0.7.3: Workbench 样片识别助手 ──────────────────────────────────────────

/** 识别一条样片是否来自 /video-lab/workbench */
const isWorkbenchSample = (sample: StyleSample): boolean => {
  const tags = Array.isArray(sample?.tags) ? sample.tags : [];
  const params = (sample?.params ?? {}) as Record<string, unknown>;
  return tags.includes("workbench") || params.source === "workbench";
};

/** Workbench 路线 id → 中文标签 */
const getWorkbenchRouteLabel = (sample: StyleSample): string => {
  const params = (sample?.params ?? {}) as Record<string, unknown>;
  const route = String(params.workbenchRoute || "");
  if (route === "pillow") return "Pillow 信息卡片";
  if (route === "remotion_data_news") return "Remotion Data News";
  if (route === "remotion_card_stack") return "Remotion Card Stack";
  return route || "未知 Workbench 路线";
};

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
  // V1.0.5: Experiment asset metadata
  source?: {
    source_type?: string;
    source_page?: string;
    source_run_id?: string;
    experiment_id?: string;
    job_id?: string;
    run_id?: string;
    workbench_route?: string;
    saved_from?: string;
  };
  generation?: {
    visual_route?: string;
    visual_profile?: string;
    remotion_family?: string;
    route_preset?: string;
    aspect_ratio?: string;
    target_duration?: number;
    key_point_count?: number;
    content_hash?: string;
  };
  asset_meta?: {
    final_video_url?: string;
    cover_url?: string;
    audio_url?: string;
    srt_url?: string;
    manifest_url?: string;
    runtime_prefix?: string;
    artifact_count?: number;
  };
  quality_meta?: {
    structural_score?: number | null;
    visual_score?: number | null;
    warnings?: string[];
    steps?: Array<Record<string, unknown>>;
  };
  review_meta?: {
    review_status?: string;
    review_notes?: string;
    problem_tags?: string[];
  };
  job_run?: {
    jobId?: string;
    runId?: string;
    experimentId?: string;
    routeId?: string;
    status?: string;
    stage?: string;
    progress?: number;
    stageLabel?: string;
  };
  schema_version?: string;
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

interface RouteFit {
  routeName: string;
  sampleCount: number;
  scoredCount: number;
  avgScore: number | null;
  best: { sampleId: string; styleName: string; score: number; grade: string; poster: string } | null;
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

// V1.0.7: Compare Bundle
interface CompareBundleItem {
  sample_id: string;
  route_id: string;
  route_name: string;
  style_name: string;
  status: string;
  score: number | null;
  grade: string;
  video_url: string;
  poster_url: string;
  manifest_url: string;
  rerun_payload_available: boolean;
  notes: string;
}

interface CompareBundleDecision {
  winner_sample_id: string;
  winner_reason: string;
  rejected_sample_ids: string[];
  rejected_reasons: Record<string, string>;
  productization_notes: string;
}

interface CompareBundle {
  id: string;
  title: string;
  goal: string;
  sample_ids: string[];
  items: CompareBundleItem[];
  decision: CompareBundleDecision;
  tags: string[];
  created_at: string;
  updated_at: string;
  schema_version: string;
}

// ─── 工具 ────────────────────────────────────────────────────────────────────

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
  highlighted = false,
}: {
  preset: PresetStyle;
  onGenerate: (p: PresetStyle) => void;
  generating: boolean;
  highlighted?: boolean;
}) {
  const color = ROUTE_COLORS[preset.route_id] ?? "#64748b";
  return (
    <div
      data-highlighted-style={highlighted ? "true" : undefined}
      style={{
        background: highlighted ? `${color}08` : "white",
        border: `1px solid ${highlighted ? color : `${color}30`}`,
        borderRadius: 12,
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        boxShadow: highlighted ? `0 0 0 3px ${color}18, 0 10px 24px ${color}16` : undefined,
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
  isHighlighted = false,
  onOpenCompare,
  copyingRerunId,
  rerunCopyFeedback,
  onCopyRerun,
}: {
  sample: StyleSample;
  onDelete: (id: string) => void;
  onCompare: (id: string) => void;
  onSave: (s: StyleSample) => void;
  selectedForCompare: boolean;
  onJudge: (id: string) => void;
  judging: boolean;
  onPromote: (id: string) => void;
  isHighlighted?: boolean;
  onOpenCompare?: () => void;
  copyingRerunId: string | null;
  rerunCopyFeedback: {
    id: string;
    type: "success" | "error";
    message: string;
  } | null;
  onCopyRerun: (id: string) => void;
}) {
  const color = ROUTE_COLORS[sample.route_id] ?? "#64748b";
  const statusInfo = STATUS_LABELS[sample.status] ?? STATUS_LABELS.candidate;
  const videoSrc = resolveUrl(sample.urls.video_url || sample.output.path);
  const posterSrc = resolveUrl(sample.urls.poster_url || sample.output.poster);
  // V0.8.7: 资产缺失诊断 —— 区分 video / poster 各自是否存在
  const hasVideo = Boolean(sample.urls.video_url || sample.output.path);
  const hasPoster = Boolean(sample.urls.poster_url || sample.output.poster);
  const hasPreview = hasVideo || hasPoster;
  // V0.8.7: 复制样片诊断 JSON —— 用于截图反馈时直接粘给开发
  const handleCopyDiagnostic = () => {
    const diagnostic = {
      id: sample.id,
      route_id: sample.route_id,
      route_name: sample.route_name,
      style_name: sample.style_name,
      status: sample.status,
      hasVideo,
      hasPoster,
      video_url: sample.urls.video_url || "",
      output_path: sample.output.path || "",
      poster_url: sample.urls.poster_url || "",
      output_poster: sample.output.poster || "",
      audio_url: sample.urls.audio_url || sample.output.audio_url || "",
      srt_url: sample.urls.srt_url || sample.output.srt_url || "",
      manifest_url: sample.urls.manifest_url || sample.output.manifest_url || "",
      duration_sec: sample.duration_sec,
      audio_duration_sec: sample.audio_duration_sec,
      params: sample.params,
    };
    try {
      navigator.clipboard.writeText(JSON.stringify(diagnostic, null, 2));
    } catch {
      // ignore
    }
  };
  // V0.7.7: 视频 ref（用于原生全屏）
  const videoRef = useRef<HTMLVideoElement>(null);
  const handleFullscreen = () => {
    const v = videoRef.current;
    if (!v) return;
    const req =
      v.requestFullscreen ||
      (v as HTMLVideoElement & { webkitRequestFullscreen?: () => void }).webkitRequestFullscreen;
    if (req) {
      try { req.call(v); } catch { /* ignore */ }
    }
  };
  // V0.7.3: Workbench 样片特殊样式
  const isWb = isWorkbenchSample(sample);
  const wbColor = "#0f766e";
  const wbBg = "#f0fdfa";
  const cardBorder = isHighlighted
    ? `2px solid ${wbColor}`
    : selectedForCompare
    ? "1px solid #3b82f6"
    : isWb
    ? "1px solid #5eead4"
    : "1px solid #e2e8f0";
  const cardBg = isHighlighted ? wbBg : "white";
  const wbRouteLabel = isWb ? getWorkbenchRouteLabel(sample) : "";
  const wbExperimentId = isWb ? String((sample.params as Record<string, unknown> | undefined)?.experimentId || "") : "";
  const wbReviewNotes = isWb ? String((sample.params as Record<string, unknown> | undefined)?.reviewNotes || "").trim() : "";

  return (
    <div
      style={{
        background: cardBg,
        border: cardBorder,
        borderRadius: 12,
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.6rem",
      }}
    >
      {/* 头部 */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b" }}>{sample.style_name}</div>
            {isWb && (
              <span
                title="此样片来自 /video-lab/workbench 的人工通过结果"
                style={{
                  fontSize: "0.6rem",
                  background: `${wbColor}15`,
                  color: wbColor,
                  border: `1px solid ${wbColor}55`,
                  borderRadius: 999,
                  padding: "1px 7px",
                  fontWeight: 700,
                }}
              >
                🧪 Workbench 样片
              </span>
            )}
            {isHighlighted && (
              <span
                style={{
                  fontSize: "0.6rem",
                  background: "#fef3c7",
                  color: "#92400e",
                  border: "1px solid #f59e0b",
                  borderRadius: 999,
                  padding: "1px 7px",
                  fontWeight: 700,
                }}
              >
                📍 已定位
              </span>
            )}
          </div>
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

      {/* V0.7.3: Workbench 来源信息块 — 不再藏在 tags / params details */}
      {isWb && (
        <div
          style={{
            background: wbBg,
            border: `1px dashed ${wbColor}55`,
            borderRadius: 8,
            padding: "0.5rem 0.65rem",
            display: "flex",
            flexDirection: "column",
            gap: 4,
            fontSize: "0.68rem",
            color: "#134e4a",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ color: wbColor, fontWeight: 700 }}>来源：</span>
            <span>Workbench 人工通过</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ color: wbColor, fontWeight: 700 }}>Workbench 路线：</span>
            <span>{wbRouteLabel}</span>
          </div>
          {wbExperimentId && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ color: wbColor, fontWeight: 700 }}>experimentId：</span>
              <span style={{ fontFamily: "monospace", wordBreak: "break-all" }}>{wbExperimentId}</span>
            </div>
          )}
          {wbReviewNotes && (
            <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
              <span style={{ color: wbColor, fontWeight: 700, flexShrink: 0 }}>备注：</span>
              <span style={{ fontStyle: "italic" }}>"{wbReviewNotes}"</span>
            </div>
          )}
        </div>
      )}

      {/* 预览 */}
      {videoSrc ? (
        <div style={{ background: "#0f172a", borderRadius: 8, overflow: "hidden" }}>
          <video
            ref={videoRef}
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
        // V0.8.7: 样片资产缺失提示 —— 不再只显示"暂无预览"
        <div
          data-testid="sample-asset-missing"
          style={{
            background: "#fef2f2",
            border: "1px dashed #fecaca",
            borderRadius: 8,
            padding: "0.7rem 0.85rem",
            display: "flex",
            flexDirection: "column",
            gap: 6,
            color: "#991b1b",
            fontSize: "0.7rem",
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 700, fontSize: "0.78rem" }}>
            ⚠️ 样片资产缺失
          </div>
          <div style={{ color: "#b91c1c" }}>
            当前记录没有 video_url / output.path / poster_url。这条记录可能是早期生成或保存字段缺失导致。
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", columnGap: 8, rowGap: 2, color: "#7f1d1d", fontSize: "0.65rem" }}>
            <span style={{ color: "#94a3b8" }}>id</span>
            <span style={{ fontFamily: "monospace", wordBreak: "break-all" }}>{sample.id}</span>
            <span style={{ color: "#94a3b8" }}>route_id</span>
            <span style={{ fontFamily: "monospace", wordBreak: "break-all" }}>{sample.route_id}</span>
            <span style={{ color: "#94a3b8" }}>style_name</span>
            <span style={{ wordBreak: "break-all" }}>{sample.style_name}</span>
            <span style={{ color: "#94a3b8" }}>manifest_url</span>
            <span style={{ fontFamily: "monospace", wordBreak: "break-all" }}>
              {sample.urls.manifest_url || sample.output.manifest_url || "—"}
            </span>
            <span style={{ color: "#94a3b8" }}>audio_url</span>
            <span style={{ fontFamily: "monospace", wordBreak: "break-all" }}>
              {sample.urls.audio_url || sample.output.audio_url || "—"}
            </span>
            <span style={{ color: "#94a3b8" }}>srt_url</span>
            <span style={{ fontFamily: "monospace", wordBreak: "break-all" }}>
              {sample.urls.srt_url || sample.output.srt_url || "—"}
            </span>
            <span style={{ color: "#94a3b8" }}>duration_sec</span>
            <span>{sample.duration_sec}</span>
            <span style={{ color: "#94a3b8" }}>audio_duration_sec</span>
            <span>{sample.audio_duration_sec}</span>
          </div>
        </div>
      )}

      {/* V0.7.7: Workbench 样片 — 如何判断效果（轻量提示 + 原生全屏） */}
      {isWb && videoSrc && (
        <div
          style={{
            background: "#f0fdfa",
            border: "1px dashed #5eead4",
            borderRadius: 6,
            padding: "0.4rem 0.6rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "0.5rem",
            flexWrap: "wrap",
          }}
        >
          <div style={{ fontSize: "0.7rem", color: "#0f766e", lineHeight: 1.5 }}>
            💡 当前为样片卡片预览，如需判断效果，请点击视频全屏播放或进入对比面板。
          </div>
          <button
            onClick={handleFullscreen}
            style={{
              background: "white",
              color: "#0f766e",
              border: "1px solid #5eead4",
              borderRadius: 4,
              padding: "0.2rem 0.5rem",
              fontSize: "0.7rem",
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
            title="浏览器原生全屏播放"
          >
            🔍 全屏观看
          </button>
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

      {/* V1.0.5: 实验资产信息 */}
      {(sample.source || sample.generation || sample.asset_meta || sample.job_run || sample.schema_version) && (
        <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.6rem", fontSize: "0.68rem" }}>
          <div style={{ fontWeight: 600, color: "#475569", marginBottom: "0.3rem" }}>实验资产信息</div>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", columnGap: 8, rowGap: 2 }}>
            {sample.source?.source_type && (
              <>
                <span style={{ color: "#94a3b8" }}>来源类型</span>
                <span style={{ color: "#1e293b" }}>{sample.source.source_type}</span>
              </>
            )}
            {sample.source?.experiment_id && (
              <>
                <span style={{ color: "#94a3b8" }}>experimentId</span>
                <span style={{ fontFamily: "monospace", wordBreak: "break-all" }}>{sample.source.experiment_id}</span>
              </>
            )}
            {sample.source?.run_id && (
              <>
                <span style={{ color: "#94a3b8" }}>runId</span>
                <span style={{ fontFamily: "monospace" }}>{sample.source.run_id}</span>
              </>
            )}
            {sample.source?.job_id && (
              <>
                <span style={{ color: "#94a3b8" }}>jobId</span>
                <span style={{ fontFamily: "monospace" }}>{sample.source.job_id}</span>
              </>
            )}
            {sample.generation?.visual_route && (
              <>
                <span style={{ color: "#94a3b8" }}>visualRoute</span>
                <span style={{ color: "#1e293b" }}>{sample.generation.visual_route}</span>
              </>
            )}
            {sample.generation?.visual_profile && (
              <>
                <span style={{ color: "#94a3b8" }}>visualProfile</span>
                <span style={{ color: "#1e293b" }}>{sample.generation.visual_profile}</span>
              </>
            )}
            {sample.generation?.remotion_family && (
              <>
                <span style={{ color: "#94a3b8" }}>remotionFamily</span>
                <span style={{ color: "#1e293b" }}>{sample.generation.remotion_family}</span>
              </>
            )}
            {sample.job_run?.status && (
              <>
                <span style={{ color: "#94a3b8" }}>jobRun状态</span>
                <span style={{ color: sample.job_run.status === "succeeded" ? "#10b981" : "#f59e0b" }}>
                  {sample.job_run.status} {sample.job_run.stageLabel ? `/ ${sample.job_run.stageLabel}` : ""}
                </span>
              </>
            )}
            {sample.asset_meta?.manifest_url && (
              <>
                <span style={{ color: "#94a3b8" }}>manifest</span>
                <a href={sample.asset_meta.manifest_url} target="_blank" rel="noreferrer" style={{ color: "#0f766e", wordBreak: "break-all" }}>
                  {sample.asset_meta.manifest_url.split("/").pop()}
                </a>
              </>
            )}
            {sample.quality_meta?.structural_score != null && (
              <>
                <span style={{ color: "#94a3b8" }}>structuralScore</span>
                <span style={{ color: "#1e293b" }}>{sample.quality_meta.structural_score}</span>
              </>
            )}
            {sample.review_meta?.review_status && (
              <>
                <span style={{ color: "#94a3b8" }}>reviewStatus</span>
                <span style={{ color: "#1e293b" }}>{sample.review_meta.review_status}</span>
              </>
            )}
          </div>
          {/* V1.0.6: 复制复现参数按钮 */}
          <button
            onClick={() => onCopyRerun(sample.id)}
            disabled={copyingRerunId === sample.id}
            style={{
              marginTop: "0.5rem",
              background: copyingRerunId === sample.id ? "#e2e8f0" : "#f0fdf4",
              color: copyingRerunId === sample.id ? "#94a3b8" : "#0f766e",
              border: "1px solid",
              borderColor: copyingRerunId === sample.id ? "#e2e8f0" : "#bbf7d0",
              borderRadius: 6,
              padding: "0.3rem 0.6rem",
              fontSize: "0.68rem",
              cursor: copyingRerunId === sample.id ? "wait" : "pointer",
              width: "100%",
            }}
          >
            {copyingRerunId === sample.id ? "复制中..." : "📋 复制复现参数"}
          </button>
          {rerunCopyFeedback?.id === sample.id && (
            <div
              style={{
                fontSize: "0.65rem",
                color: rerunCopyFeedback.type === "success" ? "#0f766e" : "#dc2626",
                marginTop: "0.2rem",
                wordBreak: "break-all",
              }}
            >
              {rerunCopyFeedback.type === "success" ? "✓ " : "⚠ "}
              {rerunCopyFeedback.message}
            </div>
          )}
        </div>
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

      {/* V0.7.3: 已加入对比面板提示 + 打开对比按钮（仅 comparing 状态） */}
      {sample.status === "comparing" && (
        <div
          style={{
            background: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: 8,
            padding: "0.5rem 0.65rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "0.5rem",
          }}
        >
          <div style={{ fontSize: "0.7rem", color: "#1d4ed8", fontWeight: 600 }}>
            ✓ 已加入对比面板
          </div>
          {onOpenCompare && (
            <button
              onClick={onOpenCompare}
              style={{
                background: "#3b82f6",
                color: "white",
                border: "none",
                borderRadius: 6,
                padding: "0.3rem 0.65rem",
                fontSize: "0.7rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              打开对比面板
            </button>
          )}
        </div>
      )}

      {/* 操作按钮 */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "auto" }}>
        <button
          onClick={handleCopyDiagnostic}
          data-testid="copy-sample-diagnostic"
          style={{
            background: hasPreview ? "#f1f5f9" : "#fef3c7",
            color: hasPreview ? "#475569" : "#92400e",
            border: hasPreview ? "none" : "1px solid #fde68a",
            borderRadius: 6,
            padding: "0.35rem 0.75rem",
            fontSize: "0.72rem",
            cursor: "pointer",
          }}
          title="复制样片诊断 JSON，用于反馈样片资产问题"
        >
          🩺 复制样片诊断 JSON
        </button>
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
  const [searchParams] = useSearchParams();
  const highlightedPresetStyleId = searchParams.get("style_id") || "";
  const [presets, setPresets] = useState<PresetStyle[]>([]);
  const [samples, setSamples] = useState<StyleSample[]>([]);
  const [templates, setTemplates] = useState<StyleTemplate[]>([]);
  const [filterRoute, setFilterRoute] = useState<string>(() => {
    const routeFromUrl = searchParams.get("route_id") || searchParams.get("route");
    if (routeFromUrl) return routeFromUrl;
    return highlightedPresetStyleId.startsWith("remotion_") ? "template_programmatic_render" : "";
  });
  const [filterStatus, setFilterStatus] = useState<string>("");
  // V0.7.3: 新增来源筛选 + Workbench 高亮定位
  const [filterSource, setFilterSource] = useState<"" | "workbench" | "gallery">(() => {
    const v = searchParams.get("source");
    return v === "workbench" || v === "gallery" ? v : "";
  });
  const [highlightSampleId, setHighlightSampleId] = useState<string | null>(
    () => searchParams.get("sample_id"),
  );
  const [highlightDismissed, setHighlightDismissed] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);
  const [compareSet, setCompareSet] = useState<Set<string>>(new Set());
  const [judgingSet, setJudgingSet] = useState<Set<string>>(new Set());
  // V1.0.6: rerun payload copy state
  const [copyingRerunId, setCopyingRerunId] = useState<string | null>(null);
  const [rerunCopyFeedback, setRerunCopyFeedback] = useState<{
    id: string;
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [activeTab, setActiveTab] = useState<"presets" | "gallery" | "compare" | "templates">(() => {
    const v = searchParams.get("tab");
    return v === "gallery" || v === "compare" || v === "templates" ? v : "presets";
  });
  const [scoreSummary, setScoreSummary] = useState<Record<string, RouteScoreSummary>>({});
  const [judgeAvailable, setJudgeAvailable] = useState<boolean>(true);
  const [judgeUnavailableMsg, setJudgeUnavailableMsg] = useState<string>("");
  const [routeFit, setRouteFit] = useState<Record<string, RouteFit>>({});
  // V1.0.7: Compare Bundle state
  const [bundles, setBundles] = useState<CompareBundle[]>([]);
  const [bundleTitle, setBundleTitle] = useState<string>("");
  const [bundleGoal, setBundleGoal] = useState<string>("");
  const [bundleTags, setBundleTags] = useState<string>("");
  const [savingBundle, setSavingBundle] = useState(false);

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

  const loadJudgeAvailability = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/style-gallery/judge-availability`);
      const data = await resp.json();
      setJudgeAvailable(!!data.available);
      setJudgeUnavailableMsg(data.message || "");
    } catch { /* ignore */ }
  }, []);

  const loadScoreHistory = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/style-gallery/score-history`);
      const data = await resp.json();
      setScoreSummary(data.byRoute ?? {});
    } catch { /* ignore */ }
  }, []);

  const loadRouteFit = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/style-gallery/route-fit`);
      const data = await resp.json();
      setRouteFit(data ?? {});
    } catch { /* ignore */ }
  }, []);

  // V1.0.7: Compare Bundle
  const loadBundles = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/style-compare-bundles`);
      if (!resp.ok) throw new Error(`${resp.status}`);
      const data: CompareBundle[] = await resp.json();
      setBundles(data);
    } catch { /* ignore */ }
  }, []);

  // V1.0.7: Save current comparing samples as a bundle
  const handleSaveBundle = async () => {
    const comparingSamples = samples.filter((s) => s.status === "comparing");
    if (comparingSamples.length === 0) return;
    setSavingBundle(true);
    setError("");
    setSuccessMsg("");
    try {
      const defaultTitle = `样片对比包 ${new Date().toLocaleString("zh-CN", { hour12: false })}`;
      const resp = await fetch(`${API_BASE}/style-compare-bundles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: bundleTitle || defaultTitle,
          goal: bundleGoal,
          sampleIds: comparingSamples.map((s) => s.id),
          tags: bundleTags
            ? bundleTags.split(",").map((t) => t.trim()).filter(Boolean)
            : [],
        }),
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      const saved: CompareBundle = await resp.json();
      setSuccessMsg(`已保存对比包：${saved.id}`);
      setBundleTitle("");
      setBundleGoal("");
      setBundleTags("");
      loadBundles();
    } catch (e) {
      setError("保存对比包失败: " + String(e));
    } finally {
      setSavingBundle(false);
    }
  };

  // V1.0.7: Copy bundle JSON
  const handleCopyBundleJson = (bundle: CompareBundle) => {
    navigator.clipboard.writeText(JSON.stringify(bundle, null, 2));
    setSuccessMsg(`已复制对比包 JSON：${bundle.id}`);
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  // V1.0.7: Delete bundle
  const handleDeleteBundle = async (bundleId: string) => {
    if (!confirm("确认删除该对比包？")) return;
    try {
      await fetch(`${API_BASE}/style-compare-bundles/${bundleId}`, { method: "DELETE" });
      loadBundles();
    } catch (e) {
      setError("删除对比包失败: " + String(e));
    }
  };

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
  useEffect(() => { loadJudgeAvailability(); }, [loadJudgeAvailability]);
  useEffect(() => { loadRouteFit(); }, [loadRouteFit]);
  useEffect(() => { loadBundles(); }, [loadBundles]);

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

      // V0.8.7: 保存字段 fallback —— 优先 final_video_url / cover_url，回落 data.output.path
      const outputPath = data.output?.path || data.final_video_url || "";
      const posterPath = data.output?.poster || data.cover_url || "";
      const audioUrl = data.audio_url || data.output?.audio_url || "";
      const srtUrl = data.srt_url || data.output?.srt_url || "";
      const manifestUrl = data.manifest_url || data.output?.manifest_url || "";

      // V0.8.7: 生成接口"成功"但缺视频路径时，不再静默保存无预览样片
      if (!outputPath && !data.final_video_url) {
        throw new Error(
          "生成接口成功返回，但缺少 final_video_url / output.path，无法保存为可预览样片。" +
            "请检查 /style-samples/generate 返回值。",
        );
      }

      // 自动保存到样片库
      const saveResp = await fetch(`${API_BASE}/style-samples`, {
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
          output_path: outputPath,
          poster_path: posterPath,
          audio_url: audioUrl,
          srt_url: srtUrl,
          manifest_url: manifestUrl,
          content_preview: data.content_preview,
          duration_sec: data.duration_sec,
          audio_duration_sec: data.audio_duration_sec,
          tags: opts.tags,
        }),
      });
      // V0.8.7: 保存接口 resp.ok 检查，避免生成成功 / 保存失败时 UI 误报成功
      if (!saveResp.ok) {
        const text = await saveResp.text().catch(() => "");
        throw new Error(`保存样片失败: HTTP ${saveResp.status} ${text}`);
      }
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
      loadRouteFit();
    } catch (e) {
      const msg = String(e).replace(/^Error:\s*/, "");
      if (msg.includes("MINIMAX_API_KEY") || msg.includes("视觉评分")) {
        setJudgeAvailable(false);
        setJudgeUnavailableMsg(msg);
        setError("");
      } else {
        setError("评分失败: " + msg);
      }
    } finally {
      setJudgingSet((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  // V1.0.6: 复制 rerun payload
  const handleCopyRerun = async (id: string) => {
    setCopyingRerunId(id);
    setRerunCopyFeedback(null);
    try {
      const resp = await fetch(`${API_BASE}/style-samples/${id}/rerun-payload`);
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      const payload = await resp.json();
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setRerunCopyFeedback({ id, type: "success", message: "已复制复现参数" });
    } catch (e) {
      const msg = String(e).replace(/^Error:\s*/, "");
      setRerunCopyFeedback({ id, type: "error", message: `复制失败：${msg}` });
    } finally {
      setCopyingRerunId(null);
      setTimeout(() => setRerunCopyFeedback(null), 3000);
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

  // V0.7.3: 二次过滤（路线/状态由后端过滤，来源在前端过滤）
  const visibleSamples = samples.filter((s) => {
    if (filterSource === "workbench") return isWorkbenchSample(s);
    if (filterSource === "gallery") return !isWorkbenchSample(s);
    return true;
  });

  // V0.7.3: Workbench 样片统计（基于后端已返回的 samples 计算）
  const workbenchSamples = samples.filter(isWorkbenchSample);
  const workbenchCount = workbenchSamples.length;
  const workbenchComparing = workbenchSamples.filter((s) => s.status === "comparing").length;
  const workbenchApproved = workbenchSamples.filter((s) => s.status === "approved").length;

  const filteredPresets = (filterRoute ? presets.filter((p) => p.route_id === filterRoute) : presets)
    .slice()
    .sort((a, b) => {
      if (!highlightedPresetStyleId) return 0;
      if (a.style_id === highlightedPresetStyleId) return -1;
      if (b.style_id === highlightedPresetStyleId) return 1;
      return 0;
    });
  const filteredTemplates = filterRoute ? templates.filter((t) => t.route_id === filterRoute) : templates;
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
        V0.7.3 · 无数据库 · 风格探索 · 视觉评分 · 对比选优 · 模板沉淀 · Workbench 样片识别
      </p>

      {/* V0.7.3: 顶部 — 已定位到 Workbench 保存的样片（来自 URL ?sample_id=） */}
      {highlightSampleId && !highlightDismissed && (
        <div
          style={{
            marginTop: "1rem",
            background: "#f0fdfa",
            border: "1px solid #0f766e",
            borderRadius: 10,
            padding: "0.75rem 1rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          <div style={{ fontSize: "0.82rem", color: "#0f766e", fontWeight: 600 }}>
            📍 已定位到 Workbench 保存的样片：<code style={{ background: "white", padding: "1px 6px", borderRadius: 4, color: "#0f766e" }}>{highlightSampleId}</code>
            {visibleSamples.find((s) => s.id === highlightSampleId) ? null : (
              <span style={{ marginLeft: 8, color: "#dc2626", fontWeight: 400 }}>
                （当前筛选下未显示 — 切换「全部来源」或调整路线/状态筛选可查看）
              </span>
            )}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => { setFilterSource("workbench"); setActiveTab("gallery"); }}
              style={{
                background: "#0f766e", color: "white", border: "none",
                borderRadius: 6, padding: "0.3rem 0.75rem",
                fontSize: "0.75rem", fontWeight: 600, cursor: "pointer",
              }}
            >
              查看 Workbench 样片
            </button>
            <button
              onClick={() => setHighlightDismissed(true)}
              style={{
                background: "transparent", color: "#0f766e",
                border: "1px solid #0f766e55",
                borderRadius: 6, padding: "0.3rem 0.6rem",
                fontSize: "0.75rem", cursor: "pointer",
              }}
            >
              关闭
            </button>
          </div>
        </div>
      )}

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
          模板库 ({filteredTemplates.length})
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
        {/* V0.7.3: 来源筛选（仅样片库 tab 有意义，其它 tab 会忽略） */}
        <select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value as "" | "workbench" | "gallery")}
          style={{
            padding: "0.4rem 0.75rem",
            border: `1px solid ${filterSource === "workbench" ? "#0f766e" : "#e2e8f0"}`,
            background: filterSource === "workbench" ? "#f0fdfa" : "white",
            color: filterSource === "workbench" ? "#0f766e" : "#475569",
            borderRadius: 8,
            fontSize: "0.8rem",
            fontWeight: filterSource === "workbench" ? 600 : 400,
            cursor: "pointer",
          }}
        >
          <option value="">全部来源</option>
          <option value="workbench">🧪 Workbench 样片</option>
          <option value="gallery">样片库生成</option>
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
      {!judgeAvailable && (
        <div style={{ marginTop: "1rem", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 8, padding: "0.75rem", fontSize: "0.82rem", color: "#92400e" }}>
          🔑 {judgeUnavailableMsg || "视觉评分需配置 MINIMAX_API_KEY（云端能力，非本地）。"}
        </div>
      )}

      {/* 预置风格 Tab */}
      {activeTab === "presets" && (
        <div style={{ marginTop: "1rem" }}>
          {/* V0.8.7: 区分"生成样片"与"探索 Remotion" */}
          <div
            data-testid="preset-tab-hint"
            style={{
              background: "#eff6ff",
              border: "1px solid #bfdbfe",
              borderRadius: 10,
              padding: "0.7rem 0.9rem",
              marginBottom: "1rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "0.75rem",
              flexWrap: "wrap",
              color: "#1d4ed8",
              fontSize: "0.78rem",
              lineHeight: 1.5,
            }}
          >
            <div>
              这里可以单独生成某个预置风格样片；如果要系统比较 Remotion 多个风格，请使用 Style Sweep。
            </div>
            <Link
              to="/video-lab/style-sweep"
              style={{
                background: "#3b82f6",
                color: "white",
                textDecoration: "none",
                borderRadius: 6,
                padding: "0.35rem 0.85rem",
                fontSize: "0.78rem",
                fontWeight: 600,
                whiteSpace: "nowrap",
              }}
            >
              进入 Style Sweep
            </Link>
          </div>
          {filterRoute === "template_programmatic_render" && (
            <div
              data-testid="remotion-preset-focus"
              style={{
                background: "#f8fafc",
                border: "1px solid #cbd5e1",
                borderRadius: 10,
                padding: "0.7rem 0.9rem",
                marginBottom: "1rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "0.75rem",
                flexWrap: "wrap",
                color: "#334155",
                fontSize: "0.78rem",
                lineHeight: 1.5,
              }}
            >
              <div>
                Remotion 样式扩展预设已按范式筛选；可直接生成样片，再进入样片库做评分、对比和沉淀。
                {highlightedPresetStyleId && (
                  <span style={{ color: "#2563eb", fontWeight: 700 }}> 当前聚焦：{highlightedPresetStyleId}</span>
                )}
              </div>
              <Link
                to="/video-lab/remotion-style-family"
                style={{
                  background: "#0f172a",
                  color: "white",
                  textDecoration: "none",
                  borderRadius: 6,
                  padding: "0.35rem 0.85rem",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                }}
              >
                返回 Remotion 范式
              </Link>
            </div>
          )}
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
                      highlighted={p.style_id === highlightedPresetStyleId}
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
          {/* V0.8.7: 样片库定位提示 */}
          <div
            data-testid="gallery-tab-hint"
            style={{
              background: "#fffbeb",
              border: "1px solid #fbbf24",
              borderRadius: 10,
              padding: "0.7rem 0.9rem",
              marginBottom: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: 4,
              color: "#92400e",
              fontSize: "0.78rem",
              lineHeight: 1.6,
            }}
          >
            <div>
              样片库用于沉淀已经生成或人工通过的样片。每条可用样片应至少包含 <code>video_url</code> 或 <code>poster_url</code>。
              如果卡片显示「样片资产缺失」，说明记录存在但预览路径缺失，建议删除后重新生成或回到 Workbench / Style Sweep 生成新样片。
            </div>
            <div style={{ color: "#78350f" }}>
              Style Gallery 不是 Remotion 批量探索入口；Remotion 能力探索请使用 <Link to="/video-lab/style-sweep" style={{ color: "#1d4ed8", fontWeight: 600 }}>Style Sweep</Link>。
            </div>
          </div>
          {/* V0.7.3: Workbench 样片说明区 — 仅当筛选 workbench 或 URL 带 source=workbench 时显示 */}
          {(filterSource === "workbench" || searchParams.get("source") === "workbench") && (
            <div
              style={{
                background: "#f0fdfa",
                border: "1px solid #5eead4",
                borderRadius: 12,
                padding: "0.85rem 1rem",
                marginBottom: "1rem",
              }}
            >
              <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f766e", marginBottom: 4 }}>
                🧪 Workbench 样片说明
              </div>
              <div style={{ fontSize: "0.78rem", color: "#134e4a", lineHeight: 1.55 }}>
                这些样片来自 <code style={{ background: "white", padding: "1px 5px", borderRadius: 3 }}>/video-lab/workbench</code> 的人工通过结果。
                它们代表已经生成完整视频，并经过人工确认。可在对比面板中并排查看，或升级为模板。
              </div>
              <div
                style={{
                  marginTop: "0.6rem",
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.6rem",
                  fontSize: "0.75rem",
                }}
              >
                <span style={{ background: "white", border: "1px solid #5eead4", borderRadius: 6, padding: "2px 8px", color: "#0f766e" }}>
                  Workbench 样片数量：<b>{workbenchCount}</b>
                </span>
                <span style={{ background: "white", border: "1px solid #5eead4", borderRadius: 6, padding: "2px 8px", color: "#0f766e" }}>
                  对比中：<b>{workbenchComparing}</b>
                </span>
                <span style={{ background: "white", border: "1px solid #5eead4", borderRadius: 6, padding: "2px 8px", color: "#0f766e" }}>
                  已确认：<b>{workbenchApproved}</b>
                </span>
                <span style={{ background: "white", border: "1px solid #5eead4", borderRadius: 6, padding: "2px 8px", color: "#0f766e" }}>
                  当前可见：<b>{visibleSamples.length}</b>
                </span>
              </div>
            </div>
          )}

          {visibleSamples.length === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem 0", color: "#94a3b8", fontSize: "0.9rem" }}>
              {samples.length === 0
                ? "暂无样片，请先在「预置风格」中生成"
                : filterSource === "workbench"
                ? "当前筛选下没有 Workbench 样片，可切回「全部来源」或前往 /video-lab/workbench 生成并通过一条"
                : "当前来源筛选下没有样片"}
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem" }}>
              {visibleSamples.map((s) => (
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
                  isHighlighted={highlightSampleId === s.id}
                  onOpenCompare={() => setActiveTab("compare")}
                  copyingRerunId={copyingRerunId}
                  rerunCopyFeedback={rerunCopyFeedback}
                  onCopyRerun={handleCopyRerun}
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

          {/* V0.4.9: 每条路线最适合风格（宏观目标①：沉淀"哪条路线适合什么"）*/}
          {Object.values(routeFit).some((r) => r.best) && (
            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "0.75rem 1rem", marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>🏆 各路线最适合风格（按最高视觉评分）</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
                {Object.entries(routeFit).filter(([, r]) => r.best).map(([rid, r]) => {
                  const color = ROUTE_COLORS[rid] ?? "#64748b";
                  const b = r.best!;
                  const gradeColor = b.score >= 70 ? "#10b981" : b.score >= 55 ? "#f59e0b" : "#ef4444";
                  return (
                    <div key={rid} style={{ border: `1px solid ${color}33`, borderRadius: 8, padding: "0.5rem 0.7rem", minWidth: 200, display: "flex", gap: "0.6rem", alignItems: "center" }}>
                      {b.poster && (
                        <img src={resolveUrl(b.poster)} alt="" style={{ width: 44, height: 78, objectFit: "cover", borderRadius: 4, background: "#0f172a", flexShrink: 0 }} />
                      )}
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: "0.7rem", color: "#64748b" }}>{r.routeName}</div>
                        <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{b.styleName}</div>
                        <div style={{ fontSize: "0.72rem" }}>
                          <span style={{ color: gradeColor, fontWeight: 700 }}>{b.score}</span>
                          <span style={{ color: "#94a3b8" }}> · 均 {r.avgScore ?? "—"} · {r.scoredCount}/{r.sampleCount} 已评</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* V1.0.7: 保存当前对比包 */}
          {compareSet.size > 0 && (
            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "0.75rem 1rem", marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>💾 保存当前对比包</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <input
                  type="text"
                  placeholder={`标题（默认：样片对比包 ${new Date().toLocaleString("zh-CN", { hour12: false })}）`}
                  value={bundleTitle}
                  onChange={(e) => setBundleTitle(e.target.value)}
                  style={{ padding: "0.4rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.78rem", width: "100%" }}
                />
                <textarea
                  placeholder="对比目标（可选）"
                  value={bundleGoal}
                  onChange={(e) => setBundleGoal(e.target.value)}
                  rows={2}
                  style={{ padding: "0.4rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.78rem", width: "100%", resize: "vertical" }}
                />
                <input
                  type="text"
                  placeholder="标签，逗号分隔（可选）"
                  value={bundleTags}
                  onChange={(e) => setBundleTags(e.target.value)}
                  style={{ padding: "0.4rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.78rem", width: "100%" }}
                />
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    onClick={handleSaveBundle}
                    disabled={savingBundle}
                    style={{
                      background: savingBundle ? "#93c5fd" : "#3b82f6",
                      color: "white",
                      border: "none",
                      borderRadius: 8,
                      padding: "0.45rem 1rem",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      cursor: savingBundle ? "wait" : "pointer",
                    }}
                  >
                    {savingBundle ? "保存中..." : "💾 保存当前对比包"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* V1.0.7: 历史对比包列表 */}
          {bundles.length > 0 && (
            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "0.75rem 1rem", marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>📁 历史对比包</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: 300, overflowY: "auto" }}>
                {bundles.map((b) => (
                  <div key={b.id} style={{ border: "1px solid #e2e8f0", borderRadius: 8, padding: "0.6rem 0.75rem" }}>
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.5rem" }}>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#1e293b" }}>{b.title}</div>
                        {b.goal && <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: 2 }}>目标：{b.goal}</div>}
                        <div style={{ fontSize: "0.65rem", color: "#94a3b8", marginTop: 2 }}>
                          {b.items.length} 个样片 · {b.decision.winner_sample_id ? `胜出：${b.decision.winner_sample_id}` : "暂无评分"}
                          {b.decision.winner_reason ? `（${b.decision.winner_reason}）` : ""}
                        </div>
                        {b.tags.length > 0 && (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.2rem", marginTop: "0.25rem" }}>
                            {b.tags.map((t) => (
                              <span key={t} style={{ fontSize: "0.6rem", background: "#f1f5f9", color: "#475569", borderRadius: 4, padding: "1px 5px" }}>#{t}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div style={{ display: "flex", gap: "0.3rem", flexShrink: 0 }}>
                        <button
                          onClick={() => handleCopyBundleJson(b)}
                          style={{ background: "#f1f5f9", color: "#475569", border: "none", borderRadius: 6, padding: "0.25rem 0.5rem", fontSize: "0.68rem", cursor: "pointer" }}
                          title="复制 JSON"
                        >
                          📋
                        </button>
                        <button
                          onClick={() => handleDeleteBundle(b.id)}
                          style={{ background: "#fef2f2", color: "#ef4444", border: "1px solid #fecaca", borderRadius: 6, padding: "0.25rem 0.5rem", fontSize: "0.68rem", cursor: "pointer" }}
                          title="删除"
                        >
                          🗑
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
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
          {filteredTemplates.length === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem 0", color: "#94a3b8", fontSize: "0.9rem" }}>
              {templates.length === 0 ? "暂无模板，请先从高分样片或对比面板中升级" : "当前路线筛选下暂无模板"}
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
              {filteredTemplates.map((t) => {
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
