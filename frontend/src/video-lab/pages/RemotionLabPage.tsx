// Remotion 能力探索中心 - V1.2.4
// Lab-only 前端页面，用于探索 Remotion 的表现范式、背景、转场、视觉风格和候选模板。
// 不直接等同于正式 Style Sweep 生产模板。

import { useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

// ─── Types ────────────────────────────────────────────────────────────────────

interface BackgroundMatrixItem {
  family: string;
  backgroundPreset: string;
  success: boolean;
  videoUrl: string;
  elapsedMs: number;
  message: string;
}

interface BackgroundMatrixResponse {
  items: BackgroundMatrixItem[];
  totalElapsedMs: number;
}

interface TransitionMatrixItem {
  family: string;
  transitionStyle: string;
  success: boolean;
  videoUrl: string;
  elapsedMs: number;
  message: string;
}

interface TransitionMatrixResponse {
  items: TransitionMatrixItem[];
  totalElapsedMs: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const TABS = [
  { id: "paradigm", label: "表现范式" },
  { id: "background", label: "背景矩阵" },
  { id: "transition", label: "转场矩阵" },
  { id: "visual-style", label: "视觉风格" },
  { id: "candidate", label: "候选模板" },
  { id: "acceptance", label: "验收记录" },
] as const;

const BACKGROUNDS = [
  { id: "tech_grid_dark", label: "tech_grid_dark", desc: "深色科技网格" },
  { id: "aurora_blue", label: "aurora_blue", desc: "极光蓝" },
  { id: "glass_dashboard", label: "glass_dashboard", desc: "玻璃态看板" },
  { id: "warm_cinematic", label: "warm_cinematic", desc: "暖色电影感" },
  { id: "neon_circuit", label: "neon_circuit", desc: "霓虹电路（实验）" },
  { id: "deep_space", label: "deep_space", desc: "深空星云（实验）" },
];

const TRANSITIONS = [
  { id: "slide_fade", label: "slide_fade", desc: "滑动淡入淡出" },
  { id: "fade", label: "fade", desc: "纯淡入淡出" },
  { id: "slide", label: "slide", desc: "滑动" },
  { id: "push", label: "push", desc: "推进（实验）" },
  { id: "wipe", label: "wipe", desc: "扫光（实验）" },
  { id: "zoom_blur", label: "zoom_blur", desc: "镜头推进（实验）" },
  { id: "flip", label: "flip", desc: "翻转（实验）" },
  { id: "glitch", label: "glitch", desc: "故障（实验）" },
];

const VISUAL_STYLE_DIRECTIONS = [
  {
    id: "light_editorial",
    name: "light_editorial",
    label: "浅色科技媒体",
    tone: "浅色科技感，清新活泼",
    suitable: "轻量资讯、工具推荐、创业公司动态",
    motion: "中低动效，强调留白和文字可读性",
    sweepReady: "待探索",
  },
  {
    id: "pastel_glass",
    name: "pastel_glass",
    label: "淡色玻璃拟态",
    tone: "粉蓝淡紫 + 毛玻璃质感",
    suitable: "女性向内容、生活方式、AI 产品功能介绍",
    motion: "柔和过渡，轻微模糊动画",
    sweepReady: "待探索",
  },
  {
    id: "warm_paper",
    name: "warm_paper",
    label: "米白纸张报告",
    tone: "米白纸张纹理 + 暖灰文字",
    suitable: "企业咨询报告、行业研究报告、正式新闻",
    motion: "克制动效，静态为主",
    sweepReady: "待探索",
  },
  {
    id: "apple_keynote",
    name: "apple_keynote",
    label: "产品发布会",
    tone: "深色背景 + 大字标题 + 强调色点缀",
    suitable: "产品发布、功能演示、科技公司公告",
    motion: "慢速优雅过渡，镜头感强",
    sweepReady: "待探索",
  },
  {
    id: "calm_enterprise",
    name: "calm_enterprise",
    label: "企业咨询报告",
    tone: "深蓝灰 + 白色文字，信息密度高",
    suitable: "企业培训、咨询报告、方案展示",
    motion: "结构化卡片，强调信息层次",
    sweepReady: "待探索",
  },
  {
    id: "bold_magazine",
    name: "bold_magazine",
    label: "杂志爆点风",
    tone: "高对比黑白 + 红色强调，大字号",
    suitable: "突发新闻、观点短评、爆点资讯",
    motion: "快速切换，冲击感强",
    sweepReady: "待探索",
  },
];

const CANDIDATE_PRESETS = [
  {
    styleId: "remotion_report_stable",
    styleName: "稳重报告型",
    family: "data_news",
    background: "tech_grid_dark",
    transition: "slide_fade",
    status: "实验候选",
    note: "报告型长内容，阅读优先",
  },
  {
    styleId: "remotion_dashboard_glass_wipe",
    styleName: "玻璃看板快报",
    family: "dashboard_brief",
    background: "glass_dashboard",
    transition: "wipe",
    status: "实验候选",
    note: "Benchmark / 指标对比",
  },
  {
    styleId: "remotion_deep_space_stack",
    styleName: "深空卡片栈",
    family: "card_stack",
    background: "deep_space",
    transition: "push",
    status: "实验候选",
    note: "多信息点 / 资讯合集",
  },
  {
    styleId: "remotion_neon_glitch",
    styleName: "霓虹故障高能",
    family: "data_news",
    background: "neon_circuit",
    transition: "glitch",
    status: "实验候选",
    note: "强风格短视频 / 科技爆点",
  },
  {
    styleId: "remotion_caption_aurora_zoom",
    styleName: "极光大字叙事",
    family: "caption_story",
    background: "aurora_blue",
    transition: "zoom_blur",
    status: "实验候选",
    note: "观点摘要 / 口播解释",
  },
];

const ACCEPTANCE_SUMMARY = [
  { label: "工程能力", status: "部分通过", detail: "接口可用，测试通过" },
  { label: "background-matrix", status: "实测通过", detail: "HTTP 200, 3/3 clips" },
  { label: "transition-matrix", status: "实测通过", detail: "HTTP 200, 3/3 clips" },
  { label: "9-clip 限制", status: "已实施", detail: "超限返回 400" },
  { label: "invalid input", status: "已实施", detail: "返回 400 + 允许值" },
  { label: "pytest", status: "38 passed", detail: "全量测试通过" },
  { label: "前端构建", status: "通过", detail: "npm run build 成功" },
  { label: "视觉效果", status: "待人工验收", detail: "尚未完整播放所有新样式" },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function resolveUrl(u: string): string {
  return u && u.startsWith("/runtime/")
    ? `${API_BASE.replace(/\/video-lab$/, "")}${u}`
    : u || "";
}

// ─── Tab Components ────────────────────────────────────────────────────────────

function TabParadigm() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div
        style={{
          background: "linear-gradient(135deg, #7c3aed 0%, #2563eb 100%)",
          borderRadius: 16,
          padding: "1.5rem",
          color: "white",
        }}
      >
        <h2 style={{ fontSize: "1.15rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          表现范式
        </h2>
        <p style={{ fontSize: "0.85rem", opacity: 0.9, lineHeight: 1.6, marginBottom: "1rem" }}>
          表现范式用于比较 Remotion 的结构类型：Data News / Card Stack / Timeline / Dashboard / Caption Story。
          不同的版式结构带来完全不同的观看体验。
        </p>
        <div
          style={{
            background: "rgba(255,255,255,0.15)",
            borderRadius: 8,
            padding: "0.75rem 1rem",
            fontSize: "0.8rem",
            lineHeight: 1.6,
          }}
        >
          <strong>注意：</strong>表现范式不等于最终视觉风格。同一范式可以搭配不同的背景、转场、色彩、字体组合。
        </div>
      </div>

      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: 16,
          padding: "1.25rem",
        }}
      >
        <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          当前 5 种表现范式
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem" }}>
          {[
            { id: "data_news", name: "Data News", icon: "📊", color: "#7c3aed", desc: "数字驱动 / 指标变化" },
            { id: "card_stack", name: "Card Stack", icon: "🗂️", color: "#2563eb", desc: "卡片堆叠 / 信息流" },
            { id: "timeline_news", name: "Timeline", icon: "📅", color: "#0891b2", desc: "事件演进 / 时间线" },
            { id: "dashboard_brief", name: "Dashboard", icon: "🖥️", color: "#f59e0b", desc: "指标看板 / 排行" },
            { id: "caption_story", name: "Caption Story", icon: "💬", color: "#ec4899", desc: "大字旁白 / 叙事" },
          ].map((f) => (
            <div
              key={f.id}
              style={{
                border: `1px solid ${f.color}30`,
                borderRadius: 10,
                padding: "0.85rem",
                background: `${f.color}08`,
              }}
            >
              <div style={{ fontSize: "1.3rem", marginBottom: "0.35rem" }}>{f.icon}</div>
              <div style={{ fontSize: "0.85rem", fontWeight: 700, color: f.color }}>{f.name}</div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "0.2rem" }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <Link
        to="/video-lab/remotion-style-family"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          background: "#7c3aed",
          color: "white",
          textDecoration: "none",
          borderRadius: 10,
          padding: "0.75rem 1.25rem",
          fontSize: "0.9rem",
          fontWeight: 700,
          alignSelf: "flex-start",
        }}
      >
        前往表现范式研究台 →
      </Link>
    </div>
  );
}

function TabBackground() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BackgroundMatrixResponse | null>(null);
  const [error, setError] = useState("");

  const runMatrix = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const resp = await fetch(`${API_BASE}/style-family/background-matrix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: "OpenAI 发布新一代多模态模型，重点提升语音、图像和视频理解能力。",
          params: { clipSeconds: 2, keyPointCount: 2 },
          matrix: {
            families: ["timeline_news"],
            backgroundPresets: ["tech_grid_dark", "warm_cinematic", "neon_circuit"],
          },
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

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: 16,
          padding: "1.25rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem", color: "#1e293b" }}>
          背景矩阵
        </h2>
        <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "1rem", lineHeight: 1.6 }}>
          同一内容 × 多个背景 preset，观察背景能否给同一版式带来不同的视觉氛围。
          Lab-only，不写 Style Sweep job 或 Style Gallery sample。
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "0.75rem",
            marginBottom: "1.25rem",
          }}
        >
          {BACKGROUNDS.map((bg) => (
            <div
              key={bg.id}
              style={{
                border: "1px solid #e2e8f0",
                borderRadius: 10,
                padding: "0.75rem",
                background: "#f8fafc",
              }}
            >
              <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.2rem" }}>
                {bg.label}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#64748b" }}>{bg.desc}</div>
            </div>
          ))}
        </div>

        <button
          onClick={runMatrix}
          disabled={loading}
          style={{
            background: loading ? "#94a3b8" : "#0891b2",
            color: "white",
            border: "none",
            borderRadius: 8,
            padding: "0.6rem 1.25rem",
            fontSize: "0.9rem",
            fontWeight: 600,
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "渲染中..." : "运行最小背景矩阵（1 family × 3 backgrounds）"}
        </button>

        {error && (
          <div style={{ color: "#ef4444", fontSize: "0.82rem", marginTop: "0.75rem", padding: "0.75rem", background: "#fef2f2", borderRadius: 8 }}>
            错误：{error}
          </div>
        )}
      </div>

      {result && (
        <div
          style={{
            background: "white",
            border: "1px solid #e2e8f0",
            borderRadius: 16,
            padding: "1.25rem",
          }}
        >
          <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "1rem" }}>
            成功 {result.items.filter((i) => i.success).length}/{result.items.length} · {result.totalElapsedMs}ms
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
            {result.items.map((item) => (
              <div
                key={`${item.family}-${item.backgroundPreset}`}
                style={{
                  border: "1px solid #e2e8f0",
                  borderRadius: 10,
                  overflow: "hidden",
                }}
              >
                <div style={{ padding: "0.5rem 0.75rem", background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#1e293b" }}>{item.backgroundPreset}</div>
                  <div style={{ fontSize: "0.7rem", color: "#64748b" }}>{item.family}</div>
                </div>
                <div style={{ background: "#0f172a", padding: "0.5rem" }}>
                  {item.success && item.videoUrl ? (
                    <video
                      controls
                      src={resolveUrl(item.videoUrl)}
                      style={{ width: "100%", height: 160, objectFit: "contain", borderRadius: 6 }}
                    />
                  ) : (
                    <div style={{ height: 160, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.72rem", color: "#ef4444" }}>
                      {item.message || "失败"}
                    </div>
                  )}
                </div>
                <div style={{ padding: "0.4rem 0.75rem", borderTop: "1px solid #f1f5f9", fontSize: "0.7rem", color: "#94a3b8" }}>
                  {item.success ? "✓ 成功" : "✗ 失败"} · {item.elapsedMs}ms
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TabTransition() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TransitionMatrixResponse | null>(null);
  const [error, setError] = useState("");

  const runMatrix = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const resp = await fetch(`${API_BASE}/style-family/transition-matrix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: "OpenAI 发布新一代多模态模型，重点提升语音、图像和视频理解能力。",
          params: { clipSeconds: 2, keyPointCount: 2, backgroundPreset: "tech_grid_dark" },
          matrix: {
            families: ["data_news"],
            transitionStyles: ["push", "wipe", "glitch"],
          },
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

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: 16,
          padding: "1.25rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem", color: "#1e293b" }}>
          转场矩阵
        </h2>
        <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "1rem", lineHeight: 1.6 }}>
          同一内容 × 多个转场风格，观察转场是否带来不同的节奏感知和情绪。
          Lab-only，不写 Style Sweep job 或 Style Gallery sample。
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem", marginBottom: "1.25rem" }}>
          {TRANSITIONS.map((t) => (
            <div
              key={t.id}
              style={{
                border: "1px solid #e2e8f0",
                borderRadius: 10,
                padding: "0.75rem",
                background: "#f8fafc",
              }}
            >
              <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.2rem" }}>{t.label}</div>
              <div style={{ fontSize: "0.72rem", color: "#64748b" }}>{t.desc}</div>
            </div>
          ))}
        </div>

        <button
          onClick={runMatrix}
          disabled={loading}
          style={{
            background: loading ? "#94a3b8" : "#7c3aed",
            color: "white",
            border: "none",
            borderRadius: 8,
            padding: "0.6rem 1.25rem",
            fontSize: "0.9rem",
            fontWeight: 600,
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "渲染中..." : "运行最小转场矩阵（1 family × 3 transitions）"}
        </button>

        {error && (
          <div style={{ color: "#ef4444", fontSize: "0.82rem", marginTop: "0.75rem", padding: "0.75rem", background: "#fef2f2", borderRadius: 8 }}>
            错误：{error}
          </div>
        )}
      </div>

      {result && (
        <div
          style={{
            background: "white",
            border: "1px solid #e2e8f0",
            borderRadius: 16,
            padding: "1.25rem",
          }}
        >
          <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "1rem" }}>
            成功 {result.items.filter((i) => i.success).length}/{result.items.length} · {result.totalElapsedMs}ms
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
            {result.items.map((item) => (
              <div
                key={`${item.family}-${item.transitionStyle}`}
                style={{
                  border: "1px solid #e2e8f0",
                  borderRadius: 10,
                  overflow: "hidden",
                }}
              >
                <div style={{ padding: "0.5rem 0.75rem", background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#1e293b" }}>{item.transitionStyle}</div>
                  <div style={{ fontSize: "0.7rem", color: "#64748b" }}>{item.family}</div>
                </div>
                <div style={{ background: "#0f172a", padding: "0.5rem" }}>
                  {item.success && item.videoUrl ? (
                    <video
                      controls
                      src={resolveUrl(item.videoUrl)}
                      style={{ width: "100%", height: 160, objectFit: "contain", borderRadius: 6 }}
                    />
                  ) : (
                    <div style={{ height: 160, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.72rem", color: "#ef4444" }}>
                      {item.message || "失败"}
                    </div>
                  )}
                </div>
                <div style={{ padding: "0.4rem 0.75rem", borderTop: "1px solid #f1f5f9", fontSize: "0.7rem", color: "#94a3b8" }}>
                  {item.success ? "✓ 成功" : "✗ 失败"} · {item.elapsedMs}ms
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TabVisualStyle() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div
        style={{
          background: "#fffbeb",
          border: "1px solid #fde68a",
          borderRadius: 12,
          padding: "1rem 1.25rem",
          fontSize: "0.85rem",
          color: "#92400e",
          lineHeight: 1.6,
        }}
      >
        <strong>视觉风格 ≠ 背景。</strong>视觉风格 = 色彩 + 背景 + 字体 + 卡片 + 布局 + 动效 + 信息密度 + 情绪。
        以下 6 个方向是建议探索方向，不代表已有实现。
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
        {VISUAL_STYLE_DIRECTIONS.map((dir) => (
          <div
            key={dir.id}
            style={{
              background: "white",
              border: "1px solid #e2e8f0",
              borderRadius: 12,
              padding: "1rem",
            }}
          >
            <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.4rem" }}>
              {dir.label}
            </div>
            <div style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#94a3b8", marginBottom: "0.6rem" }}>
              {dir.name}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.78rem" }}>
              <div>
                <span style={{ fontWeight: 600, color: "#64748b" }}>色彩基调：</span>
                <span style={{ color: "#475569" }}>{dir.tone}</span>
              </div>
              <div>
                <span style={{ fontWeight: 600, color: "#64748b" }}>适合内容：</span>
                <span style={{ color: "#475569" }}>{dir.suitable}</span>
              </div>
              <div>
                <span style={{ fontWeight: 600, color: "#64748b" }}>动效倾向：</span>
                <span style={{ color: "#475569" }}>{dir.motion}</span>
              </div>
              <div style={{ marginTop: "0.3rem" }}>
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 700,
                    color: "#b45309",
                    background: "#fef3c7",
                    border: "1px solid #fde68a",
                    borderRadius: 999,
                    padding: "0.1rem 0.45rem",
                  }}
                >
                  {dir.sweepReady}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TabCandidate() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div
        style={{
          background: "#fef2f2",
          border: "1px solid #fecaca",
          borderRadius: 12,
          padding: "1rem 1.25rem",
          fontSize: "0.82rem",
          color: "#991b1b",
          lineHeight: 1.6,
        }}
      >
        以下为 <strong>实验候选模板</strong>，尚未完成完整 Style Sweep 人工验收。
        请勿在文档或产品中称为"正式稳定模板"。
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
        {CANDIDATE_PRESETS.map((preset) => (
          <div
            key={preset.styleId}
            style={{
              background: "white",
              border: "1px solid #e2e8f0",
              borderRadius: 12,
              padding: "1rem 1.25rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
              <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#1e293b" }}>{preset.styleName}</div>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  color: "#b45309",
                  background: "#fef3c7",
                  border: "1px solid #fde68a",
                  borderRadius: 999,
                  padding: "0.1rem 0.5rem",
                }}
              >
                {preset.status}
              </span>
            </div>
            <div style={{ fontSize: "0.72rem", fontFamily: "monospace", color: "#64748b", marginBottom: "0.6rem" }}>
              {preset.styleId}
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", fontSize: "0.78rem" }}>
              {[
                `family: ${preset.family}`,
                `background: ${preset.background}`,
                `transition: ${preset.transition}`,
              ].map((tag) => (
                <span
                  key={tag}
                  style={{
                    background: "#f8fafc",
                    color: "#475569",
                    border: "1px solid #e2e8f0",
                    borderRadius: 6,
                    padding: "0.15rem 0.45rem",
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
            <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "0.5rem" }}>
              {preset.note}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TabAcceptance() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: 16,
          padding: "1.25rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem", color: "#1e293b" }}>
          V1.2.3 Remotion 特性探索验收记录
        </h2>
        <p style={{ fontSize: "0.78rem", color: "#64748b", marginBottom: "1rem" }}>
          基于 <code style={{ background: "#f1f5f9", padding: "1px 4px", borderRadius: 4 }}>028a85c</code> Codex 优化remotion模块 ·
          验收日期：2026-06-17
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {ACCEPTANCE_SUMMARY.map((item) => (
            <div
              key={item.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                fontSize: "0.85rem",
              }}
            >
              <span style={{ width: 130, fontWeight: 600, color: "#475569", flexShrink: 0 }}>{item.label}</span>
              <span
                style={{
                  color: item.status.includes("通过") || item.status.includes("已实施") || item.status === "通过"
                    ? "#15803d"
                    : item.status === "待人工验收"
                    ? "#b45309"
                    : "#475569",
                  fontWeight: 700,
                }}
              >
                {item.status}
              </span>
              <span style={{ color: "#94a3b8", fontSize: "0.78rem" }}>{item.detail}</span>
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: 16,
          padding: "1.25rem",
        }}
      >
        <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "0.75rem", color: "#1e293b" }}>
          结论：部分通过
        </h3>
        <p style={{ fontSize: "0.82rem", color: "#475569", lineHeight: 1.6 }}>
          工程能力可用，视觉效果仍需人工验收。所有新候选背景（neon_circuit、deep_space）和
          转场（push、wipe、zoom_blur、flip、glitch）的实际视觉效果尚未完整播放确认。
        </p>
      </div>

      <div
        style={{
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: 16,
          padding: "1.25rem",
        }}
      >
        <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "0.75rem", color: "#1e293b" }}>
          风险与遗留问题
        </h3>
        <ul style={{ fontSize: "0.82rem", color: "#475569", lineHeight: 1.8, margin: 0, paddingLeft: "1.2rem" }}>
          <li>视觉效果尚未人工验收，新候选不应视为正式生产稳定模板</li>
          <li>Codex 可能因限额中断，还有未探索完的修改意图</li>
          <li>候选 style 尚未进入 Style Sweep 流程</li>
        </ul>
      </div>

      <div style={{ fontSize: "0.78rem", color: "#94a3b8" }}>
        完整文档：<code style={{ background: "#f1f5f9", padding: "1px 4px", borderRadius: 4 }}>docs/V1_2_3_REMOTION_FEATURE_EXPLORATION_ACCEPTANCE.md</code>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function RemotionLabPage() {
  const [activeTab, setActiveTab] = useState<string>("paradigm");

  const renderTab = () => {
    switch (activeTab) {
      case "paradigm":
        return <TabParadigm />;
      case "background":
        return <TabBackground />;
      case "transition":
        return <TabTransition />;
      case "visual-style":
        return <TabVisualStyle />;
      case "candidate":
        return <TabCandidate />;
      case "acceptance":
        return <TabAcceptance />;
      default:
        return null;
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f766e 100%)",
          color: "white",
          borderRadius: 16,
          padding: "1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "1.5rem" }}>🧪</span>
          <h1 style={{ fontSize: "1.35rem", fontWeight: 700, margin: 0 }}>
            Remotion 能力探索中心
          </h1>
        </div>
        <p style={{ fontSize: "0.88rem", opacity: 0.88, lineHeight: 1.6, margin: 0 }}>
          Lab-only，用于探索 Remotion 的表现范式、背景、转场、视觉风格和候选模板。
          不直接等同于正式 Style Sweep 生产模板。
        </p>
      </div>

      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.35rem",
          marginBottom: "1.5rem",
          borderBottom: "1px solid #e2e8f0",
          paddingBottom: "0.75rem",
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: activeTab === tab.id ? "#7c3aed" : "transparent",
              color: activeTab === tab.id ? "white" : "#64748b",
              border: "none",
              borderRadius: 8,
              padding: "0.45rem 0.9rem",
              fontSize: "0.85rem",
              fontWeight: activeTab === tab.id ? 700 : 500,
              cursor: "pointer",
              transition: "background 0.15s, color 0.15s",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>{renderTab()}</div>

      {/* Footer nav */}
      <div
        style={{
          marginTop: "2rem",
          paddingTop: "1.25rem",
          borderTop: "1px solid #e2e8f0",
          display: "flex",
          gap: "1rem",
          flexWrap: "wrap",
          fontSize: "0.82rem",
        }}
      >
        <Link to="/video-lab/remotion-style-family" style={{ color: "#7c3aed", textDecoration: "none" }}>
          ← 表现范式研究台
        </Link>
        <Link to="/video-lab" style={{ color: "#64748b", textDecoration: "none" }}>
          ← Video Lab 首页
        </Link>
      </div>
    </div>
  );
}
