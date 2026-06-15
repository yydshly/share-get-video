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

// ─── 工具 ────────────────────────────────────────────────────────────────────

const resolveUrl = (u: string) =>
  u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u;

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
}: {
  sample: StyleSample;
  onDelete: (id: string) => void;
  onCompare: (id: string) => void;
  onSave: (s: StyleSample) => void;
  selectedForCompare: boolean;
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

      {/* 标签 */}
      {sample.tags.length > 0 && (
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

// ─── 主页面 ──────────────────────────────────────────────────────────────────

export default function StyleGalleryPage() {
  const [presets, setPresets] = useState<PresetStyle[]>([]);
  const [samples, setSamples] = useState<StyleSample[]>([]);
  const [filterRoute, setFilterRoute] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [generating, setGenerating] = useState<string | null>(null);
  const [compareSet, setCompareSet] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"presets" | "gallery">("presets");

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
    } catch (e) {
      setError("加载样片库失败: " + String(e));
    }
  }, [filterRoute, filterStatus]);

  useEffect(() => { loadPresets(); }, [loadPresets]);
  useEffect(() => { loadSamples(); }, [loadSamples]);

  const handleGenerate = async (preset: PresetStyle) => {
    setGenerating(preset.style_id);
    setError("");
    try {
      const resp = await fetch(`${API_BASE}/style-samples/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          style_name: preset.style_name,
          description: preset.description,
          route_id: preset.route_id,
          content: "",
          params: preset.params,
          tags: preset.tags,
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
          route_name: preset.route_name,
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
          tags: preset.tags,
        }),
      });
      loadSamples();
      setActiveTab("gallery");
    } catch (e) {
      setError("生成失败: " + String(e));
    } finally {
      setGenerating(null);
    }
  };

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
        V0.3.7 · 无数据库 · 每条路线独立风格探索 · 暂不升级为模板
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
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
