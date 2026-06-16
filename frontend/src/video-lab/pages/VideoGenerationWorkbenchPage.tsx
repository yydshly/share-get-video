// Video Generation Workbench Page - V0.7.2
// 视频生成实验台 V0.7.2：approved 后保存样片 / 加入对比真实功能
// V1.0.4: 增加 JobRun 阶段状态展示（同步任务状态契约）

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { resolveUrl, stripRuntimeUrlPrefix, API_BASE } from "../utils/url";

// ─── Types ───────────────────────────────────────────────────────────────────

type RouteId = "pillow" | "remotion_data_news" | "remotion_card_stack" | "ai_asset";
type HumanReviewStatus = "pending" | "approved" | "problem" | "discarded";

// V1.0.4: JobRun v1 status contract (sync task tracking)
interface JobRun {
  jobId: string;
  runId: string;
  experimentId: string;
  mode: string;
  routeId: string;
  status: "pending" | "running" | "succeeded" | "failed" | "canceled";
  stage: string;
  progress: number;
  stageLabel: string;
  logs?: string[];
  artifacts?: Record<string, unknown>;
  error?: { code?: string; message?: string; type?: string } | null;
  createdAt?: string;
  updatedAt?: string;
}

interface PreviewResult {
  experimentId: string;
  success: boolean;
  videoUrl: string;
  runtimePath: string;
  elapsedMs: number;
  route: string;
  message: string;
  failedReason: string | null;
  jobRun?: JobRun;
}

interface FullVideoResult {
  experimentId: string;
  status: string;
  visualRoute: string;
  finalVideoUrl: string;
  coverUrl: string;
  audioUrl?: string;
  srtUrl?: string;
  manifestUrl?: string;
  audioDurationSec?: number;
  subtitleCount?: number;
  failedReason?: string;
  warnings?: string[];
  quality?: {
    overallScore?: number;
    dimensionScores?: Record<string, number>;
    counts?: Record<string, number>;
  };
  params?: Record<string, unknown>;
  steps?: Array<{ name: string; status: string; output: string }>;
  jobRun?: JobRun;
}

interface VisualRouteAvailability {
  routeId: string;
  displayName: string;
  available: boolean;
  availabilityMessage: string;
}

interface RouteOption {
  id: RouteId;
  name: string;
  tagline: string;
  description: string;
  suitable: string[];
  speed: "快（秒级）" | "中（10-30秒）" | "慢（30秒+）";
  cost: "低" | "中" | "高";
  status: "stable" | "experimental" | "preview_only";
  note?: string;
}

// V1.2.1: Information Summary Video Mode
type GenerationMode = "normal" | "information_summary";
type CompressionMode = "brief" | "balanced" | "strict" | "itemized" | "manual";
type TargetPointCount = "auto" | "3" | "5" | "8" | "all";
type EvidencePolicy = "hide" | "badge" | "ending_sources" | "keep_inline";
type DurationMode = "auto" | "30" | "60" | "90";

interface InformationSummaryPlan {
  mode: GenerationMode;
  compressionMode: CompressionMode;
  targetPointCount: TargetPointCount;
  includeOverview: boolean;
  includeConclusion: boolean;
  evidencePolicy: EvidencePolicy;
  targetDurationMode: DurationMode;
  overview: { title: string; subtitle: string; summary: string };
  items: Array<{
    id: string;
    title: string;
    description: string;
    evidence?: string[];
    sourceText?: string;
    selected: boolean;
  }>;
  conclusion: { title: string; text: string };
  stats: {
    detectedItemCount: number;
    selectedItemCount: number;
    droppedItemCount: number;
    estimatedDurationSec: number;
  };
}

// ─── Route Definitions ───────────────────────────────────────────────────────

const ROUTES: RouteOption[] = [
  {
    id: "pillow",
    name: "Pillow 信息卡片",
    tagline: "静态卡 + Ken Burns 动效",
    description: "Pillow 渲染静态信息卡，配合 FFmpeg Ken Burns 实现缓慢缩放 + 淡入动效，速度快，稳定性高。",
    suitable: ["快速验证", "不需要动效的简报", "pillow 基线对比"],
    speed: "快（秒级）",
    cost: "低",
    status: "stable",
  },
  {
    id: "remotion_data_news",
    name: "Remotion Data News",
    tagline: "数字驱动 / 数字滚动 / 数据条",
    description: "以数字高亮和滚动动画为核心，适合性能提升、榜单数据、Benchmark 通过率等数据驱动型内容。",
    suitable: ["性能数据", "榜单排名", "指标变化"],
    speed: "中（10-30秒）",
    cost: "低",
    status: "stable",
    note: "Remotion 动效路线，数字滚动+数据条生长",
  },
  {
    id: "remotion_card_stack",
    name: "Remotion Card Stack",
    tagline: "卡片堆叠 / 短视频信息流",
    description: "以卡片滑动为核心，适合 AI 工具推荐、多产品快速介绍、短资讯合集等强短视频感场景。",
    suitable: ["AI 工具推荐", "今日 AI 三件事", "短资讯合集"],
    speed: "中（10-30秒）",
    cost: "低",
    status: "experimental",
    note: "V0.6.5.2 已强化 prev/next 图层可见性",
  },
  {
    id: "ai_asset",
    name: "AI 素材氛围",
    tagline: "AI 生图 + 信息卡叠加",
    description: "先用 AI 生成氛围背景图，再叠信息卡片，视觉效果丰富但生成较慢，成本较高。",
    suitable: ["追求视觉丰富", "氛围感强的内容", "演示场景"],
    speed: "慢（30秒+）",
    cost: "高",
    status: "experimental",
    note: "AI 生图背景 + 信息卡，预览与完整视频均已接入（生图较慢、耗 API）",
  },
];

// ─── Sample Content ──────────────────────────────────────────────────────────

const SAMPLE_CONTENT = {
  title: "今日 AI 前沿速递",
  body: `科学研究评审实现突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越传统方法39%。
依据：依据 1

购物AI助手落后：主流模型通过率仅57-77%，真实网购任务中完成率仍有较大提升空间。
依据：依据 1

企业级AI加速落地：Anthropic与TCS合作推进企业级 AI 应用，DeepMind投资千万美元。`,
};

// ─── Route → Sample Meta mapping ───────────────────────────────────────────

const ROUTE_SAMPLE_META: Record<RouteId, { route_id: string; route_name: string; style_name: string } | null> = {
  pillow: {
    route_id: "local_frame_compose",
    route_name: "Pillow 信息卡片",
    style_name: "Workbench / Pillow 信息卡片",
  },
  remotion_data_news: {
    route_id: "template_programmatic_render",
    route_name: "Remotion Data News",
    style_name: "Workbench / Remotion Data News",
  },
  remotion_card_stack: {
    route_id: "template_programmatic_render",
    route_name: "Remotion Card Stack",
    style_name: "Workbench / Remotion Card Stack",
  },
  ai_asset: {
    route_id: "ai_asset_then_compose",
    route_name: "AI 素材氛围",
    style_name: "Workbench / AI 素材氛围",
  },
};

// ─── Component ───────────────────────────────────────────────────────────────

function RouteCard({
  route,
  selected,
  availability,
  onSelect,
}: {
  route: RouteOption;
  selected: boolean;
  availability?: VisualRouteAvailability;
  onSelect: () => void;
}) {
  const unavailable = availability?.available === false;
  const statusColor = {
    stable: "#16a34a",
    experimental: "#f59e0b",
    preview_only: "#94a3b8",
  }[route.status];

  const statusLabel = {
    stable: "稳定",
    experimental: "实验中",
    preview_only: "预览暂未接入",
  }[route.status];

  return (
    <div
      onClick={route.status === "preview_only" || unavailable ? undefined : onSelect}
      style={{
        border: selected ? "2px solid #0f766e" : "1px solid #e2e8f0",
        borderRadius: 12,
        padding: "0.85rem 1rem",
        background: selected ? "#f0fdfa" : "white",
        cursor: route.status === "preview_only" || unavailable ? "not-allowed" : "pointer",
        opacity: route.status === "preview_only" || unavailable ? 0.6 : 1,
        transition: "all 0.15s",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: "0.95rem", fontWeight: 700, color: "#1e293b" }}>{route.name}</span>
        <span
          style={{
            fontSize: "0.7rem",
            fontWeight: 600,
            color: statusColor,
            background: `${statusColor}15`,
            border: `1px solid ${statusColor}40`,
            borderRadius: 999,
            padding: "1px 7px",
          }}
        >
          {statusLabel}
        </span>
      </div>
      <div style={{ fontSize: "0.75rem", color: "#64748b", fontStyle: "italic", marginBottom: 6 }}>
        {route.tagline}
      </div>
      <p style={{ fontSize: "0.78rem", color: "#475569", margin: "0 0 8px 0", lineHeight: 1.5 }}>
        {route.description}
      </p>
      <div style={{ display: "flex", gap: 12, fontSize: "0.72rem", color: "#64748b" }}>
        <span>速度：{route.speed}</span>
        <span>成本：{route.cost}</span>
      </div>
      {route.note && (
        <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginTop: 4 }}>{route.note}</div>
      )}
      {availability && (
        <div style={{ fontSize: "0.7rem", color: availability.available ? "#16a34a" : "#dc2626", marginTop: 4 }}>
          {availability.available ? "运行环境可用" : `不可用：${availability.availabilityMessage}`}
        </div>
      )}
    </div>
  );
}

function ReviewBadge({ status }: { status: HumanReviewStatus }) {
  const cfg = {
    pending: { label: "待人工确认", color: "#94a3b8", bg: "#f8fafc" },
    approved: { label: "✅ 已通过", color: "#16a34a", bg: "#f0fdf4" },
    problem: { label: "⚠️ 有问题", color: "#d97706", bg: "#fffbeb" },
    discarded: { label: "❌ 已丢弃", color: "#dc2626", bg: "#fef2f2" },
  }[status];

  return (
    <span
      style={{
        display: "inline-block",
        fontSize: "0.78rem",
        fontWeight: 600,
        color: cfg.color,
        background: cfg.bg,
        border: `1px solid ${cfg.color}40`,
        borderRadius: 999,
        padding: "3px 10px",
      }}
    >
      {cfg.label}
    </span>
  );
}

// ─── JobRun Panel (V1.0.4) ────────────────────────────────────────────────────

function JobRunPanel({ jobRun }: { jobRun?: JobRun | null }) {
  if (!jobRun) return null;

  const statusColor =
    jobRun.status === "succeeded"
      ? { color: "#0f766e", bg: "#f0fdfa", border: "#5eead4" }
      : jobRun.status === "failed"
      ? { color: "#dc2626", bg: "#fef2f2", border: "#fca5a5" }
      : jobRun.status === "running"
      ? { color: "#2563eb", bg: "#eff6ff", border: "#93c5fd" }
      : { color: "#64748b", bg: "#f1f5f9", border: "#cbd5e1" };

  const statusLabel =
    {
      pending: "等待中",
      running: "进行中",
      succeeded: "成功",
      failed: "失败",
      canceled: "已取消",
    }[jobRun.status] || jobRun.status;

  return (
    <div
      style={{
        marginTop: "0.75rem",
        padding: "0.65rem 0.85rem",
        background: statusColor.bg,
        border: `1px solid ${statusColor.border}`,
        borderRadius: 8,
        fontSize: "0.72rem",
        color: "#475569",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          flexWrap: "wrap",
          marginBottom: 6,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              color: statusColor.color,
              background: "white",
              border: `1px solid ${statusColor.border}`,
              borderRadius: 999,
              padding: "2px 9px",
            }}
          >
            JobRun · {statusLabel}
          </span>
          <span style={{ color: "#1e293b", fontWeight: 600 }}>{jobRun.stageLabel}</span>
          <span style={{ color: "#94a3b8" }}>· {jobRun.progress}%</span>
        </div>
        <span style={{ fontFamily: "monospace", color: "#64748b" }}>
          {jobRun.jobId}
        </span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, color: "#64748b" }}>
        <span>
          runId: <span style={{ fontFamily: "monospace", color: "#1e293b" }}>{jobRun.runId}</span>
        </span>
        <span>
          experimentId:{" "}
          <span style={{ fontFamily: "monospace", color: "#1e293b" }}>{jobRun.experimentId}</span>
        </span>
        <span>route: {jobRun.routeId}</span>
        <span>stage: {jobRun.stage}</span>
      </div>
      {/* Progress bar (visual only, no real-time updates — sync task) */}
      <div
        style={{
          marginTop: 6,
          height: 4,
          background: "white",
          border: `1px solid ${statusColor.border}`,
          borderRadius: 999,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${Math.max(0, Math.min(100, jobRun.progress))}%`,
            background: statusColor.color,
            transition: "width 0.3s",
          }}
        />
      </div>
      {jobRun.error && (
        <div
          style={{
            marginTop: 6,
            color: "#dc2626",
            fontSize: "0.7rem",
          }}
        >
          ⚠ {jobRun.error.code || "Error"}：{jobRun.error.message || "未知错误"}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function VideoGenerationWorkbenchPage() {
  // ── Section 1: Content Input ────────────────────────────────────────────
  const [title, setTitle] = useState(SAMPLE_CONTENT.title);
  const [body, setBody] = useState(SAMPLE_CONTENT.body);

  // ── Section 2: Route Selection ──────────────────────────────────────────
  const [selectedRoute, setSelectedRoute] = useState<RouteId>("pillow");
  const [routeAvailability, setRouteAvailability] = useState<Record<string, VisualRouteAvailability>>({});
  const [routeAvailabilityError, setRouteAvailabilityError] = useState("");

  // ── Section 3: Generation Control ───────────────────────────────────────
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [fullLoading, setFullLoading] = useState(false);
  const [fullError, setFullError] = useState("");

  // ── Section 4: Results ──────────────────────────────────────────────────
  const [previewResult, setPreviewResult] = useState<PreviewResult | null>(null);
  const [fullResult, setFullResult] = useState<FullVideoResult | null>(null);

  // ── Section 5: Human Review ─────────────────────────────────────────────
  const [reviewStatus, setReviewStatus] = useState<HumanReviewStatus>("pending");
  const [reviewNotes, setReviewNotes] = useState("");
  const [copied, setCopied] = useState(false);

  // V1.2.1: Information Summary Mode
  const [generationMode, setGenerationMode] = useState<GenerationMode>("normal");
  const [infoSummaryLoading, setInfoSummaryLoading] = useState(false);
  const [infoSummaryError, setInfoSummaryError] = useState("");
  const [infoSummaryPlan, setInfoSummaryPlan] = useState<InformationSummaryPlan | null>(null);
  const [infoSummaryInputFingerprint, setInfoSummaryInputFingerprint] = useState("");
  const [compressionMode, setCompressionMode] = useState<CompressionMode>("balanced");
  const [targetPointCount, setTargetPointCount] = useState<TargetPointCount>("auto");
  const [includeOverview, setIncludeOverview] = useState(true);
  const [includeConclusion, setIncludeConclusion] = useState(true);
  const [evidencePolicy, setEvidencePolicy] = useState<EvidencePolicy>("ending_sources");
  const [targetDurationMode, setTargetDurationMode] = useState<DurationMode>("auto");

  // V1.2.1.1: Helper - compute input fingerprint
  const getCurrentInputFingerprint = () => {
    const text = [title.trim(), body.trim()].filter(Boolean).join("\n\n");
    return `${text.length}:${text.slice(0, 80)}:${text.slice(-80)}`;
  };

  // V1.2.1.1: Helper - clear info summary plan (call on any input/param change)
  const clearInfoSummaryPlan = () => {
    setInfoSummaryPlan(null);
    setInfoSummaryInputFingerprint("");
    setInfoSummaryError("");
  };

  // ── Save / Compare State ───────────────────────────────────────────────
  const [savedSampleId, setSavedSampleId] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");

  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState("");
  const [compareSuccess, setCompareSuccess] = useState(false);

  const loadSample = () => {
    setTitle(SAMPLE_CONTENT.title);
    setBody(SAMPLE_CONTENT.body);
    setPreviewResult(null);
    setFullResult(null);
    setReviewStatus("pending");
    setReviewNotes("");
    setPreviewError("");
    setFullError("");
    // Reset save/compare state
    setSavedSampleId(null);
    setSaveError("");
    setSaveSuccess("");
    setCompareError("");
    setCompareSuccess(false);
    // V1.2.1.1: Reset info summary plan
    clearInfoSummaryPlan();
  };

  const routeToVisualRoute: Record<RouteId, string> = {
    pillow: "local_frame_compose",
    remotion_data_news: "template_programmatic_render",
    remotion_card_stack: "template_programmatic_render",
    ai_asset: "ai_asset_then_compose",
  };

  useEffect(() => {
    let cancelled = false;
    const loadRouteAvailability = async () => {
      try {
        const resp = await fetch(`${API_BASE}/visual-routes`);
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
        const next: Record<string, VisualRouteAvailability> = {};
        for (const item of data as VisualRouteAvailability[]) {
          next[item.routeId] = item;
        }
        if (!cancelled) {
          setRouteAvailability(next);
          setRouteAvailabilityError("");
        }
      } catch (e) {
        if (!cancelled) setRouteAvailabilityError(String(e));
      }
    };
    loadRouteAvailability();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedVisualRoute = routeToVisualRoute[selectedRoute];
  const selectedAvailability = routeAvailability[selectedVisualRoute];
  const selectedRouteUnavailable = selectedAvailability?.available === false;

  // V1.2.1: Build content - use serialized plan content if in info summary mode
  const buildGenerationContent = () => {
    if (generationMode === "information_summary" && infoSummaryPlan) {
      // Use the serialized content from the plan
      const lines: string[] = [];
      if (infoSummaryPlan.includeOverview && infoSummaryPlan.overview) {
        lines.push("【首页总览】");
        if (infoSummaryPlan.overview.title) lines.push(`标题：${infoSummaryPlan.overview.title}`);
        if (infoSummaryPlan.overview.summary) lines.push(`摘要：${infoSummaryPlan.overview.summary}`);
        lines.push("");
      }
      infoSummaryPlan.items.forEach((item, i) => {
        lines.push(`【信息点 ${i + 1}】`);
        if (item.title) lines.push(`标题：${item.title}`);
        if (item.description) lines.push(`描述：${item.description}`);
        if (item.evidence && evidencePolicy === "badge") lines.push(`依据：${item.evidence.join("、")}`);
        lines.push("");
      });
      if (infoSummaryPlan.includeConclusion && infoSummaryPlan.conclusion) {
        lines.push("【尾部总结】");
        if (infoSummaryPlan.conclusion.title) lines.push(`标题：${infoSummaryPlan.conclusion.title}`);
        if (infoSummaryPlan.conclusion.text) lines.push(`内容：${infoSummaryPlan.conclusion.text}`);
      }
      return lines.join("\n");
    }
    return [title.trim(), body.trim()].filter(Boolean).join("\n\n");
  };

  const buildVisualRouteParams = (): Record<string, unknown> => {
    let targetDuration = 45;
    let keyPointCount = 3;

    if (generationMode === "information_summary" && infoSummaryPlan) {
      targetDuration = infoSummaryPlan.stats.estimatedDurationSec || 60;
      keyPointCount = infoSummaryPlan.items.length || 5;
    }

    const base = {
      targetDuration,
      aspectRatio: "9:16",
      keyPointCount,
      useLlmPlan: true,
      coverTitle: title.trim(),
    };
    if (selectedRoute === "remotion_data_news") return { ...base, remotionFamily: "data_news" };
    if (selectedRoute === "remotion_card_stack") return { ...base, remotionFamily: "card_stack" };
    return base;
  };

  // V1.2.1: Generate information structure
  const callGenerateInformationStructure = async () => {
    const fingerprint = getCurrentInputFingerprint();
    setInfoSummaryLoading(true);
    setInfoSummaryError("");

    try {
      const resp = await fetch(`${API_BASE}/information-structure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: [title.trim(), body.trim()].filter(Boolean).join("\n\n"),
          compression_mode: compressionMode,
          target_point_count: targetPointCount,
          include_overview: includeOverview,
          include_conclusion: includeConclusion,
          evidence_policy: evidencePolicy,
          target_duration_mode: targetDurationMode,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
      setInfoSummaryPlan(data.plan as InformationSummaryPlan);
      setInfoSummaryInputFingerprint(fingerprint);
    } catch (e) {
      setInfoSummaryError(String(e));
    } finally {
      setInfoSummaryLoading(false);
    }
  };

  // ── Preview ─────────────────────────────────────────────────────────────
  const callPreview = async () => {
    if (selectedRouteUnavailable) {
      setPreviewError(selectedAvailability?.availabilityMessage || "Selected route is not available");
      return;
    }
    // V1.2.1.1: Validate plan freshness in information_summary mode
    if (generationMode === "information_summary") {
      const currentFingerprint = getCurrentInputFingerprint();
      if (!infoSummaryPlan || infoSummaryInputFingerprint !== currentFingerprint) {
        setPreviewError("输入已变化，请先重新生成信息结构。");
        return;
      }
    }
    setPreviewLoading(true);
    setPreviewError("");
    setPreviewResult(null);
    setReviewStatus("pending");
    setSavedSampleId(null);
    setSaveError("");
    setSaveSuccess("");
    setCompareError("");
    setCompareSuccess(false);

    const visualRoute = selectedVisualRoute;
    const params = { ...buildVisualRouteParams(), clipSeconds: 3 };
    const content = buildGenerationContent();
    const shot = { headline: title.trim(), display: body.trim(), emphasisTerms: [] };
    let payload: Record<string, unknown>;

    if (selectedRoute === "pillow") {
      payload = {
        visualRoute,
        content,
        shot,
        frameType: "keypoint",
        coverTitle: title.trim(),
        params,
      };
    } else if (selectedRoute === "remotion_data_news") {
      payload = {
        visualRoute,
        content,
        shot: {},
        frameType: "keypoint",
        params,
      };
    } else if (selectedRoute === "remotion_card_stack") {
      payload = {
        visualRoute,
        content,
        shot: {},
        frameType: "keypoint",
        params,
      };
    } else if (selectedRoute === "ai_asset") {
      // AI 素材：单帧(AI 生图背景+叠卡) → Ken Burns 动效片段（需图像 API，较慢）
      payload = {
        visualRoute,
        content,
        shot,
        frameType: "keypoint",
        coverTitle: title.trim(),
        params,
      };
    } else {
      setPreviewError("未知路线");
      setPreviewLoading(false);
      return;
    }

    try {
      const resp = await fetch(`${API_BASE}/clip-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!resp.ok && !data) throw new Error(`${resp.status}`);
      if (!data.success) {
        const msg =
          data?.error?.message ||
          data?.message ||
          data?.detail ||
          data?.warnings?.join("；") ||
          "预览生成失败";
        setPreviewResult({
          experimentId: data.experimentId || data.jobRun?.experimentId || "—",
          success: false,
          videoUrl: "",
          runtimePath: "",
          elapsedMs: data.elapsedMs || 0,
          route: data.route || selectedRoute,
          message: data.message || "",
          failedReason: msg,
          jobRun: (data.jobRun as JobRun | undefined) || undefined,
        });
        setPreviewError("");
        return;
      }

      setPreviewResult({
        experimentId: data.experimentId || "—",
        success: true,
        videoUrl: data.clipUrl || data.videoUrl || data.artifacts?.videoUrl || "",
        runtimePath: data.clipPath || data.runtimePath || data.artifacts?.videoUrl || "",
        elapsedMs: data.elapsedMs || 0,
        route: data.route || selectedRoute,
        message: data.message || "",
        failedReason: null,
        jobRun: (data.jobRun as JobRun | undefined) || undefined,
      });
    } catch (e) {
      setPreviewError(String(e));
    } finally {
      setPreviewLoading(false);
    }
  };

  // ── Full Video ───────────────────────────────────────────────────────────
  const callFullVideo = async () => {
    if (selectedRouteUnavailable) {
      setFullError(selectedAvailability?.availabilityMessage || "Selected route is not available");
      return;
    }
    // V1.2.1.1: Validate plan freshness in information_summary mode
    if (generationMode === "information_summary") {
      const currentFingerprint = getCurrentInputFingerprint();
      if (!infoSummaryPlan || infoSummaryInputFingerprint !== currentFingerprint) {
        setFullError("输入已变化，请先重新生成信息结构。");
        setFullLoading(false);
        return;
      }
    }
    setFullLoading(true);
    setFullError("");
    setFullResult(null);
    setReviewStatus("pending");
    setSavedSampleId(null);
    setSaveError("");
    setSaveSuccess("");
    setCompareError("");
    setCompareSuccess(false);

    const visualRoute = selectedVisualRoute;
    if (!visualRoute) {
      setFullError("该路线不支持完整视频生成");
      setFullLoading(false);
      return;
    }

    try {
      const resp = await fetch(`${API_BASE}/visual-compose`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: buildGenerationContent(),
          visualRoute,
          params: buildVisualRouteParams(),
        }),
      });
      const data = await resp.json();
      if (!resp.ok && !data) throw new Error(`${resp.status}`);
      if (data.detail) throw new Error(data.detail);

      setFullResult(data as FullVideoResult);
    } catch (e) {
      setFullError(String(e));
    } finally {
      setFullLoading(false);
    }
  };

  // ── Save Approved Sample ─────────────────────────────────────────────────
  const saveApprovedSample = async (status: "approved" | "rejected" = "approved"): Promise<string | null> => {
    if (!fullResult || fullResult.status !== "succeeded" || !fullResult.finalVideoUrl) return null;
    const sampleMeta = ROUTE_SAMPLE_META[selectedRoute];
    if (!sampleMeta) return null;

    setSaveLoading(true);
    setSaveError("");
    setSaveSuccess("");

    try {
      const resp = await fetch(`${API_BASE}/style-samples`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: `workbench_${fullResult.experimentId}`,
          route_id: sampleMeta.route_id,
          route_name: sampleMeta.route_name,
          style_name: sampleMeta.style_name,
          description: `Workbench ${status}: ${title.trim().slice(0, 80)}`,
          status,
          params: {
            ...(fullResult.params || {}),
            source: "workbench",
            workbenchRoute: selectedRoute,
            experimentId: fullResult.experimentId,
            reviewStatus: status,
            reviewNotes,
            quality: fullResult.quality || {},
            warnings: fullResult.warnings || [],
            steps: fullResult.steps || [],
            // V1.0.6: full content for reproducible rerun
            fullContent: buildGenerationContent(),
            contentHash: "",
          },
          output_type: "mp4",
          output_path: stripRuntimeUrlPrefix(fullResult.finalVideoUrl),
          poster_path: stripRuntimeUrlPrefix(fullResult.coverUrl || ""),
          audio_url: stripRuntimeUrlPrefix(fullResult.audioUrl || ""),
          srt_url: stripRuntimeUrlPrefix(fullResult.srtUrl || ""),
          manifest_url: stripRuntimeUrlPrefix(fullResult.manifestUrl || ""),
          content_preview: buildGenerationContent().slice(0, 160),
          duration_sec: Number(fullResult.audioDurationSec || 0),
          audio_duration_sec: Number(fullResult.audioDurationSec || 0),
          tags: ["workbench", selectedRoute, status],
          evaluation_notes: [
            reviewNotes,
            fullResult.quality?.overallScore != null ? `quality=${fullResult.quality.overallScore}` : "",
            fullResult.warnings?.length ? `warnings=${fullResult.warnings.join("；")}` : "",
          ].filter(Boolean).join("\n"),
          // V1.0.5: Experiment asset metadata
          source: {
            source_type: "workbench",
            source_page: "/video-lab/workbench",
            source_run_id: fullResult.jobRun?.runId || "",
            experiment_id: fullResult.experimentId || "",
            job_id: fullResult.jobRun?.jobId || "",
            run_id: fullResult.jobRun?.runId || "",
            workbench_route: selectedRoute,
            saved_from: "full_video_result",
          },
          generation: {
            visual_route: fullResult.visualRoute || "",
            visual_profile: String(fullResult.params?.visualProfile || ""),
            remotion_family: String(fullResult.params?.remotionFamily || ""),
            route_preset: selectedRoute,
            aspect_ratio: String(fullResult.params?.aspectRatio || "9:16"),
            target_duration: Number(fullResult.params?.targetDuration || 0),
            key_point_count: Number(fullResult.params?.keyPointCount || 0),
            content_hash: "",
          },
          asset_meta: {
            final_video_url: fullResult.finalVideoUrl || "",
            cover_url: fullResult.coverUrl || "",
            audio_url: fullResult.audioUrl || "",
            srt_url: fullResult.srtUrl || "",
            manifest_url: fullResult.manifestUrl || "",
            runtime_prefix: "",
            artifact_count: 0,
          },
          quality_meta: {
            structural_score: fullResult.quality?.overallScore ?? null,
            visual_score: null,
            warnings: fullResult.warnings || [],
            steps: fullResult.steps || [],
          },
          review_meta: {
            review_status: status,
            review_notes: reviewNotes,
            problem_tags: status === "rejected" ? ["problem"] : [],
          },
          job_run: fullResult.jobRun || {},
          schema_version: "1.0.5",
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);

      const savedId = data.id || `workbench_${fullResult.experimentId}`;
      setSavedSampleId(savedId);
      setSaveSuccess(status === "approved" ? `已保存为样片：${savedId}` : `已记录问题样片：${savedId}`);
      return savedId;
    } catch (e) {
      setSaveError(`保存失败：${String(e)}`);
      return null;
    } finally {
      setSaveLoading(false);
    }
  };

  // ── Mark Sample For Compare ──────────────────────────────────────────────
  const addSavedSampleToCompare = async () => {
    let sampleId = savedSampleId;

    // If not saved yet, save first
    if (!sampleId) {
      sampleId = await saveApprovedSample();
      if (!sampleId) return; // save failed, error already set
    }

    setCompareLoading(true);
    setCompareError("");

    try {
      const resp = await fetch(`${API_BASE}/style-samples/${sampleId}/compare`, { method: "POST" });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      setCompareSuccess(true);
      setCompareError("");
    } catch (e) {
      setCompareError(`加入对比失败：${String(e)}`);
    } finally {
      setCompareLoading(false);
    }
  };

  // ── Human Review ────────────────────────────────────────────────────────
  const recordProblemSample = async () => {
    await saveApprovedSample("rejected");
  };

  const hasFullVideo = fullResult && fullResult.status === "succeeded" && fullResult.finalVideoUrl;
  const hasPreview = previewResult && previewResult.success;

  const handleReview = (status: HumanReviewStatus) => {
    setReviewStatus(status);
  };

  const copyPath = async () => {
    const url = fullResult?.finalVideoUrl || previewResult?.videoUrl || "";
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // silent
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.4rem" }}>
          视频生成实验台
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.9rem" }}>
          输入内容 → 选择路线 → 生成预览 / 完整视频 → 人工观察确认 → 保存样片 / 加入对比
        </p>
      </div>

      {/* ── Section 1: Content Input ────────────────────────────────────── */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          1. 内容输入
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div>
            <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "#475569", display: "block", marginBottom: 4 }}>
              标题
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => { setTitle(e.target.value); clearInfoSummaryPlan(); }}
              placeholder="例如：今日 AI 前沿速递"
              style={{ width: "100%", padding: "0.55rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.9rem", boxSizing: "border-box" }}
            />
          </div>
          <div>
            <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "#475569", display: "block", marginBottom: 4 }}>
              正文（每段一个要点，用空行分隔）
            </label>
            <textarea
              value={body}
              onChange={(e) => { setBody(e.target.value); clearInfoSummaryPlan(); }}
              rows={8}
              style={{ width: "100%", padding: "0.55rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.85rem", fontFamily: "inherit", resize: "vertical", boxSizing: "border-box" }}
            />
          </div>
          <div>
            <button onClick={loadSample} style={{ background: "#f1f5f9", color: "#475569", border: "1px solid #e2e8f0", borderRadius: 8, padding: "0.4rem 0.9rem", fontSize: "0.8rem", cursor: "pointer" }}>
              加载示例内容（AI 新闻三条）
            </button>
          </div>
        </div>
      </div>

      {/* ── Section 2: Route Selection ──────────────────────────────────── */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          2. 路线选择
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
          {ROUTES.map((route) => (
            <RouteCard
              key={route.id}
              route={route}
              selected={selectedRoute === route.id}
              availability={routeAvailability[routeToVisualRoute[route.id]]}
              onSelect={() => {
                const unavailable = routeAvailability[routeToVisualRoute[route.id]]?.available === false;
                if (route.status !== "preview_only" && !unavailable) setSelectedRoute(route.id);
              }}
            />
          ))}
        </div>
        {routeAvailabilityError && (
          <div style={{ marginTop: "0.75rem", fontSize: "0.75rem", color: "#d97706" }}>
            路线可用性读取失败：{routeAvailabilityError}
          </div>
        )}
      </div>

      {/* ── Section 3: Generation Control ───────────────────────────────── */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          3. 生成控制
        </h2>
        <p style={{ fontSize: "0.78rem", color: "#64748b", marginBottom: "1rem" }}>
          预览用于快速看版式；完整视频会调用 TTS、字幕和 FFmpeg 合成，耗时更长（约 30-90 秒）。
        </p>

        {/* V1.2.1: Generation Mode Selector */}
        <div style={{ marginBottom: "1rem", padding: "0.75rem", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0" }}>
          <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "#1e293b", marginBottom: "0.5rem" }}>生成模式</div>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              onClick={() => { setGenerationMode("normal"); clearInfoSummaryPlan(); }}
              style={{
                padding: "0.35rem 0.85rem",
                borderRadius: 6,
                border: generationMode === "normal" ? "2px solid #0f766e" : "1px solid #e2e8f0",
                background: generationMode === "normal" ? "#f0fdfa" : "white",
                color: generationMode === "normal" ? "#0f766e" : "#64748b",
                fontSize: "0.78rem",
                fontWeight: generationMode === "normal" ? 600 : 400,
                cursor: "pointer",
              }}
            >
              普通视频
            </button>
            <button
              onClick={() => { setGenerationMode("information_summary"); clearInfoSummaryPlan(); }}
              style={{
                padding: "0.35rem 0.85rem",
                borderRadius: 6,
                border: generationMode === "information_summary" ? "2px solid #7c3aed" : "1px solid #e2e8f0",
                background: generationMode === "information_summary" ? "#f5f3ff" : "white",
                color: generationMode === "information_summary" ? "#7c3aed" : "#64748b",
                fontSize: "0.78rem",
                fontWeight: generationMode === "information_summary" ? 600 : 400,
                cursor: "pointer",
              }}
            >
              📋 信息总结视频
            </button>
          </div>

          {/* V1.2.1: Information Summary Controls */}
          {generationMode === "information_summary" && (
            <div style={{ marginTop: "0.85rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.5rem" }}>
                {/* Compression Mode */}
                <div>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>内容处理模式</label>
                  <select
                    value={compressionMode}
                    onChange={(e) => { setCompressionMode(e.target.value as CompressionMode); clearInfoSummaryPlan(); }}
                    style={{ width: "100%", padding: "0.3rem 0.5rem", border: "1px solid #e2e8f0", borderRadius: 6, fontSize: "0.78rem" }}
                  >
                    <option value="brief">精简摘要（保留 3 条）</option>
                    <option value="balanced">均衡总结（保留 5-7 条）</option>
                    <option value="strict">严格保留（尽量全部保留）</option>
                    <option value="itemized">逐条展开（每条单独成卡）</option>
                    <option value="manual">手动分段</option>
                  </select>
                </div>

                {/* Target Point Count */}
                <div>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>目标信息点数量</label>
                  <select
                    value={targetPointCount}
                    onChange={(e) => { setTargetPointCount(e.target.value as TargetPointCount); clearInfoSummaryPlan(); }}
                    style={{ width: "100%", padding: "0.3rem 0.5rem", border: "1px solid #e2e8f0", borderRadius: 6, fontSize: "0.78rem" }}
                  >
                    <option value="auto">自动</option>
                    <option value="3">3 条</option>
                    <option value="5">5 条</option>
                    <option value="8">8 条</option>
                    <option value="all">全部主要信息点</option>
                  </select>
                </div>

                {/* Target Duration */}
                <div>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>目标视频时长</label>
                  <select
                    value={targetDurationMode}
                    onChange={(e) => { setTargetDurationMode(e.target.value as DurationMode); clearInfoSummaryPlan(); }}
                    style={{ width: "100%", padding: "0.3rem 0.5rem", border: "1px solid #e2e8f0", borderRadius: 6, fontSize: "0.78rem" }}
                  >
                    <option value="auto">自动匹配信息量</option>
                    <option value="30">30 秒快讯</option>
                    <option value="60">60 秒标准总结</option>
                    <option value="90">90 秒完整展开</option>
                  </select>
                </div>

                {/* Evidence Policy */}
                <div>
                  <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>依据处理</label>
                  <select
                    value={evidencePolicy}
                    onChange={(e) => { setEvidencePolicy(e.target.value as EvidencePolicy); clearInfoSummaryPlan(); }}
                    style={{ width: "100%", padding: "0.3rem 0.5rem", border: "1px solid #e2e8f0", borderRadius: 6, fontSize: "0.78rem" }}
                  >
                    <option value="hide">隐藏</option>
                    <option value="badge">角标</option>
                    <option value="ending_sources">片尾来源</option>
                    <option value="keep_inline">原文保留</option>
                  </select>
                </div>
              </div>

              {/* Structure Options Toggles */}
              <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.78rem", color: "#475569", cursor: "pointer" }}>
                  <input type="checkbox" checked={includeOverview} onChange={(e) => { setIncludeOverview(e.target.checked); clearInfoSummaryPlan(); }} />
                  生成首页总览
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.78rem", color: "#475569", cursor: "pointer" }}>
                  <input type="checkbox" checked={includeConclusion} onChange={(e) => { setIncludeConclusion(e.target.checked); clearInfoSummaryPlan(); }} />
                  生成尾部总结
                </label>
              </div>

              {/* Generate Information Structure Button */}
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginTop: "0.25rem" }}>
                <button
                  onClick={callGenerateInformationStructure}
                  disabled={infoSummaryLoading}
                  style={{
                    padding: "0.4rem 1rem",
                    borderRadius: 6,
                    border: "none",
                    background: infoSummaryLoading ? "#94a3b8" : "#7c3aed",
                    color: "white",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    cursor: infoSummaryLoading ? "not-allowed" : "pointer",
                  }}
                >
                  {infoSummaryLoading ? "分析中..." : "📋 生成信息结构"}
                </button>
                {/* V1.2.1.1: Show stale warning or current status */}
                {(() => {
                  const currentFp = getCurrentInputFingerprint();
                  const isStale = !infoSummaryPlan || infoSummaryInputFingerprint !== currentFp;
                  if (isStale && (title.trim() || body.trim())) {
                    return <span style={{ fontSize: "0.75rem", color: "#d97706" }}>⚠️ 输入已变化，请重新生成信息结构</span>;
                  }
                  if (infoSummaryPlan) {
                    return <span style={{ fontSize: "0.75rem", color: "#16a34a" }}>✅ 已基于当前输入生成：识别 {infoSummaryPlan.stats.detectedItemCount} 条，保留 {infoSummaryPlan.stats.selectedItemCount} 条（预计 {infoSummaryPlan.stats.estimatedDurationSec}s）</span>;
                  }
                  return <span style={{ fontSize: "0.75rem", color: "#64748b" }}>当前输入：标题 {title.trim().length} 字，正文 {body.trim().length} 字</span>;
                })()}
              </div>

              {infoSummaryError && (
                <div style={{ fontSize: "0.75rem", color: "#dc2626" }}>错误：{infoSummaryError}</div>
              )}

              {/* V1.2.1: Information Structure Preview */}
              {infoSummaryPlan && (
                <div style={{ marginTop: "0.5rem", padding: "0.75rem", background: "white", borderRadius: 8, border: "1px solid #ddd", maxHeight: 320, overflowY: "auto" }}>
                  <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#1e293b", marginBottom: "0.5rem" }}>📋 信息结构预览</div>

                  {/* V1.2.1.1: Show structure source / fingerprint */}
                  <div style={{ fontSize: "0.68rem", color: "#94a3b8", marginBottom: "0.4rem", padding: "0.25rem 0.5rem", background: "#f8fafc", borderRadius: 4 }}>
                    📌 结构来源：标题「{title.trim().slice(0, 20) || "（无）"}」，正文 {body.trim().length} 字
                    {infoSummaryInputFingerprint && (
                      <span> · 指纹 {infoSummaryInputFingerprint.slice(0, 30)}...</span>
                    )}
                  </div>

                  {infoSummaryPlan.includeOverview && infoSummaryPlan.overview && (
                    <div style={{ marginBottom: "0.6rem", padding: "0.5rem", background: "#f0fdfa", borderRadius: 6, borderLeft: "3px solid #0f766e" }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "#0f766e" }}>🏠 首页总览：{infoSummaryPlan.overview.title}</div>
                      {infoSummaryPlan.overview.summary && (
                        <div style={{ fontSize: "0.7rem", color: "#475569", marginTop: 2 }}>{infoSummaryPlan.overview.summary.slice(0, 80)}...</div>
                      )}
                    </div>
                  )}

                  <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "#475569", marginBottom: "0.3rem" }}>
                    📌 信息点（{infoSummaryPlan.stats.selectedItemCount}/{infoSummaryPlan.stats.detectedItemCount} 已选）
                  </div>
                  {infoSummaryPlan.items.map((item, i) => (
                    <div key={item.id} style={{ marginBottom: "0.4rem", padding: "0.4rem 0.5rem", background: "#f8fafc", borderRadius: 5, borderLeft: `3px solid ${item.selected ? "#16a34a" : "#94a3b8"}` }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 600, color: item.selected ? "#16a34a" : "#94a3b8" }}>
                        {i + 1}. {item.title || "(无标题)"}
                      </div>
                      {item.description && (
                        <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: 1 }}>{item.description.slice(0, 60)}{item.description.length > 60 ? "..." : ""}</div>
                      )}
                      {item.evidence && item.evidence.length > 0 && (
                        <div style={{ fontSize: "0.65rem", color: "#94a3b8", marginTop: 1 }}>依据：{item.evidence.join("、")}</div>
                      )}
                    </div>
                  ))}

                  {infoSummaryPlan.stats.droppedItemCount > 0 && (
                    <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginTop: "0.3rem", fontStyle: "italic" }}>
                      ⏭ {infoSummaryPlan.stats.droppedItemCount} 条已省略（篇幅限制）
                    </div>
                  )}

                  {infoSummaryPlan.includeConclusion && infoSummaryPlan.conclusion && (
                    <div style={{ marginTop: "0.6rem", padding: "0.5rem", background: "#f5f3ff", borderRadius: 6, borderLeft: "3px solid #7c3aed" }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "#7c3aed" }}>🔚 尾部总结：{infoSummaryPlan.conclusion.title}</div>
                      {infoSummaryPlan.conclusion.text && (
                        <div style={{ fontSize: "0.7rem", color: "#475569", marginTop: 2 }}>{infoSummaryPlan.conclusion.text.slice(0, 80)}...</div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap", marginBottom: "0.75rem" }}>
          <button
            onClick={callPreview}
            disabled={previewLoading || selectedRouteUnavailable}
            style={{
              background: previewLoading || selectedRouteUnavailable ? "#94a3b8" : "#0f766e",
              color: "white", border: "none", borderRadius: 8,
              padding: "0.6rem 1.5rem", fontSize: "0.9rem", fontWeight: 600,
              cursor: previewLoading || selectedRouteUnavailable ? "not-allowed" : "pointer",
            }}
          >
            {previewLoading ? "预览生成中..." : "生成预览"}
          </button>

          <button
            onClick={callFullVideo}
            disabled={fullLoading || selectedRouteUnavailable}
            style={{
              background: fullLoading || selectedRouteUnavailable ? "#94a3b8" : "#7c3aed",
              color: "white", border: "none", borderRadius: 8,
              padding: "0.6rem 1.5rem", fontSize: "0.9rem", fontWeight: 600,
              cursor: fullLoading || selectedRouteUnavailable ? "not-allowed" : "pointer",
            }}
          >
            {fullLoading ? "完整视频生成中（约 30-90 秒）..." : "生成完整视频"}
          </button>

          {(previewLoading || fullLoading) && (
            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
              {previewLoading ? "预览生成中" : fullLoading ? "完整视频生成中" : ""}，路线：{ROUTES.find((r) => r.id === selectedRoute)?.name}
            </span>
          )}
        </div>

        {selectedRouteUnavailable && (
          <div style={{ fontSize: "0.78rem", color: "#dc2626", marginBottom: "0.5rem" }}>
            当前路线不可用：{selectedAvailability?.availabilityMessage}
          </div>
        )}

        {selectedRoute === "ai_asset" && (
          <div style={{ fontSize: "0.78rem", color: "#94a3b8", marginBottom: "0.5rem" }}>
            AI 素材路线会先调用图像 API 生成背景图，预览与完整视频都比其它路线慢、且消耗 API 额度。
          </div>
        )}

        {previewError && (
          <div style={{ marginTop: "0.75rem", padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.82rem", color: "#dc2626" }}>
            预览错误：{previewError}
            <button onClick={() => setPreviewError("")} style={{ marginLeft: 12, background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: "0.82rem", textDecoration: "underline" }}>关闭</button>
          </div>
        )}

        {fullError && (
          <div style={{ marginTop: "0.75rem", padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.82rem", color: "#dc2626" }}>
            完整视频错误：{fullError}
            <button onClick={() => setFullError("")} style={{ marginLeft: 12, background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: "0.82rem", textDecoration: "underline" }}>关闭</button>
          </div>
        )}
      </div>

      {/* ── Section 4: Result Viewing ───────────────────────────────────── */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          4. 结果观看
        </h2>

        {/* Preview */}
        <div style={{ marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#475569", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: 8 }}>
            <span>预览结果</span>
            {previewLoading && <span style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 400 }}>⏳ 生成中...</span>}
          </div>

          {!previewResult && !previewLoading && (
            <div style={{ textAlign: "center", padding: "1.5rem", color: "#94a3b8", fontSize: "0.82rem" }}>点击上方「生成预览」</div>
          )}

          {previewResult && previewResult.success && (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem", fontSize: "0.75rem", color: "#64748b" }}>
                <span>experiment_id：<span style={{ color: "#1e293b", fontFamily: "monospace" }}>{previewResult.experimentId}</span></span>
                <span>路线：<span style={{ color: "#1e293b" }}>{previewResult.route}</span></span>
                <span>耗时：<span style={{ color: "#1e293b" }}>{previewResult.elapsedMs}ms</span></span>
                <span>地址：<span style={{ color: "#1e293b", fontFamily: "monospace", wordBreak: "break-all" }}>{previewResult.videoUrl}</span></span>
              </div>
              {previewResult.videoUrl && (
                <video controls src={resolveUrl(previewResult.videoUrl)} style={{ width: "100%", maxWidth: 400, borderRadius: 8, background: "#0f172a" }} />
              )}

              <JobRunPanel jobRun={previewResult.jobRun} />
            </div>
          )}

          {previewResult && !previewResult.success && (
            <div style={{ padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.82rem", color: "#dc2626" }}>
              预览失败：{previewResult.failedReason || previewResult.message || "未知错误"}
              <JobRunPanel jobRun={previewResult.jobRun} />
            </div>
          )}
        </div>

        <div style={{ borderTop: "1px solid #e2e8f0", marginBottom: "1.5rem" }} />

        {/* Full Video */}
        <div>
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#475569", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: 8 }}>
            <span>完整视频</span>
            {fullLoading && <span style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 400 }}>⏳ 生成中...</span>}
          </div>

          {!fullResult && !fullLoading && (
            <div style={{ textAlign: "center", padding: "1.5rem", color: "#94a3b8", fontSize: "0.82rem" }}>点击上方「生成完整视频」</div>
          )}

          {fullResult && fullResult.status === "succeeded" && fullResult.finalVideoUrl && (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem", fontSize: "0.75rem", color: "#64748b" }}>
                <span>experiment_id：<span style={{ color: "#1e293b", fontFamily: "monospace" }}>{fullResult.experimentId}</span></span>
                <span>visualRoute：<span style={{ color: "#1e293b" }}>{fullResult.visualRoute}</span></span>
                <span>status：<span style={{ color: "#16a34a" }}>{fullResult.status}</span></span>
                <span>audioDuration：<span style={{ color: "#1e293b" }}>{fullResult.audioDurationSec}s</span></span>
                <span>subtitleCount：<span style={{ color: "#1e293b" }}>{fullResult.subtitleCount ?? "—"}</span></span>
                <span>地址：<span style={{ color: "#1e293b", fontFamily: "monospace", wordBreak: "break-all" }}>{fullResult.finalVideoUrl}</span></span>
              </div>

              {(fullResult.audioUrl || fullResult.srtUrl || fullResult.manifestUrl) && (
                <div style={{ marginBottom: "0.75rem", fontSize: "0.75rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                  {fullResult.audioUrl && <a href={resolveUrl(fullResult.audioUrl)} target="_blank" rel="noreferrer" style={{ color: "#7c3aed" }}>音频</a>}
                  {fullResult.srtUrl && <a href={resolveUrl(fullResult.srtUrl)} target="_blank" rel="noreferrer" style={{ color: "#7c3aed" }}>字幕</a>}
                  {fullResult.manifestUrl && <a href={resolveUrl(fullResult.manifestUrl)} target="_blank" rel="noreferrer" style={{ color: "#7c3aed" }}>Manifest</a>}
                </div>
              )}

              {fullResult.warnings && fullResult.warnings.length > 0 && (
                <div style={{ marginBottom: "0.75rem", padding: "0.5rem 0.75rem", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 6, fontSize: "0.75rem", color: "#92400e" }}>
                  警告：{fullResult.warnings.join("；")}
                </div>
              )}

              {fullResult.quality && fullResult.quality.overallScore != null && (
                <div style={{ marginBottom: "0.75rem", padding: "0.65rem 0.75rem", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.75rem", color: "#475569" }}>
                  <div style={{ fontWeight: 700, color: "#1e293b", marginBottom: 4 }}>
                    结构质量分：{fullResult.quality.overallScore}
                  </div>
                  {fullResult.quality.dimensionScores && (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {Object.entries(fullResult.quality.dimensionScores).map(([key, value]) => (
                        <span key={key}>{key}: {value}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {fullResult.steps && fullResult.steps.length > 0 && (
                <details style={{ marginBottom: "0.75rem", fontSize: "0.75rem", color: "#475569" }}>
                  <summary style={{ cursor: "pointer", fontWeight: 600, color: "#334155" }}>生成步骤</summary>
                  <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 4 }}>
                    {fullResult.steps.map((step, idx) => (
                      <div key={`${step.name}-${idx}`} style={{ display: "grid", gridTemplateColumns: "110px 1fr", gap: 8 }}>
                        <span style={{ color: step.status === "failed" ? "#dc2626" : "#64748b" }}>{step.status}</span>
                        <span>{step.name}{step.output ? `：${step.output}` : ""}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}

              <video controls src={resolveUrl(fullResult.finalVideoUrl)} style={{ width: "100%", maxWidth: 480, borderRadius: 8, background: "#0f172a" }} />

              <JobRunPanel jobRun={fullResult.jobRun} />
            </div>
          )}

          {fullResult && fullResult.status !== "succeeded" && (
            <div style={{ padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.82rem", color: "#dc2626" }}>
              生成失败：{fullResult.failedReason || "未知错误"}
              <JobRunPanel jobRun={fullResult.jobRun} />
            </div>
          )}
        </div>
      </div>

      {/* ── Section 5: Human Review ──────────────────────────────────────── */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          5. 人工观察确认
          {hasFullVideo && (
            <span style={{ marginLeft: 10 }}>
              <ReviewBadge status={reviewStatus} />
            </span>
          )}
        </h2>

        {!hasFullVideo && !hasPreview && (
          <div style={{ textAlign: "center", padding: "1.5rem", color: "#94a3b8", fontSize: "0.85rem" }}>
            生成视频后才可进行人工确认
          </div>
        )}

        {hasFullVideo && (
          <>
            <p style={{ fontSize: "0.82rem", color: "#475569", marginBottom: "1rem" }}>
              请播放完整视频后，判断该视频是否可用：
            </p>

            <div style={{ display: "flex", gap: "0.6rem", marginBottom: "1rem", flexWrap: "wrap" }}>
              <button
                onClick={() => handleReview("approved")}
                style={{
                  background: reviewStatus === "approved" ? "#16a34a" : "#f0fdf4",
                  color: reviewStatus === "approved" ? "white" : "#16a34a",
                  border: `1px solid ${reviewStatus === "approved" ? "#16a34a" : "#bbf7d0"}`,
                  borderRadius: 8, padding: "0.5rem 1.2rem", fontSize: "0.85rem", fontWeight: 600, cursor: "pointer",
                }}
              >
                ✅ 通过
              </button>
              <button
                onClick={() => handleReview("problem")}
                style={{
                  background: reviewStatus === "problem" ? "#d97706" : "#fffbeb",
                  color: reviewStatus === "problem" ? "white" : "#d97706",
                  border: `1px solid ${reviewStatus === "problem" ? "#d97706" : "#fde68a"}`,
                  borderRadius: 8, padding: "0.5rem 1.2rem", fontSize: "0.85rem", fontWeight: 600, cursor: "pointer",
                }}
              >
                ⚠️ 有问题
              </button>
              <button
                onClick={() => handleReview("discarded")}
                style={{
                  background: reviewStatus === "discarded" ? "#dc2626" : "#fef2f2",
                  color: reviewStatus === "discarded" ? "white" : "#dc2626",
                  border: `1px solid ${reviewStatus === "discarded" ? "#dc2626" : "#fecaca"}`,
                  borderRadius: 8, padding: "0.5rem 1.2rem", fontSize: "0.85rem", fontWeight: 600, cursor: "pointer",
                }}
              >
                ❌ 丢弃
              </button>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ fontSize: "0.78rem", fontWeight: 600, color: "#475569", display: "block", marginBottom: 4 }}>
                观察备注
              </label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                rows={3}
                style={{ width: "100%", padding: "0.55rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.82rem", fontFamily: "inherit", resize: "vertical", boxSizing: "border-box" }}
              />
            </div>

            {/* ── Approved Actions ── */}
            {reviewStatus === "approved" && (
              <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, padding: "1rem", marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "#166534", marginBottom: "0.75rem" }}>
                  视频通过 — 选择后续操作：
                </div>

                {/* Save / Compare status */}
                <div style={{ fontSize: "0.75rem", color: "#475569", marginBottom: "0.75rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                  {saveSuccess && <div style={{ color: "#16a34a" }}>✅ {saveSuccess}</div>}
                  {saveError && <div style={{ color: "#dc2626" }}>❌ {saveError}</div>}
                  {compareSuccess && <div style={{ color: "#16a34a" }}>✅ 已加入对比</div>}
                  {compareError && <div style={{ color: "#dc2626" }}>❌ {compareError}</div>}
                </div>

                <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap", alignItems: "center" }}>
                  {savedSampleId ? (
                    <span style={{ fontSize: "0.78rem", color: "#16a34a", fontWeight: 600 }}>
                      ✅ 已保存：{savedSampleId}
                    </span>
                  ) : (
                    <button
                      onClick={() => saveApprovedSample()}
                      disabled={saveLoading}
                      style={{
                        background: saveLoading ? "#94a3b8" : "#0f766e",
                        color: "white", border: "none", borderRadius: 8,
                        padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: 600,
                        cursor: saveLoading ? "not-allowed" : "pointer",
                      }}
                    >
                      {saveLoading ? "保存中..." : "💾 保存为样片"}
                    </button>
                  )}

                  <button
                    onClick={addSavedSampleToCompare}
                    disabled={compareLoading}
                    style={{
                      background: compareLoading ? "#94a3b8" : "#7c3aed",
                      color: "white", border: "none", borderRadius: 8,
                      padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: 600,
                      cursor: compareLoading ? "not-allowed" : "pointer",
                    }}
                  >
                    {compareLoading ? "加入中..." : compareSuccess ? "✅ 已加入对比" : "⚖️ 加入对比"}
                  </button>

                  <button
                    onClick={copyPath}
                    style={{
                      background: copied ? "#16a34a" : "#f1f5f9",
                      color: copied ? "white" : "#475569",
                      border: "1px solid #e2e8f0", borderRadius: 8,
                      padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: 600,
                      cursor: "pointer", transition: "background 0.2s",
                    }}
                  >
                    {copied ? "✅ 已复制" : "📋 复制完整视频路径"}
                  </button>

                  {compareSuccess && (
                    <Link
                      to={
                        savedSampleId
                          ? `/video-lab/style-gallery?tab=gallery&source=workbench&sample_id=${encodeURIComponent(savedSampleId)}`
                          : "/video-lab/style-gallery?tab=gallery&source=workbench"
                      }
                      style={{
                        fontSize: "0.78rem", color: "#7c3aed",
                        textDecoration: "none", border: "1px solid #7c3aed",
                        borderRadius: 8, padding: "0.5rem 1rem",
                      }}
                    >
                      查看样片库 →
                    </Link>
                  )}
                </div>
              </div>
            )}

            {/* ── Problem Actions ── */}
            {reviewStatus === "problem" && (
              <div style={{ display: "flex", gap: "0.6rem" }}>
                <button
                  onClick={callFullVideo}
                  style={{ background: "#d97706", color: "white", border: "none", borderRadius: 8, padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: 600, cursor: "pointer" }}
                >
                  🔄 重新生成
                </button>
                <button
                  onClick={recordProblemSample}
                  disabled={saveLoading}
                  style={{
                    background: saveLoading ? "#f1f5f9" : "#fff7ed",
                    color: saveLoading ? "#94a3b8" : "#c2410c",
                    border: "1px solid #fed7aa",
                    borderRadius: 8,
                    padding: "0.5rem 1.1rem",
                    fontSize: "0.82rem",
                    cursor: saveLoading ? "not-allowed" : "pointer",
                  }}
                >
                  {saveLoading ? "记录中..." : "📝 记录问题样片"}
                </button>
                {(saveSuccess || saveError) && (
                  <span style={{ alignSelf: "center", fontSize: "0.75rem", color: saveError ? "#dc2626" : "#16a34a" }}>
                    {saveError || saveSuccess}
                  </span>
                )}
              </div>
            )}

            {/* ── Discarded ── */}
            {reviewStatus === "discarded" && (
              <div style={{ padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.82rem", color: "#dc2626" }}>
                已丢弃，不建议保存。如需重新生成，请再次点击「生成完整视频」。
              </div>
            )}
          </>
        )}

        {hasPreview && !hasFullVideo && (
          <div style={{ textAlign: "center", padding: "1rem", color: "#94a3b8", fontSize: "0.82rem" }}>
            当前仅生成预览（{previewResult?.videoUrl ? "可播放" : "播放失败"}）。完整视频生成后可做最终确认。
          </div>
        )}
      </div>

      {/* Back link */}
      <div style={{ textAlign: "center" }}>
        <Link to="/video-lab" style={{ color: "#64748b", textDecoration: "none", fontSize: "0.85rem" }}>
          ← 返回 Video Lab 首页
        </Link>
      </div>
    </div>
  );
}
