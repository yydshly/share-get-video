// Video Generation Workbench Page - V0.7.2
// 视频生成实验台 V0.7.2：approved 后保存样片 / 加入对比真实功能

import { useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

// ─── Types ───────────────────────────────────────────────────────────────────

type RouteId = "pillow" | "remotion_data_news" | "remotion_card_stack" | "ai_asset";
type HumanReviewStatus = "pending" | "approved" | "problem" | "discarded";

interface PreviewResult {
  experimentId: string;
  success: boolean;
  videoUrl: string;
  runtimePath: string;
  elapsedMs: number;
  route: string;
  message: string;
  failedReason: string | null;
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
  params?: Record<string, unknown>;
  steps?: Array<{ name: string; status: string; output: string }>;
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
    status: "preview_only",
    note: "暂未接入完整视频生成",
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
  ai_asset: null,
};

// ─── Helpers ────────────────────────────────────────────────────────────────

const stripRuntimePrefix = (url: string) =>
  url.startsWith("/runtime/") ? url.replace(/^\/runtime\//, "") : url;

// ─── Component ───────────────────────────────────────────────────────────────

function RouteCard({
  route,
  selected,
  onSelect,
}: {
  route: RouteOption;
  selected: boolean;
  onSelect: () => void;
}) {
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
      onClick={route.status === "preview_only" ? undefined : onSelect}
      style={{
        border: selected ? "2px solid #0f766e" : "1px solid #e2e8f0",
        borderRadius: 12,
        padding: "0.85rem 1rem",
        background: selected ? "#f0fdfa" : "white",
        cursor: route.status === "preview_only" ? "not-allowed" : "pointer",
        opacity: route.status === "preview_only" ? 0.6 : 1,
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

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function VideoGenerationWorkbenchPage() {
  // ── Section 1: Content Input ────────────────────────────────────────────
  const [title, setTitle] = useState(SAMPLE_CONTENT.title);
  const [body, setBody] = useState(SAMPLE_CONTENT.body);

  // ── Section 2: Route Selection ──────────────────────────────────────────
  const [selectedRoute, setSelectedRoute] = useState<RouteId>("pillow");

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
  };

  const resolveUrl = (u: string) =>
    u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u || "";

  const routeToVisualRoute: Record<RouteId, string> = {
    pillow: "local_frame_compose",
    remotion_data_news: "template_programmatic_render",
    remotion_card_stack: "template_programmatic_render",
    ai_asset: "ai_asset_then_compose",
  };

  const buildVisualRouteParams = (): Record<string, unknown> => {
    const base = { targetDuration: 45, aspectRatio: "9:16", keyPointCount: 3, useLlmPlan: true };
    if (selectedRoute === "remotion_data_news") return { ...base, remotionFamily: "data_news" };
    if (selectedRoute === "remotion_card_stack") return { ...base, remotionFamily: "card_stack" };
    return base;
  };

  // ── Preview ─────────────────────────────────────────────────────────────
  const callPreview = async () => {
    setPreviewLoading(true);
    setPreviewError("");
    setPreviewResult(null);
    setReviewStatus("pending");
    setSavedSampleId(null);
    setSaveError("");
    setSaveSuccess("");
    setCompareError("");
    setCompareSuccess(false);

    const shot = { headline: title.trim(), display: body.trim(), emphasisTerms: [] };
    let payload: Record<string, unknown>;

    if (selectedRoute === "pillow") {
      payload = {
        visualRoute: "local_frame_compose",
        content: body.trim(),
        shot,
        frameType: "keypoint",
        coverTitle: title.trim(),
        params: { clipSeconds: 3, aspectRatio: "9:16" },
      };
    } else if (selectedRoute === "remotion_data_news") {
      payload = {
        visualRoute: "template_programmatic_render",
        content: body.trim(),
        shot: {},
        frameType: "keypoint",
        params: { clipSeconds: 3, aspectRatio: "9:16", keyPointCount: 3, remotionFamily: "data_news" },
      };
    } else if (selectedRoute === "remotion_card_stack") {
      payload = {
        visualRoute: "template_programmatic_render",
        content: body.trim(),
        shot: {},
        frameType: "keypoint",
        params: { clipSeconds: 3, aspectRatio: "9:16", keyPointCount: 3, remotionFamily: "card_stack" },
      };
    } else {
      setPreviewError("AI 素材路线暂未接入预览");
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
      if (!data.success) throw new Error(data.message || "预览生成失败");

      setPreviewResult({
        experimentId: data.experimentId || "—",
        success: true,
        videoUrl: data.clipUrl || data.videoUrl || "",
        runtimePath: data.clipPath || data.runtimePath || "",
        elapsedMs: data.elapsedMs || 0,
        route: data.route || selectedRoute,
        message: data.message || "",
        failedReason: null,
      });
    } catch (e) {
      setPreviewError(String(e));
    } finally {
      setPreviewLoading(false);
    }
  };

  // ── Full Video ───────────────────────────────────────────────────────────
  const callFullVideo = async () => {
    setFullLoading(true);
    setFullError("");
    setFullResult(null);
    setReviewStatus("pending");
    setSavedSampleId(null);
    setSaveError("");
    setSaveSuccess("");
    setCompareError("");
    setCompareSuccess(false);

    const visualRoute = routeToVisualRoute[selectedRoute];
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
          content: body.trim(),
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
  const saveApprovedSample = async (): Promise<string | null> => {
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
          description: `Workbench approved: ${title.trim().slice(0, 80)}`,
          status: "approved",
          params: {
            ...(fullResult.params || {}),
            source: "workbench",
            workbenchRoute: selectedRoute,
            experimentId: fullResult.experimentId,
            reviewNotes,
          },
          output_type: "mp4",
          output_path: stripRuntimePrefix(fullResult.finalVideoUrl),
          poster_path: stripRuntimePrefix(fullResult.coverUrl || ""),
          audio_url: stripRuntimePrefix(fullResult.audioUrl || ""),
          srt_url: stripRuntimePrefix(fullResult.srtUrl || ""),
          manifest_url: stripRuntimePrefix(fullResult.manifestUrl || ""),
          content_preview: body.trim().slice(0, 160),
          duration_sec: Number(fullResult.audioDurationSec || 0),
          audio_duration_sec: Number(fullResult.audioDurationSec || 0),
          tags: ["workbench", selectedRoute, "approved"],
          evaluation_notes: reviewNotes,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);

      const savedId = data.id || `workbench_${fullResult.experimentId}`;
      setSavedSampleId(savedId);
      setSaveSuccess(`已保存为样片：${savedId}`);
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
              onChange={(e) => setTitle(e.target.value)}
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
              onChange={(e) => setBody(e.target.value)}
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
              onSelect={() => { if (route.status !== "preview_only") setSelectedRoute(route.id); }}
            />
          ))}
        </div>
      </div>

      {/* ── Section 3: Generation Control ───────────────────────────────── */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1.25rem", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          3. 生成控制
        </h2>
        <p style={{ fontSize: "0.78rem", color: "#64748b", marginBottom: "1rem" }}>
          预览用于快速看版式；完整视频会调用 TTS、字幕和 FFmpeg 合成，耗时更长（约 30-90 秒）。
        </p>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap", marginBottom: "0.75rem" }}>
          <button
            onClick={callPreview}
            disabled={previewLoading || selectedRoute === "ai_asset"}
            style={{
              background: previewLoading || selectedRoute === "ai_asset" ? "#94a3b8" : "#0f766e",
              color: "white", border: "none", borderRadius: 8,
              padding: "0.6rem 1.5rem", fontSize: "0.9rem", fontWeight: 600,
              cursor: previewLoading || selectedRoute === "ai_asset" ? "not-allowed" : "pointer",
            }}
          >
            {previewLoading ? "预览生成中..." : "生成预览"}
          </button>

          <button
            onClick={callFullVideo}
            disabled={fullLoading || selectedRoute === "ai_asset"}
            style={{
              background: fullLoading || selectedRoute === "ai_asset" ? "#94a3b8" : "#7c3aed",
              color: "white", border: "none", borderRadius: 8,
              padding: "0.6rem 1.5rem", fontSize: "0.9rem", fontWeight: 600,
              cursor: fullLoading || selectedRoute === "ai_asset" ? "not-allowed" : "pointer",
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

        {selectedRoute === "ai_asset" && (
          <div style={{ fontSize: "0.78rem", color: "#94a3b8", marginBottom: "0.5rem" }}>
            AI 素材路线暂未接入完整视频生成
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
            </div>
          )}

          {previewResult && !previewResult.success && (
            <div style={{ padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.82rem", color: "#dc2626" }}>
              预览失败：{previewResult.failedReason || previewResult.message || "未知错误"}
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

              <video controls src={resolveUrl(fullResult.finalVideoUrl)} style={{ width: "100%", maxWidth: 480, borderRadius: 8, background: "#0f172a" }} />
            </div>
          )}

          {fullResult && fullResult.status !== "succeeded" && (
            <div style={{ padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.82rem", color: "#dc2626" }}>
              生成失败：{fullResult.failedReason || "未知错误"}
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
                      onClick={saveApprovedSample}
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
                      to="/video-lab/style-gallery"
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
                  style={{ background: "#f1f5f9", color: "#94a3b8", border: "1px solid #e2e8f0", borderRadius: 8, padding: "0.5rem 1.1rem", fontSize: "0.82rem", cursor: "not-allowed" }}
                >
                  📝 记录问题功能下一阶段接入
                </button>
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
