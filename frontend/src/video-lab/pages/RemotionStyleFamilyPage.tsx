// Remotion Style Family Page - V0.6.5.2 / V0.8.8
// V0.8.8: 升级为「Remotion 表现范式研究台」 —
//   - 扩展 StyleFamily：referenceExamples / implementationPattern / requiredComponents / styleSweepMapping / nextExperiment
//   - 新增「参考样例 → 可落地范式」「当前实现覆盖度」「下一步最小实验推荐」三个区块
//   - 参考来源（人工整理）：
//       Remotion 官方 templates 方向：Audiogram / Music Visualization / Prompt to Video /
//         3D / Code Hike / Stargazer / TikTok word-by-word captions / Overlay
//       Remotion Showcase / Prompt Showcase 方向：News article headline highlight /
//         Product Demo / Cinematic Tech Intro / Rocket Launches Timeline /
//         Three.js Ranking / Bar + Line Chart / Travel Route Map / Transparent CTA overlay

import { Link } from "react-router-dom";
import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

interface CompareResult {
  experimentId: string;
  success: boolean;
  videoUrl: string;
  clipSeconds: number;
  elapsedMs: number;
  message: string;
  warnings: string[];
}

interface CompareResponse {
  dataNews: CompareResult;
  cardStack: CompareResult;
  timelineNews?: CompareResult;
  dashboardBrief?: CompareResult;
  captionStory?: CompareResult;
  totalElapsedMs: number;
}

// V1.2.3: Background Variant Matrix
interface MatrixItem {
  family: string;
  backgroundPreset: string;
  success: boolean;
  videoUrl: string;
  experimentId: string;
  clipSeconds: number;
  elapsedMs: number;
  message: string;
  warnings: string[];
}

interface MatrixResponse {
  items: MatrixItem[];
  totalElapsedMs: number;
}

interface TransitionMatrixItem {
  family: string;
  transitionStyle: string;
  success: boolean;
  videoUrl: string;
  experimentId: string;
  clipSeconds: number;
  elapsedMs: number;
  message: string;
  warnings: string[];
}

interface TransitionMatrixResponse {
  items: TransitionMatrixItem[];
  totalElapsedMs: number;
}

// V1.2.4: Visual Style Preset Matrix
interface VisualStyleMatrixItem {
  family: string;
  visualStylePreset: string;
  success: boolean;
  videoUrl: string;
  experimentId: string;
  clipSeconds: number;
  elapsedMs: number;
  message: string;
  warnings: string[];
}

interface VisualStyleMatrixResponse {
  items: VisualStyleMatrixItem[];
  totalElapsedMs: number;
}

// V1.2.4: Visual Technique Matrix
interface VisualTechniqueMatrixItem {
  family: string;
  visualTechnique: string;
  success: boolean;
  videoUrl: string;
  experimentId: string;
  clipSeconds: number;
  elapsedMs: number;
  message: string;
  warnings: string[];
}

interface VisualTechniqueMatrixResponse {
  items: VisualTechniqueMatrixItem[];
  totalElapsedMs: number;
}

// ─── Style Family Definition ───────────────────────────────────────────────────

interface StyleFamily {
  id: string;
  name: string;
  tagline: string;
  description: string;
  suitable: string[];
  visualFeatures: string[];
  currentStatus: string;
  priority: "P0" | "P1" | "P2";
  priorityReason: string;
  accentColor: string;
  icon: string;

  // V0.8.8: 参考样例 / 实现映射（来自 Remotion 官方模板 / Showcase / Prompt Showcase 抽象）
  referenceExamples?: string[];
  implementationPattern?: string[];
  requiredComponents?: string[];
  styleSweepMapping?: string[];
  nextExperiment?: string;
}

const FAMILIES: StyleFamily[] = [
  {
    id: "data_news",
    name: "Data News",
    tagline: "数据新闻 / 指标变化 / 百分比高亮",
    description:
      "以数字驱动为核心，适合模型性能提升、融资数据、用户增长、Benchmark 通过率等需要突出数据变化的场景。",
    suitable: [
      "模型性能提升",
      "Benchmark 通过率",
      "融资/估值数据",
      "用户增长指标",
      "榜单变化",
    ],
    visualFeatures: [
      "数字滚动动画",
      "数据条生长",
      "百分比高亮",
      "趋势箭头",
      "指标卡片",
    ],
    currentStatus: "已有基础 — AiNewsVideo 当前形态最接近此方向",
    priority: "P0",
    priorityReason: "与当前 AI 新闻场景最贴近，已验证可行",
    accentColor: "#7c3aed",
    icon: "📊",
    referenceExamples: [
      "News article headline highlight",
      "Bar + Line Chart",
      "Ranking / Leaderboard",
    ],
    implementationPattern: [
      "数据驱动卡片",
      "指标动画",
      "标题高亮",
      "趋势箭头",
    ],
    requiredComponents: ["MetricCard", "AnimatedCounter", "TrendArrow", "HeadlineHighlight"],
    styleSweepMapping: ["remotion_metric_motion", "remotion_minimal_clean", "remotion_chart_story", "remotion_ranking_strip"],
    nextExperiment:
      "把 metricAnimation 从 countup_bar 扩展到 chart_story / ranking_strip",
  },
  {
    id: "card_stack",
    name: "Card Stack",
    tagline: "卡片堆叠 / 短资讯合集 / 短视频信息流",
    description:
      "以卡片滑动为核心，适合 AI 工具推荐、三条新闻合集、多产品快速介绍等需要强短视频感的场景。",
    suitable: [
      "AI 工具推荐",
      "今日 AI 三件事",
      "多产品快速介绍",
      "模型能力清单",
      "短资讯合集",
    ],
    visualFeatures: [
      "卡片滑入出场",
      "当前卡片突出",
      "上一张退到背景层",
      "下一张卡片预览",
      "短视频节奏",
    ],
    currentStatus: "V0.6.5.2 已支持 UI 预览对比 — prev/next 图层已强化可见性，蓝/青边框+PREV/NEXT角标使堆叠效果可辨识",
    priority: "P1",
    priorityReason: "短视频感最强，适合 AI 新闻信息流方向",
    accentColor: "#2563eb",
    icon: "🗂️",
    referenceExamples: [
      "Product Demo",
      "TikTok-style card carousel",
      "Social post carousel",
    ],
    implementationPattern: [
      "多卡片队列",
      "prev / current / next 三层",
      "卡片滑入滑出",
      "短视频信息流节奏",
    ],
    requiredComponents: ["CardStackLayer", "SwipeTransition", "PrevNextIndicator"],
    styleSweepMapping: ["remotion_card_stack"],
    nextExperiment:
      "增加 card depth、swipe transition、当前卡片强调、结尾总览卡",
  },
  {
    id: "timeline",
    name: "Timeline",
    tagline: "事件演进 / 时间线 / 因果顺序",
    description:
      "以时间顺序为核心，适合政策演进、产品发布步骤、论文方法流程、技术路线变化等需要清晰因果顺序的场景。",
    suitable: [
      "政策演进",
      "产品发布步骤",
      "论文方法流程",
      "技术路线变化",
      "公司合作进展",
    ],
    visualFeatures: [
      "竖向时间线",
      "节点依次出现",
      "当前节点高亮",
      "历史节点淡化",
      "因果箭头连接",
    ],
    currentStatus: "V0.8.9 已有最小实现 — TimelineNewsLayout 已接入 AiNewsVideo 的 timeline_news 分支",
    priority: "P1",
    priorityReason: "适合解释复杂事件，与 Data News 正交",
    accentColor: "#0891b2",
    icon: "📅",
    referenceExamples: [
      "Rocket Launches Timeline",
      "Travel Route Map",
      "产品发布路线图",
    ],
    implementationPattern: [
      "时间节点",
      "事件进度线",
      "当前节点高亮",
      "历史节点淡化",
    ],
    requiredComponents: ["TimelineNode", "ProgressLine", "EventCard"],
    styleSweepMapping: ["remotion_timeline_news", "remotion_timeline_route_map"],
    nextExperiment:
      "增强节点节奏、事件日期/阶段标签、结尾路线总览",
  },
  {
    id: "dashboard",
    name: "Dashboard",
    tagline: "多指标看板 / 排行榜 / 模型对比矩阵",
    description:
      "以多面板布局为核心，适合模型排行榜、Benchmark 矩阵、多公司指标对比、产品能力评分等高信息密度场景。",
    suitable: [
      "模型排行榜",
      "Benchmark 矩阵",
      "多公司指标对比",
      "产品能力评分",
      "投资组合概览",
    ],
    visualFeatures: [
      "多数据面板",
      "排行榜",
      "进度条",
      "矩阵布局",
      "小型指标组件",
    ],
    currentStatus: "已有最小可生成预设 — remotion_dashboard_brief，先覆盖 3 指标卡 + 活动信号 + 排行列表",
    priority: "P2",
    priorityReason: "信息密度高但复杂度也高，容易过度设计",
    accentColor: "#f59e0b",
    icon: "🖥️",
    referenceExamples: [
      "Three.js Ranking",
      "Bar + Line Chart",
      "Benchmark dashboard",
      "Leaderboard",
    ],
    implementationPattern: [
      "多指标面板",
      "排行榜",
      "矩阵布局",
      "进度条 / 小图表",
    ],
    requiredComponents: ["DashboardPanel", "RankingList", "MiniBar", "MiniSpark"],
    styleSweepMapping: ["remotion_dashboard_brief", "remotion_chart_story", "remotion_ranking_strip"],
    nextExperiment:
      "新增 remotion_dashboard_brief，先做 3 指标面板 + 1 个排行榜模块",
  },
  {
    id: "subtitle_story",
    name: "Subtitle Story",
    tagline: "旁白驱动 / 大字幕 / 情绪叙事",
    description:
      "以旁白节奏为核心，适合观点短片、深夜独白、情绪 MV、口播内容等情绪驱动的场景。",
    suitable: [
      "观点短片",
      "深夜独白",
      "情绪 MV",
      "一句话长成短片",
      "口播内容",
    ],
    visualFeatures: [
      "大字幕占主导",
      "弱化画面",
      "背景轻动效",
      "节奏跟随旁白",
      "情绪色彩渐变",
    ],
    currentStatus: "已有最小可生成预设 — remotion_caption_story，先覆盖大字标题 + 旁白节奏 + 进度条叙事",
    priority: "P2",
    priorityReason: "更偏向情绪内容，与当前 AI 新闻定位差异较大",
    accentColor: "#ec4899",
    icon: "💬",
    referenceExamples: [
      "TikTok word-by-word captions",
      "Cinematic Tech Intro",
      "Transparent CTA overlay",
    ],
    implementationPattern: [
      "大字幕",
      "逐词高亮",
      "背景弱动效",
      "旁白节奏驱动",
    ],
    requiredComponents: ["WordCaption", "SentenceCard", "AmbientBackground"],
    styleSweepMapping: ["remotion_caption_story", "remotion_caption_intro", "remotion_cta_overlay"],
    nextExperiment:
      "新增 remotion_caption_story，用大字幕 + word highlight 做一版 AI 新闻口播",
  },
];

// ─── Comparison Matrix ────────────────────────────────────────────────────────

interface ComparisonRow {
  dimension: string;
  dataNews: string;
  cardStack: string;
  timeline: string;
  dashboard: string;
  subtitleStory: string;
}

const COMPARISON_MATRIX: ComparisonRow[] = [
  {
    dimension: "信息密度",
    dataNews: "★★★★☆",
    cardStack: "★★★☆☆",
    timeline: "★★★☆☆",
    dashboard: "★★★★★",
    subtitleStory: "★★☆☆☆",
  },
  {
    dimension: "动效强度",
    dataNews: "★★★★☆",
    cardStack: "★★★★☆",
    timeline: "★★★☆☆",
    dashboard: "★★★☆☆",
    subtitleStory: "★★☆☆☆",
  },
  {
    dimension: "实现难度",
    dataNews: "★☆☆☆☆",
    cardStack: "★★☆☆☆",
    timeline: "★★★☆☆",
    dashboard: "★★★★☆",
    subtitleStory: "★★☆☆☆",
  },
  {
    dimension: "适合 AI 新闻",
    dataNews: "★★★★★",
    cardStack: "★★★★☆",
    timeline: "★★★★☆",
    dashboard: "★★★☆☆",
    subtitleStory: "★★☆☆☆",
  },
  {
    dimension: "适合情绪内容",
    dataNews: "★★☆☆☆",
    cardStack: "★★☆☆☆",
    timeline: "★★☆☆☆",
    dashboard: "★☆☆☆☆",
    subtitleStory: "★★★★★",
  },
  {
    dimension: "适合批量生成",
    dataNews: "★★★★☆",
    cardStack: "★★★★☆",
    timeline: "★★★☆☆",
    dashboard: "★★☆☆☆",
    subtitleStory: "★★★★☆",
  },
  {
    dimension: "商业展示感",
    dataNews: "★★★★☆",
    cardStack: "★★★☆☆",
    timeline: "★★★☆☆",
    dashboard: "★★★★★",
    subtitleStory: "★★★☆☆",
  },
];

// ─── Priority Roadmap ─────────────────────────────────────────────────────────

const PRIORITY_ROADMAP = [
  {
    step: 1,
    families: ["data_news"],
    reason: "与当前 AI 新闻场景最贴近；已有基础；风险最低",
  },
  {
    step: 2,
    families: ["card_stack"],
    reason: "短视频感最强；'今日 AI 三件事'场景明确；可快速验证",
  },
  {
    step: 3,
    families: ["timeline"],
    reason: "适合解释复杂事件；与 Data News 正交；拓展内容边界",
  },
  {
    step: 4,
    families: ["dashboard", "subtitle_story"],
    reason: "Dashboard 复杂度高；Subtitle Story 更适合情绪视频产品线",
  },
];

// ─── Min Sample ─────────────────────────────────────────────────────────────

const MIN_SAMPLE = {
  family: "Card Stack",
  reason:
    "1. 与当前 AiNewsVideo 差异明显（卡片 vs 数字）\n2. 短视频感更强\n3. 适合'今日 AI 三件事'\n4. 不需要复杂数据图表\n5. 可复用现有数据结构快速验证",
  status: "V0.6.4 已支持 UI 实际预览对比",
  experimentId: "clip_4f6e00b7",
  detail: "remotionFamily=card_stack 时，主卡后层叠加一张 prev 卡片（右下角露出），形成堆叠视觉效果。\n实际渲染验证：secondary card layer 确实出现在主卡右下角，与 Data News 有可见差异。",
};

// ─── Component ───────────────────────────────────────────────────────────────

const REMOTION_GALLERY_BASE =
  "/video-lab/style-gallery?tab=presets&route_id=template_programmatic_render";

const getFamilyGalleryUrl = (family: StyleFamily): string => {
  const styleId = family.styleSweepMapping?.[0];
  return styleId ? `${REMOTION_GALLERY_BASE}&style_id=${styleId}` : REMOTION_GALLERY_BASE;
};

function FamilyCard({ family }: { family: StyleFamily }) {
  const priorityColor = {
    P0: "#16a34a",
    P1: "#2563eb",
    P2: "#94a3b8",
  }[family.priority];

  return (
    <div
      style={{
        background: "white",
        border: `1px solid #e2e8f0`,
        borderRadius: "16px",
        overflow: "hidden",
        boxShadow: `0 2px 8px ${family.accentColor}15`,
      }}
    >
      {/* Header */}
      <div
        style={{
          background: `linear-gradient(135deg, ${family.accentColor}18 0%, ${family.accentColor}08 100%)`,
          borderBottom: `1px solid ${family.accentColor}30`,
          padding: "1.1rem 1.25rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem", marginBottom: "0.4rem" }}>
          <span style={{ fontSize: "1.5rem" }}>{family.icon}</span>
          <div>
            <div style={{ fontSize: "1rem", fontWeight: 700, color: "#1e293b" }}>
              {family.name}
            </div>
            <div style={{ fontSize: "0.78rem", color: "#64748b", fontStyle: "italic" }}>
              {family.tagline}
            </div>
          </div>
          <div
            style={{
              marginLeft: "auto",
              background: priorityColor,
              color: "white",
              borderRadius: "999px",
              padding: "0.15rem 0.55rem",
              fontSize: "0.75rem",
              fontWeight: 700,
            }}
          >
            {family.priority}
          </div>
        </div>
        <p style={{ fontSize: "0.85rem", color: "#475569", lineHeight: 1.5 }}>
          {family.description}
        </p>
      </div>

      {/* Body */}
      <div style={{ padding: "1.1rem 1.25rem" }}>
        {/* Suitable */}
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "0.3rem" }}>
            适合内容
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
            {family.suitable.map((s) => (
              <span
                key={s}
                style={{
                  background: `${family.accentColor}12`,
                  color: family.accentColor,
                  border: `1px solid ${family.accentColor}30`,
                  borderRadius: "6px",
                  padding: "0.1rem 0.45rem",
                  fontSize: "0.75rem",
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </div>

        {/* Visual Features */}
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "0.3rem" }}>
            视觉特征
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
            {family.visualFeatures.map((f) => (
              <span
                key={f}
                style={{
                  background: "#f8fafc",
                  color: "#475569",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                  padding: "0.1rem 0.45rem",
                  fontSize: "0.75rem",
                }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>

        {/* Status */}
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "0.3rem" }}>
            当前状态
          </div>
          <div style={{ fontSize: "0.82rem", color: "#475569" }}>{family.currentStatus}</div>
        </div>

        {/* Priority Reason */}
        <div
          style={{
            background: `${family.accentColor}08`,
            border: `1px solid ${family.accentColor}25`,
            borderRadius: "8px",
            padding: "0.55rem 0.75rem",
            fontSize: "0.78rem",
            color: "#475569",
          }}
        >
          <span style={{ fontWeight: 600, color: family.accentColor }}>{family.priority} 原因：</span>
          {family.priorityReason}
        </div>
        <div
          style={{
            marginTop: "0.85rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
            {family.styleSweepMapping?.length
              ? `Gallery preset: ${family.styleSweepMapping.join(", ")}`
              : "No dedicated preset yet"}
          </div>
          <Link
            to={getFamilyGalleryUrl(family)}
            style={{
              background: family.styleSweepMapping?.length ? family.accentColor : "#64748b",
              color: "white",
              textDecoration: "none",
              borderRadius: "8px",
              padding: "0.4rem 0.8rem",
              fontSize: "0.78rem",
              fontWeight: 700,
              whiteSpace: "nowrap",
            }}
          >
            {family.styleSweepMapping?.length ? "去生成该范式" : "查看 Remotion 预设"}
          </Link>
        </div>
      </div>
    </div>
  );
}

// ─── V0.8.8: 当前实现覆盖度面板 ───────────────────────────────────────────────

function CoveragePanel() {
  // V0.8.9: Timeline News 已加入已实现基础
  // 已实现基础：Data News / Card Stack / Timeline News
  // 部分实现：Data News 指标动画 / Card Stack 卡片堆叠 / Timeline News 竖向时间线
  // 未实现：Dashboard / Subtitle Story / Map Journey / Code Walkthrough / Audio Wave
  const implemented = [
    { name: "Data News", note: "AiNewsVideo 当前形态即 Data News 范式" },
    { name: "Card Stack", note: "V0.6.5.2 已支持 prev/next 三层卡片 UI 预览对比" },
    { name: "Timeline News", note: "V0.8.9 已在 AiNewsVideo 中实现 TimelineNewsLayout 最小模板（竖向时间线 + 节点高亮 + 进度线）" },
    { name: "Dashboard Brief", note: "V0.9.0 已接入 remotion_dashboard_brief：指标卡 + 活动信号 + 排行列表" },
    { name: "Caption Story", note: "V0.9.0 已接入 remotion_caption_story：大字标题 + 旁白节奏 + 进度条叙事" },
  ];
  const partial = [
    { name: "Data News 指标动画", note: "已有 countup_bar；chart_story / ranking_strip 待扩展" },
    { name: "Card Stack 卡片堆叠", note: "已有 prev/next 视觉；swipe transition / 当前卡片强调待增强" },
    { name: "Timeline News 竖向时间线", note: "已有节点高亮 + 进度线；事件日期 / 阶段标签 / 结尾路线总览待增强" },
  ];
  const missing = [
    { name: "Map Journey", note: "未纳入本轮主流程" },
    { name: "Code Walkthrough", note: "未纳入本轮主流程" },
    { name: "Audio Wave", note: "未纳入本轮主流程" },
  ];
  return (
    <div
      data-testid="remotion-coverage-panel"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
      }}
    >
      <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem", color: "#1e293b" }}>
        当前实现覆盖度
      </h2>
      <p style={{ fontSize: "0.78rem", color: "#94a3b8", marginBottom: "1rem" }}>
        下方三列明确区分"已实现基础 / 部分实现 / 未实现"，避免误以为本页列出的 family 都已可生成。
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "0.85rem",
        }}
      >
        <CoverageColumn
          title="已实现基础"
          color="#10b981"
          bg="#f0fdf4"
          border="#bbf7d0"
          items={implemented}
        />
        <CoverageColumn
          title="部分实现"
          color="#f59e0b"
          bg="#fffbeb"
          border="#fde68a"
          items={partial}
        />
        <CoverageColumn
          title="未实现"
          color="#94a3b8"
          bg="#f8fafc"
          border="#e2e8f0"
          items={missing}
        />
      </div>
    </div>
  );
}

function CoverageColumn({
  title,
  color,
  bg,
  border,
  items,
}: {
  title: string;
  color: string;
  bg: string;
  border: string;
  items: { name: string; note: string }[];
}) {
  return (
    <div style={{ background: bg, border: `1px solid ${border}`, borderRadius: 10, padding: "0.75rem 0.85rem" }}>
      <div style={{ fontSize: "0.82rem", fontWeight: 700, color, marginBottom: 6 }}>
        {title}（{items.length}）
      </div>
      <ul style={{ margin: 0, paddingLeft: "1rem", fontSize: "0.78rem", color: "#334155", lineHeight: 1.55 }}>
        {items.map((it) => (
          <li key={it.name} style={{ marginBottom: 4 }}>
            <b style={{ color: "#1e293b" }}>{it.name}</b> — {it.note}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── V0.8.8: 下一步最小实验推荐 ───────────────────────────────────────────────

function NextExperimentPanel() {
  return (
    <div
      data-testid="remotion-next-experiment-panel"
      style={{
        background: "linear-gradient(135deg, #0f766e 0%, #0ea5e9 100%)",
        borderRadius: "16px",
        padding: "1.25rem 1.5rem",
        color: "white",
        marginBottom: "2.5rem",
      }}
    >
      <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem" }}>
        下一步最小实验推荐
      </h2>
      <p style={{ fontSize: "0.78rem", opacity: 0.85, marginBottom: "0.85rem" }}>
        V0.8.9 已实现 <code style={{ background: "rgba(255,255,255,0.18)", padding: "1px 6px", borderRadius: 4 }}>remotion_timeline_news</code> 最小模板。
        下一步建议进入 Style Sweep 实测，观察下列几点：
      </p>
      <div
        style={{
          background: "rgba(255,255,255,0.15)",
          borderRadius: 10,
          padding: "0.85rem 1rem",
          fontSize: "0.85rem",
          lineHeight: 1.65,
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: "1.4rem" }}>🧪</span>
          <span style={{ fontSize: "1.05rem", fontWeight: 700 }}>实测观察清单</span>
        </div>
        <ol style={{ margin: 0, paddingLeft: "1.1rem", opacity: 0.95 }}>
          <li>时间线是否真的比 Data News 更适合事件演进类内容</li>
          <li>文字密度是否过高（所有 keyPoints 同时显示）</li>
          <li>当前节点和历史节点是否清楚</li>
          <li>与 Card Stack 的差异是否肉眼可见（叠层 vs 时间线）</li>
        </ol>
        <div style={{ marginTop: 8, fontSize: "0.78rem", opacity: 0.85 }}>
          下一范式候选：<b>Dashboard</b> / <b>Subtitle Story</b> — 等待 Timeline News 实测结论再决定优先级。
        </div>
      </div>
    </div>
  );
}

// ─── V0.8.8: 参考样例 → 可落地范式 映射 ────────────────────────────────────────

const REFERENCE_MAPPING: {
  referenceExample: string;
  familyId: string;
  content: string;
  status: "已有基础" | "部分可做" | "待实现";
  next: string;
}[] = [
  {
    referenceExample: "News article headline highlight",
    familyId: "data_news",
    content: "AI 新闻 / 指标变化",
    status: "已有基础",
    next: "强化标题高亮",
  },
  {
    referenceExample: "Bar + Line Chart",
    familyId: "data_news",
    content: "Benchmark / 排名",
    status: "已有基础",
    next: "remotion_chart_story",
  },
  {
    referenceExample: "Ranking / Leaderboard",
    familyId: "data_news",
    content: "榜单 / Top 10",
    status: "已有基础",
    next: "remotion_ranking_strip",
  },
  {
    referenceExample: "Product Demo",
    familyId: "card_stack",
    content: "产品介绍 / 工具推荐",
    status: "已有基础",
    next: "强化多卡轮播",
  },
  {
    referenceExample: "TikTok-style card carousel",
    familyId: "card_stack",
    content: "AI 工具推荐 / 短资讯合集",
    status: "已有基础",
    next: "强化多卡轮播",
  },
  {
    referenceExample: "Rocket Launches Timeline",
    familyId: "timeline",
    content: "事件演进 / 历史里程碑",
    status: "已有基础",
    next: "remotion_timeline_news",
  },
  {
    referenceExample: "Travel Route Map",
    familyId: "timeline",
    content: "路线 / 路径展示",
    status: "已有基础",
    next: "remotion_timeline_route_map",
  },
  {
    referenceExample: "Three.js Ranking",
    familyId: "dashboard",
    content: "模型排行 / 3D 数据展示",
    status: "已有基础",
    next: "remotion_dashboard_brief",
  },
  {
    referenceExample: "Benchmark dashboard",
    familyId: "dashboard",
    content: "Benchmark 矩阵 / 分数对比",
    status: "已有基础",
    next: "remotion_dashboard_brief",
  },
  {
    referenceExample: "TikTok word-by-word captions",
    familyId: "subtitle_story",
    content: "口播 / 情绪 / 观点",
    status: "已有基础",
    next: "remotion_caption_story",
  },
  {
    referenceExample: "Cinematic Tech Intro",
    familyId: "subtitle_story",
    content: "科技开场 / 品牌感",
    status: "已有基础",
    next: "remotion_caption_intro",
  },
  {
    referenceExample: "Transparent CTA overlay",
    familyId: "subtitle_story",
    content: "行动号召 / 透明叠加",
    status: "已有基础",
    next: "remotion_cta_overlay",
  },
];

function ReferenceMappingPanel() {
  const statusColor = {
    "已有基础": { bg: "#f0fdf4", color: "#15803d", border: "#bbf7d0" },
    "部分可做": { bg: "#fffbeb", color: "#b45309", border: "#fde68a" },
    "待实现": { bg: "#f8fafc", color: "#64748b", border: "#e2e8f0" },
  } as const;
  return (
    <div
      data-testid="remotion-reference-mapping-panel"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
      }}
    >
      <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem", color: "#1e293b" }}>
        参考样例 → 可落地范式
      </h2>
      <p style={{ fontSize: "0.78rem", color: "#64748b", marginBottom: "0.85rem" }}>
        从 Remotion 官方 templates / Showcase / Prompt Showcase 抽象出的参考样例类型，映射到本页 5 个 family。
        "当前状态"列对齐上方"当前实现覆盖度"，避免重复。
      </p>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              <th style={thStyle}>参考样例类型</th>
              <th style={thStyle}>可转化 family</th>
              <th style={thStyle}>适合内容</th>
              <th style={thStyle}>当前状态</th>
              <th style={thStyle}>下一步实验</th>
            </tr>
          </thead>
          <tbody>
            {REFERENCE_MAPPING.map((row, i) => {
              const fam = FAMILIES.find((f) => f.id === row.familyId);
              const sc = statusColor[row.status];
              return (
                <tr
                  key={`${row.referenceExample}-${row.familyId}`}
                  style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "white" : "#fafafa" }}
                >
                  <td style={{ ...tdLabelStyle, fontStyle: "italic" }}>{row.referenceExample}</td>
                  <td style={tdCenterStyle}>
                    <span
                      style={{
                        background: `${fam?.accentColor}15`,
                        color: fam?.accentColor,
                        border: `1px solid ${fam?.accentColor}35`,
                        borderRadius: 6,
                        padding: "0.1rem 0.5rem",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                      }}
                    >
                      {fam?.icon} {fam?.name ?? row.familyId}
                    </span>
                  </td>
                  <td style={tdLabelStyle}>{row.content}</td>
                  <td style={tdCenterStyle}>
                    <span
                      style={{
                        background: sc.bg,
                        color: sc.color,
                        border: `1px solid ${sc.border}`,
                        borderRadius: 999,
                        padding: "0.1rem 0.55rem",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                      }}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td style={{ ...tdLabelStyle, fontSize: "0.75rem", color: "#475569" }}>
                    {row.next.startsWith("remotion_") ? (
                      <Link
                        to={`${REMOTION_GALLERY_BASE}&style_id=${row.next}`}
                        style={{ color: "#2563eb", fontWeight: 700, textDecoration: "none" }}
                      >
                        {row.next}
                      </Link>
                    ) : row.next}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ComparisonTable() {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
        <thead>
          <tr style={{ background: "#f8fafc" }}>
            <th style={thStyle}>维度</th>
            <th style={{ ...thStyle, color: "#7c3aed" }}>Data News</th>
            <th style={{ ...thStyle, color: "#2563eb" }}>Card Stack</th>
            <th style={{ ...thStyle, color: "#0891b2" }}>Timeline</th>
            <th style={{ ...thStyle, color: "#f59e0b" }}>Dashboard</th>
            <th style={{ ...thStyle, color: "#ec4899" }}>Subtitle Story</th>
          </tr>
        </thead>
        <tbody>
          {COMPARISON_MATRIX.map((row, i) => (
            <tr key={row.dimension} style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "white" : "#fafafa" }}>
              <td style={tdLabelStyle}>{row.dimension}</td>
              <td style={tdCenterStyle}>{row.dataNews}</td>
              <td style={tdCenterStyle}>{row.cardStack}</td>
              <td style={tdCenterStyle}>{row.timeline}</td>
              <td style={tdCenterStyle}>{row.dashboard}</td>
              <td style={tdCenterStyle}>{row.subtitleStory}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: "0.55rem 0.75rem",
  textAlign: "center",
  fontWeight: 600,
  fontSize: "0.82rem",
  borderBottom: "2px solid #e2e8f0",
};

const tdLabelStyle: React.CSSProperties = {
  padding: "0.55rem 0.75rem",
  fontWeight: 500,
  color: "#475569",
};

const tdCenterStyle: React.CSSProperties = {
  padding: "0.55rem 0.75rem",
  textAlign: "center",
  color: "#f59e0b",
};

// V1.2.3: Background Variant Matrix Component
const MATRIX_FAMILIES = [
  { id: "timeline_news", name: "Timeline", color: "#0891b2" },
  { id: "dashboard_brief", name: "Dashboard", color: "#f59e0b" },
  { id: "caption_story", name: "Caption Story", color: "#ec4899" },
];

const MATRIX_BACKGROUNDS = [
  { id: "tech_grid_dark", label: "tech_grid_dark" },
  { id: "aurora_blue", label: "aurora_blue" },
  { id: "glass_dashboard", label: "glass_dashboard" },
  { id: "warm_cinematic", label: "warm_cinematic" },
  { id: "neon_circuit", label: "neon_circuit" },
  { id: "deep_space", label: "deep_space" },
];

const TRANSITION_MATRIX_FAMILIES = [
  { id: "data_news", name: "Data News", color: "#7c3aed" },
  { id: "card_stack", name: "Card Stack", color: "#2563eb" },
  { id: "caption_story", name: "Caption Story", color: "#ec4899" },
];

const MATRIX_TRANSITIONS = [
  { id: "slide_fade", label: "slide_fade" },
  { id: "fade", label: "fade" },
  { id: "slide", label: "slide" },
  { id: "push", label: "push" },
  { id: "wipe", label: "wipe" },
  { id: "zoom_blur", label: "zoom_blur" },
  { id: "flip", label: "flip" },
  { id: "glitch", label: "glitch" },
];

// V1.2.4: Default transition matrix — limited to 1 family × 3 transitions = 3 clips (within MAX_MATRIX_ITEMS=9)
const DEFAULT_TRANSITION_FAMILY = [{ id: "data_news", name: "Data News", color: "#7c3aed" }];
const DEFAULT_TRANSITION_STYLES = [
  { id: "push", label: "push" },
  { id: "wipe", label: "wipe" },
  { id: "glitch", label: "glitch" },
];

// V1.2.4: Visual Style Preset Matrix constants
const VISUAL_STYLE_MATRIX_FAMILIES = [
  { id: "data_news", name: "Data News", color: "#7c3aed" },
  { id: "dashboard_brief", name: "Dashboard", color: "#f59e0b" },
  { id: "caption_story", name: "Caption Story", color: "#ec4899" },
];

const VISUAL_STYLE_PRESETS = [
  { id: "light_editorial", label: "light_editorial", desc: "浅色科技媒体" },
  { id: "warm_paper", label: "warm_paper", desc: "稳妥纸张报告" },
  { id: "bold_magazine", label: "bold_magazine", desc: "惊艳杂志爆点" },
];

const CAPABILITY_SUMMARY = [
  { label: "表现范式", value: "5", detail: "Data / Stack / Timeline / Dashboard / Caption" },
  { label: "动态背景", value: "6", detail: "含极光、玻璃、深空、霓虹电路" },
  { label: "转场风格", value: "8", detail: "含 wipe / push / zoom / flip / glitch" },
  { label: "沉淀 preset", value: "19+", detail: "可进入 Style Gallery 生成样片" },
];

const STYLE_DIMENSIONS = [
  {
    name: "版式范式",
    scope: "画面结构",
    current: "data_news / card_stack / timeline_news / dashboard_brief / caption_story",
    next: "继续做同一素材下的版式差异，而不是只换背景。",
  },
  {
    name: "背景系统",
    scope: "空间氛围",
    current: "tech_grid_dark / aurora_blue / glass_dashboard / warm_cinematic / neon_circuit / deep_space",
    next: "按内容类型选择默认背景，避免强背景抢正文。",
  },
  {
    name: "场景转场",
    scope: "段落切换",
    current: "slide_fade / fade / slide / push / wipe / zoom_blur / flip / glitch",
    next: "把稳定转场设为默认，把 glitch/flip 放到强风格 preset。",
  },
  {
    name: "数据动效",
    scope: "指标表达",
    current: "countup_bar / countup_number / none / chart_story / ranking_strip",
    next: "扩展折线、对比柱、排名推进等数据叙事。",
  },
  {
    name: "文字叙事",
    scope: "字幕与标题",
    current: "关键标题逐字浮现 / caption_story / caption_intro / cta_overlay",
    next: "补正文按行错峰、强调词闪现、口播节奏同步。",
  },
  {
    name: "报告型视频",
    scope: "长内容承载",
    current: "source-bound report opening + selected item frames",
    next: "把报告型默认 preset 与 workbench 路线配置打通。",
  },
];

const STYLE_SAMPLE_GROUPS = [
  {
    title: "版式样例",
    note: "同一份 keyPoints，用完全不同的画面组织方式呈现。",
    items: [
      { id: "remotion_card_stack", name: "卡片叠层", detail: "多信息点 / 资讯合集" },
      { id: "remotion_timeline_news", name: "时间线快讯", detail: "事件演进 / 阶段推进" },
      { id: "remotion_dashboard_brief", name: "指标看板", detail: "Benchmark / 排行对比" },
      { id: "remotion_caption_story", name: "大字旁白", detail: "观点摘要 / 口播解释" },
    ],
  },
  {
    title: "数据动效样例",
    note: "不是只显示文字，而是把数值、排行、图表作为 Remotion 动画主体。",
    items: [
      { id: "remotion_metric_motion", name: "动态数据栏目", detail: "数字滚动 + 数据条" },
      { id: "remotion_chart_story", name: "图表叙事", detail: "柱状图推进 + 当前解读" },
      { id: "remotion_ranking_strip", name: "排行条快报", detail: "Top list / 横向强弱条" },
    ],
  },
  {
    title: "文字叙事样例",
    note: "面向口播、观点和短视频标题节奏，重点不在数据图表。",
    items: [
      { id: "remotion_caption_intro", name: "电影感开场字屏", detail: "居中大标题 / 开场冲击" },
      { id: "remotion_cta_overlay", name: "行动号召叠层", detail: "结尾引导 / 系列预告" },
      { id: "remotion_caption_aurora_zoom", name: "极光大字叙事", detail: "极光背景 + 镜头推进" },
    ],
  },
  {
    title: "背景与转场组合样例",
    note: "从背景矩阵和转场矩阵中沉淀出的可用组合。",
    items: [
      { id: "remotion_report_stable", name: "稳重报告型", detail: "tech grid + slide fade" },
      { id: "remotion_dashboard_glass_wipe", name: "玻璃看板快报", detail: "glass + wipe" },
      { id: "remotion_deep_space_stack", name: "深空卡片栈", detail: "deep space + push" },
      { id: "remotion_neon_glitch", name: "霓虹故障高能", detail: "neon circuit + glitch" },
    ],
  },
];

const STYLE_MODULES = [
  {
    module: "表现范式",
    status: "已接入",
    coverage: "Data News / Card Stack / Timeline / Dashboard / Caption",
    optimize: "继续拉开同一内容在不同版式中的结构差异。",
    action: "查看范式总览",
    anchor: "#style-family-overview",
  },
  {
    module: "背景系统",
    status: "已扩展",
    coverage: "6 个动态背景，覆盖科技、玻璃、极光、深空、霓虹、暖电影。",
    optimize: "补默认搭配策略，避免背景抢正文。",
    action: "生成背景矩阵",
    anchor: "#background-matrix",
  },
  {
    module: "场景转场",
    status: "已扩展",
    coverage: "8 个转场，含 wipe / push / zoom / flip / glitch。",
    optimize: "区分默认转场和强风格转场，后者只进入高能 preset。",
    action: "生成转场矩阵",
    anchor: "#transition-matrix",
  },
  {
    module: "数据动效",
    status: "可继续扩",
    coverage: "countup_bar / countup_number / chart_story / ranking_strip。",
    optimize: "补折线推进、对比柱、排行榜变化等更强数据叙事。",
    action: "看数据样例",
    anchor: "#style-samples",
  },
  {
    module: "文字叙事",
    status: "可继续扩",
    coverage: "标题逐字浮现、Caption Story、Intro、CTA。",
    optimize: "补正文按行错峰、关键词闪现、字幕节奏模板。",
    action: "看文字样例",
    anchor: "#style-samples",
  },
  {
    module: "Gallery 沉淀",
    status: "已接入",
    coverage: "5 个矩阵沉淀组合已进入 Style Gallery preset。",
    optimize: "继续把实验矩阵里稳定组合沉淀为可复用 preset。",
    action: "查看可用组合",
    anchor: "#promoted-presets",
  },
];

function ModuleOptimizationPanel() {
  const statusStyle: Record<string, { bg: string; color: string; border: string }> = {
    "已接入": { bg: "#f0fdf4", color: "#15803d", border: "#bbf7d0" },
    "已扩展": { bg: "#eff6ff", color: "#2563eb", border: "#bfdbfe" },
    "可继续扩": { bg: "#fffbeb", color: "#b45309", border: "#fde68a" },
  };

  return (
    <div
      id="module-optimization"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap", marginBottom: "0.9rem" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          子模块优化看板
        </h2>
        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          从实验能力到可用能力
        </span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "0.85rem",
        }}
      >
        {STYLE_MODULES.map((item) => {
          const sc = statusStyle[item.status] ?? statusStyle["可继续扩"];
          return (
            <a
              key={item.module}
              href={item.anchor}
              style={{
                textDecoration: "none",
                color: "inherit",
                border: "1px solid #e2e8f0",
                borderRadius: "12px",
                padding: "0.9rem",
                background: "#ffffff",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", marginBottom: "0.5rem" }}>
                <div style={{ fontSize: "0.9rem", fontWeight: 800, color: "#1e293b" }}>{item.module}</div>
                <span style={{ fontSize: "0.68rem", fontWeight: 800, color: sc.color, background: sc.bg, border: `1px solid ${sc.border}`, borderRadius: 999, padding: "0.1rem 0.45rem", whiteSpace: "nowrap" }}>
                  {item.status}
                </span>
              </div>
              <div style={{ fontSize: "0.72rem", color: "#475569", lineHeight: 1.5, marginBottom: "0.45rem" }}>
                {item.coverage}
              </div>
              <div style={{ fontSize: "0.7rem", color: "#64748b", lineHeight: 1.5, marginBottom: "0.55rem" }}>
                {item.optimize}
              </div>
              <div style={{ fontSize: "0.72rem", fontWeight: 800, color: "#2563eb" }}>
                {item.action}
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

function CapabilitySummaryPanel() {
  return (
    <div
      id="capability-summary"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1rem",
        marginBottom: "1.25rem",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
        }}
      >
        {CAPABILITY_SUMMARY.map((item) => (
          <div
            key={item.label}
            style={{
              border: "1px solid #e2e8f0",
              borderRadius: "10px",
              padding: "0.8rem",
              background: "#f8fafc",
            }}
          >
            <div style={{ fontSize: "1.35rem", fontWeight: 900, color: "#1e293b", lineHeight: 1 }}>
              {item.value}
            </div>
            <div style={{ fontSize: "0.8rem", fontWeight: 800, color: "#334155", marginTop: "0.35rem" }}>
              {item.label}
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "0.25rem", lineHeight: 1.45 }}>
              {item.detail}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StyleDimensionsPanel() {
  return (
    <div
      id="style-dimensions"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap", marginBottom: "0.9rem" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          Remotion 样式维度地图
        </h2>
        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          不只是背景和转场
        </span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              <th style={thStyle}>维度</th>
              <th style={thStyle}>影响范围</th>
              <th style={thStyle}>当前已有能力</th>
              <th style={thStyle}>下一步价值</th>
            </tr>
          </thead>
          <tbody>
            {STYLE_DIMENSIONS.map((row, i) => (
              <tr key={row.name} style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "white" : "#fafafa" }}>
                <td style={{ ...tdLabelStyle, fontWeight: 800, color: "#1e293b" }}>{row.name}</td>
                <td style={tdLabelStyle}>{row.scope}</td>
                <td style={{ ...tdLabelStyle, color: "#475569" }}>{row.current}</td>
                <td style={{ ...tdLabelStyle, color: "#64748b" }}>{row.next}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ExpandedStyleSamplesPanel() {
  return (
    <div
      id="style-samples"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap", marginBottom: "0.9rem" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          可扩展样式样例
        </h2>
        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          样式不等于换皮
        </span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
          gap: "0.9rem",
        }}
      >
        {STYLE_SAMPLE_GROUPS.map((group) => (
          <div
            key={group.title}
            style={{
              border: "1px solid #e2e8f0",
              borderRadius: "12px",
              padding: "0.9rem",
              background: "#ffffff",
            }}
          >
            <div style={{ fontSize: "0.9rem", fontWeight: 800, color: "#1e293b", marginBottom: "0.35rem" }}>
              {group.title}
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", lineHeight: 1.5, marginBottom: "0.75rem" }}>
              {group.note}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
              {group.items.map((item) => (
                <Link
                  key={item.id}
                  to={`${REMOTION_GALLERY_BASE}&style_id=${item.id}`}
                  style={{
                    textDecoration: "none",
                    border: "1px solid #e2e8f0",
                    borderRadius: "8px",
                    padding: "0.5rem 0.6rem",
                    background: "#f8fafc",
                  }}
                >
                  <div style={{ fontSize: "0.78rem", fontWeight: 800, color: "#2563eb" }}>
                    {item.name}
                  </div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "0.15rem" }}>
                    {item.detail}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const PROMOTED_STYLE_PRESETS = [
  {
    id: "remotion_report_stable",
    name: "稳重报告型",
    useCase: "报告型长内容 / 阅读优先",
    family: "data_news",
    background: "tech_grid_dark",
    transition: "slide_fade",
    color: "#3b82f6",
  },
  {
    id: "remotion_dashboard_glass_wipe",
    name: "玻璃看板快报",
    useCase: "Benchmark / 指标对比",
    family: "dashboard_brief",
    background: "glass_dashboard",
    transition: "wipe",
    color: "#2563eb",
  },
  {
    id: "remotion_deep_space_stack",
    name: "深空卡片栈",
    useCase: "多信息点 / 资讯合集",
    family: "card_stack",
    background: "deep_space",
    transition: "push",
    color: "#38bdf8",
  },
  {
    id: "remotion_neon_glitch",
    name: "霓虹故障高能",
    useCase: "强风格短视频 / 科技爆点",
    family: "data_news",
    background: "neon_circuit",
    transition: "glitch",
    color: "#ec4899",
  },
  {
    id: "remotion_caption_aurora_zoom",
    name: "极光大字叙事",
    useCase: "观点摘要 / 口播解释",
    family: "caption_story",
    background: "aurora_blue",
    transition: "zoom_blur",
    color: "#8b5cf6",
  },
];

function PromotedStylePresets() {
  return (
    <div
      id="promoted-presets"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.9rem", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          已沉淀可用组合
        </h2>
        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          背景矩阵 + 转场矩阵 → Style Gallery preset
        </span>
      </div>
      <p style={{ fontSize: "0.82rem", color: "#64748b", marginTop: 0, marginBottom: "1rem", lineHeight: 1.6 }}>
        这些不是新的实验入口，而是从现有背景/转场实验中沉淀出的可直接生成样片的 Remotion 组合。
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
          gap: "0.85rem",
        }}
      >
        {PROMOTED_STYLE_PRESETS.map((preset) => (
          <Link
            key={preset.id}
            to={`${REMOTION_GALLERY_BASE}&style_id=${preset.id}`}
            style={{
              textDecoration: "none",
              color: "inherit",
              border: `1px solid ${preset.color}2f`,
              borderRadius: "12px",
              padding: "0.85rem",
              background: `linear-gradient(135deg, ${preset.color}10 0%, #ffffff 70%)`,
            }}
          >
            <div style={{ fontSize: "0.9rem", fontWeight: 800, color: "#1e293b", marginBottom: "0.35rem" }}>
              {preset.name}
            </div>
            <div style={{ fontSize: "0.74rem", color: "#64748b", marginBottom: "0.7rem" }}>
              {preset.useCase}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem", fontSize: "0.7rem", color: "#475569" }}>
              <span>范式：{preset.family}</span>
              <span>背景：{preset.background}</span>
              <span>转场：{preset.transition}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function BackgroundVariantMatrix({
  result,
  onReload,
  loading,
}: {
  result: MatrixResponse | null;
  onReload: () => void;
  loading: boolean;
}) {
  const resolveUrl = (u: string) =>
    u && u.startsWith("/runtime/")
      ? `${import.meta.env.VITE_API_BASE?.replace(/\/video-lab$/, "") ?? ""}${u}`
      : u || "";

  // Build 3×3 grid: rows = families, cols = backgrounds
  const grid = MATRIX_FAMILIES.map((fam) => ({
    family: fam,
    cells: MATRIX_BACKGROUNDS.map((bg) => ({
      bg,
      item: result?.items.find(
        (it) => it.family === fam.id && it.backgroundPreset === bg.id
      ),
    })),
  }));

  const totalSuccess = result?.items.filter((it) => it.success).length ?? 0;
  const totalItems = result?.items.length ?? 0;

  return (
    <div
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.85rem", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          背景差异化实验 · V1.2.3
        </h2>
        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          3 family × 3 background = 9 clips
        </span>
        <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {result && (
            <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
              {totalSuccess}/{totalItems} 成功 · {result.totalElapsedMs}ms
            </span>
          )}
          <button
            onClick={onReload}
            disabled={loading}
            style={{
              background: loading ? "#94a3b8" : "#0891b2",
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "0.45rem 1rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              cursor: loading ? "wait" : "pointer",
            }}
          >
            {loading ? "渲染中..." : "重新生成"}
          </button>
        </div>
      </div>

      <p style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.85rem" }}>
        同一内容（Timeline / Dashboard / Caption Story）× 3 种背景，观察背景能否让同一种 family 呈现不同的视觉氛围。
        Lab-only，不写 Style Sweep job 或 Style Gallery sample。
      </p>

      {/* 3×3 Responsive Grid — each cell gets more space */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${MATRIX_BACKGROUNDS.length}, minmax(150px, 1fr))`,
          gap: "0.65rem",
        }}
      >
        {grid.map((row) =>
          row.cells.map((cell) => {
            const item = cell.item;
            const success = item?.success ?? false;
            const hasVideo = success && Boolean(item?.videoUrl);

            return (
              <div
                key={`${row.family.id}-${cell.bg.id}`}
                style={{
                  border: `1px solid ${row.family.color}30`,
                  borderRadius: "10px",
                  overflow: "hidden",
                  background: "white",
                }}
              >
                {/* Card header — compact */}
                <div
                  style={{
                    background: `linear-gradient(135deg, ${row.family.color}15 0%, ${row.family.color}06 100%)`,
                    borderBottom: `1px solid ${row.family.color}25`,
                    padding: "0.4rem 0.65rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: row.family.color }}>
                    {row.family.name}
                  </span>
                  <span style={{ color: "#e2e8f0", fontSize: "0.65rem" }}>×</span>
                  <span style={{ fontSize: "0.7rem", color: "#64748b" }}>
                    {cell.bg.label}
                  </span>
                </div>

                {/* Video or status — enlarged */}
                <div style={{ padding: "0.4rem", background: "#0f172a" }}>
                  {hasVideo && item ? (
                    <video
                      controls
                      src={resolveUrl(item.videoUrl)}
                      style={{
                        width: "100%",
                        height: "220px",
                        objectFit: "contain",
                        display: "block",
                        borderRadius: "6px",
                        background: "#0a0e1a",
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        height: "220px",
                        background: "#1e293b",
                        borderRadius: "6px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.72rem",
                        color: "#ef4444",
                      }}
                    >
                      {item ? `失败：${item.message}` : "待渲染"}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div style={{
                  padding: "0.3rem 0.65rem",
                  borderTop: `1px solid ${row.family.color}15`,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}>
                  {item?.success ? (
                    <span style={{ fontSize: "0.65rem", color: "#16a34a" }}>✓ 成功</span>
                  ) : item ? (
                    <span style={{ fontSize: "0.65rem", color: "#ef4444" }}>✗ 失败</span>
                  ) : (
                    <span style={{ fontSize: "0.65rem", color: "#94a3b8" }}>—</span>
                  )}
                  <span style={{ fontSize: "0.62rem", color: "#94a3b8" }}>
                    {item ? `${item.elapsedMs}ms` : ""}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Observation hints */}
      {result && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.85rem 1rem",
            background: "#f8fafc",
            borderRadius: "8px",
            fontSize: "0.78rem",
            color: "#475569",
            lineHeight: 1.6,
          }}
        >
          <div style={{ fontWeight: 600, color: "#1e293b", marginBottom: "0.3rem" }}>观察提示：</div>
          <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
            <li>三种背景在同一 family 中是否肉眼可区分？</li>
            <li>背景是否遮挡正文文字？文字仍可读吗？</li>
            <li>9:16 画面中背景与内容的关系是否协调？</li>
            <li>family 结构差异（Timeline 时间线 / Dashboard 指标卡 / Caption 大字）在不同背景下是否仍可辨识？</li>
          </ul>
        </div>
      )}
    </div>
  );
}

function TransitionVariantMatrix({
  result,
  onReload,
  loading,
}: {
  result: TransitionMatrixResponse | null;
  onReload: () => void;
  loading: boolean;
}) {
  const resolveUrl = (u: string) =>
    u && u.startsWith("/runtime/")
      ? `${import.meta.env.VITE_API_BASE?.replace(/\/video-lab$/, "") ?? ""}${u}`
      : u || "";

  // Grid derived from actual result items — avoids showing empty cells beyond what was submitted
  const grid = result?.items
    ? (() => {
        const byFamily = new Map<string, typeof result.items>();
        for (const it of result.items) {
          if (!byFamily.has(it.family)) byFamily.set(it.family, []);
          byFamily.get(it.family)!.push(it);
        }
        return Array.from(byFamily.entries()).map(([familyId, items]) => {
          const fam = TRANSITION_MATRIX_FAMILIES.find((f) => f.id === familyId) ?? {
            id: familyId,
            name: familyId,
            color: "#64748b",
          };
          return {
            family: fam,
            cells: items.map((it) => ({
              transition: MATRIX_TRANSITIONS.find((t) => t.id === it.transitionStyle) ?? {
                id: it.transitionStyle,
                label: it.transitionStyle,
              },
              item: it,
            })),
          };
        });
      })()
    : [];

  const totalSuccess = result?.items.filter((it) => it.success).length ?? 0;
  const totalItems = result?.items.length ?? 0;

  return (
    <div
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.85rem", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          转场差异化实验 · V1.2.4
        </h2>
        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          1 family × 3 transitions = 3 clips
        </span>
        <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {result && (
            <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
              {totalSuccess}/{totalItems} 成功 · {result.totalElapsedMs}ms
            </span>
          )}
          <button
            onClick={onReload}
            disabled={loading}
            style={{
              background: loading ? "#94a3b8" : "#7c3aed",
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "0.45rem 1rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              cursor: loading ? "wait" : "pointer",
            }}
          >
            {loading ? "渲染中..." : "生成转场矩阵"}
          </button>
        </div>
      </div>

      <p style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.85rem" }}>
        基于现有背景差异化实验框架，固定内容和背景，横向比较 slide_fade / fade / slide / push / wipe / zoom_blur。
        Lab-only，不写 Style Sweep job 或 Style Gallery sample。
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${MATRIX_TRANSITIONS.length}, minmax(150px, 1fr))`,
          gap: "0.65rem",
          overflowX: "auto",
        }}
      >
        {grid.map((row) =>
          row.cells.map((cell) => {
            const item = cell.item;
            const success = item?.success ?? false;
            const hasVideo = success && Boolean(item?.videoUrl);

            return (
              <div
                key={`${row.family.id}-${cell.transition.id}`}
                style={{
                  minWidth: 150,
                  border: `1px solid ${row.family.color}30`,
                  borderRadius: "10px",
                  overflow: "hidden",
                  background: "white",
                }}
              >
                <div
                  style={{
                    background: `linear-gradient(135deg, ${row.family.color}15 0%, ${row.family.color}06 100%)`,
                    borderBottom: `1px solid ${row.family.color}25`,
                    padding: "0.4rem 0.65rem",
                  }}
                >
                  <div style={{ fontSize: "0.75rem", fontWeight: 700, color: row.family.color }}>
                    {row.family.name}
                  </div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b" }}>
                    {cell.transition.label}
                  </div>
                </div>

                <div style={{ padding: "0.4rem", background: "#0f172a" }}>
                  {hasVideo && item ? (
                    <video
                      controls
                      src={resolveUrl(item.videoUrl)}
                      style={{
                        width: "100%",
                        height: "180px",
                        objectFit: "contain",
                        display: "block",
                        borderRadius: "6px",
                        background: "#0a0e1a",
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        height: "180px",
                        background: "#1e293b",
                        borderRadius: "6px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.72rem",
                        color: "#ef4444",
                        padding: "0.5rem",
                        textAlign: "center",
                      }}
                    >
                      {item ? `失败：${item.message}` : "待渲染"}
                    </div>
                  )}
                </div>

                <div style={{
                  padding: "0.3rem 0.65rem",
                  borderTop: `1px solid ${row.family.color}15`,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}>
                  {item?.success ? (
                    <span style={{ fontSize: "0.65rem", color: "#16a34a" }}>成功</span>
                  ) : item ? (
                    <span style={{ fontSize: "0.65rem", color: "#ef4444" }}>失败</span>
                  ) : (
                    <span style={{ fontSize: "0.65rem", color: "#94a3b8" }}>-</span>
                  )}
                  <span style={{ fontSize: "0.62rem", color: "#94a3b8" }}>
                    {item ? `${item.elapsedMs}ms` : ""}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {result && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.85rem 1rem",
            background: "#f8fafc",
            borderRadius: "8px",
            fontSize: "0.78rem",
            color: "#475569",
            lineHeight: 1.6,
          }}
        >
          <div style={{ fontWeight: 600, color: "#1e293b", marginBottom: "0.3rem" }}>观察提示：</div>
          <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
            <li>fade 是否更柔和，slide/push 是否有明确方向感。</li>
            <li>wipe 是否有可见擦除边界，zoom_blur 是否有镜头推进感。</li>
            <li>同一 transition 在 Data News / Card Stack / Caption Story 中是否仍可辨识。</li>
          </ul>
        </div>
      )}
    </div>
  );
}

// V1.2.4: Visual Style Preset Matrix Component
function VisualStyleVariantMatrix({
  result,
  onReload,
  loading,
}: {
  result: VisualStyleMatrixResponse | null;
  onReload: () => void;
  loading: boolean;
}) {
  const resolveUrl = (u: string) =>
    u && u.startsWith("/runtime/")
      ? `${import.meta.env.VITE_API_BASE?.replace(/\/video-lab$/, "") ?? ""}${u}`
      : u || "";

  const grid = VISUAL_STYLE_MATRIX_FAMILIES.map((fam) => ({
    family: fam,
    cells: VISUAL_STYLE_PRESETS.map((preset) => ({
      preset,
      item: result?.items.find(
        (it) => it.family === fam.id && it.visualStylePreset === preset.id
      ),
    })),
  }));

  const totalSuccess = result?.items.filter((it) => it.success).length ?? 0;
  const totalItems = result?.items.length ?? 0;

  return (
    <div
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.85rem", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          视觉风格矩阵 · V1.2.4
        </h2>
        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          3 family × 3 visual styles = 9 clips
        </span>
        <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {result && (
            <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
              {totalSuccess}/{totalItems} 成功 · {result.totalElapsedMs}ms
            </span>
          )}
          <button
            onClick={onReload}
            disabled={loading}
            style={{
              background: loading ? "#94a3b8" : "#7c3aed",
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "0.45rem 1rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              cursor: loading ? "wait" : "pointer",
            }}
          >
            {loading ? "渲染中..." : "运行视觉风格矩阵"}
          </button>
        </div>
      </div>

      <p style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.85rem" }}>
        同一内容（Data News / Dashboard / Caption Story）× 3 种视觉风格（浅色编辑 / 暖色纸张 / 杂志爆点），
        观察整体色调、卡片、边框、文字颜色的变化。Lab-only，不写 Style Sweep job 或 Style Gallery sample。
      </p>

      {/* 3×3 Responsive Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${VISUAL_STYLE_PRESETS.length}, minmax(150px, 1fr))`,
          gap: "0.65rem",
        }}
      >
        {grid.map((row) =>
          row.cells.map((cell) => {
            const item = cell.item;
            const success = item?.success ?? false;
            const hasVideo = success && Boolean(item?.videoUrl);

            return (
              <div
                key={`${row.family.id}-${cell.preset.id}`}
                style={{
                  border: `1px solid ${row.family.color}30`,
                  borderRadius: "10px",
                  overflow: "hidden",
                  background: "white",
                }}
              >
                {/* Card header */}
                <div
                  style={{
                    background: `linear-gradient(135deg, ${row.family.color}15 0%, ${row.family.color}06 100%)`,
                    borderBottom: `1px solid ${row.family.color}25`,
                    padding: "0.4rem 0.65rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: row.family.color }}>
                    {row.family.name}
                  </span>
                  <span style={{ color: "#e2e8f0", fontSize: "0.65rem" }}>×</span>
                  <span style={{ fontSize: "0.7rem", color: "#64748b" }}>
                    {cell.preset.label}
                  </span>
                </div>

                {/* Video or status */}
                <div style={{ padding: "0.4rem", background: "#0f172a" }}>
                  {hasVideo && item ? (
                    <video
                      controls
                      src={resolveUrl(item.videoUrl)}
                      style={{
                        width: "100%",
                        height: "220px",
                        objectFit: "contain",
                        display: "block",
                        borderRadius: "6px",
                        background: "#0a0e1a",
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        height: "220px",
                        background: "#1e293b",
                        borderRadius: "6px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.72rem",
                        color: "#ef4444",
                      }}
                    >
                      {item ? `失败：${item.message}` : "待渲染"}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div style={{
                  padding: "0.3rem 0.65rem",
                  borderTop: `1px solid ${row.family.color}15`,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}>
                  {item?.success ? (
                    <span style={{ fontSize: "0.65rem", color: "#16a34a" }}>✓ 成功</span>
                  ) : item ? (
                    <span style={{ fontSize: "0.65rem", color: "#ef4444" }}>✗ 失败</span>
                  ) : (
                    <span style={{ fontSize: "0.65rem", color: "#94a3b8" }}>—</span>
                  )}
                  <span style={{ fontSize: "0.62rem", color: "#94a3b8" }}>
                    {item ? `${item.elapsedMs}ms` : ""}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Observation hints */}
      {result && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.85rem 1rem",
            background: "#f8fafc",
            borderRadius: "8px",
            fontSize: "0.78rem",
            color: "#475569",
            lineHeight: 1.6,
          }}
        >
          <div style={{ fontWeight: 600, color: "#1e293b", marginBottom: "0.3rem" }}>观察提示：</div>
          <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
            <li>light_editorial 是否明显更白/浅色，bold_magazine 是否明显更黑/高对比。</li>
            <li>warm_paper 是否呈现暖色米白基调，与其他两者明显不同。</li>
            <li>同一 family 在 3 种视觉风格下是否仍保持版式可辨识性。</li>
          </ul>
        </div>
      )}
    </div>
  );
}

// V1.2.5+: Visual Technique meta — front-end-only metadata for UI acceptance panel.
// 状态字段: status=asset_verified, acceptance=visually_unaccepted (deliberately NOT visually_accepted).
type VisualTechniqueMeta = {
  name: string;
  source: string;
  status: "asset_verified";
  acceptance: "visually_unaccepted";
  description: string;
  suitableFor: string[];
  observePoints: string[];
};

const VISUAL_TECHNIQUE_META: Record<string, VisualTechniqueMeta> = {
  academic_sketch: {
    name: "学术手绘草稿流",
    source: "Effect Prototype Gallery / academic",
    status: "asset_verified",
    acceptance: "visually_unaccepted",
    description: "米白纸张、网格线、手绘批注，用于论文解读、AI 原理解释、研究报告摘要。",
    suitableFor: ["论文解读", "AI 原理解释", "研究报告摘要", "知识类短视频"],
    observePoints: ["米白纸张是否明显", "网格线是否可见", "是否有手绘批注", "正文是否可读"],
  },
  blueprint: {
    name: "工程蓝图晒图风",
    source: "Effect Prototype Gallery / blueprint",
    status: "asset_verified",
    acceptance: "visually_unaccepted",
    description: "深蓝晒图纸、工程网格、角标记，用于架构解析、系统设计、技术规格说明。",
    suitableFor: ["架构解析", "系统设计", "技术规格", "工程原理"],
    observePoints: ["蓝图感是否明显", "工程网格是否可见", "角标记是否可见", "正文是否可读"],
  },
  data_viz_dashboard: {
    name: "数据动态看板",
    source: "Effect Prototype Gallery / dataviz",
    status: "asset_verified",
    acceptance: "visually_unaccepted",
    description: "动态图表、柱状图、折线图、圆环图和指标 chip，用于 Benchmark、模型对比、产品数据。",
    suitableFor: ["AI Benchmark", "模型能力对比", "产品数据", "性能报告"],
    observePoints: ["是否像数据看板", "图表元素是否明显", "指标 chip 是否可见", "正文是否可读"],
  },
  agent_sandbox_25d: {
    name: "智能体沙盒模拟",
    source: "Effect Prototype Gallery / sandbox",
    status: "asset_verified",
    acceptance: "visually_unaccepted",
    description: "2.5D 空间、Agent 节点、连接线和数据包，用于多智能体协作、工作流、系统架构说明。",
    suitableFor: ["Agent 工作流", "多智能体协作", "AI 自动化流程", "系统架构"],
    observePoints: ["节点是否明显", "连接线是否可见", "是否有数据包流动", "是否有系统沙盒感"],
  },
  kinetic_code_typography: {
    name: "动态代码排版",
    source: "Effect Prototype Gallery / typography",
    status: "asset_verified",
    acceptance: "visually_unaccepted",
    description: "IDE 背景、代码行、语法高亮、终端日志和光标闪烁，用于开发者内容、API 讲解、代码教程。",
    suitableFor: ["开发教程", "API 讲解", "代码片段解释", "开源项目摘要"],
    observePoints: ["是否像代码编辑器", "代码行是否可见", "终端日志是否可见", "正文是否可读"],
  },
};

// V1.2.6+: Visual Technique Test Fixtures — content modes for testing different technique semantics
export type VisualTechniqueFixtureId =
  | "generic_ai_eval"
  | "academic_explainer"
  | "blueprint_architecture"
  | "data_dashboard"
  | "agent_sandbox"
  | "code_typography";

export const VISUAL_TECHNIQUE_FIXTURES: Readonly<{
  [K in VisualTechniqueFixtureId]: {
    name: string;
    purpose: string;
    recommendedTechniques: readonly string[];
    content: string;
  };
}> = {
  generic_ai_eval: {
    name: "通用 AI 评测",
    purpose: "通用横向比较，适合快速冒烟测试。",
    recommendedTechniques: ["academic_sketch", "blueprint", "data_viz_dashboard", "agent_sandbox_25d", "kinetic_code_typography"],
    content:
      "研究显示，新一代 AI 模型在多模态理解、工具调用和复杂推理任务上都有显著提升，但评测指标仍然难以完整衡量真实智能。",
  },

  academic_explainer: {
    name: "学术解释",
    purpose: "测试 academic_sketch 是否适合解释概念、推理过程、研究摘要。",
    recommendedTechniques: ["academic_sketch"],
    content:
      "为什么 AI 评测越来越难？过去只看最终答案，现在还要看推理过程、工具调用和失败修正。真正的评测像观察学生解题，而不是只看分数。",
  },

  blueprint_architecture: {
    name: "工程架构",
    purpose: "测试 blueprint 是否适合系统架构、模块关系、工程流程。",
    recommendedTechniques: ["blueprint", "agent_sandbox_25d"],
    content:
      "一个 AI Agent 系统由四层组成：输入层接收任务，规划层拆解步骤，工具层执行动作，记忆层保存上下文。各层通过消息通道连接，形成可追踪的执行链路。",
  },

  data_dashboard: {
    name: "数据看板",
    purpose: "测试 data_viz_dashboard 是否适合 Benchmark、模型对比、产品数据。",
    recommendedTechniques: ["data_viz_dashboard"],
    content:
      "模型 A 在多模态理解上提升 24%，工具调用成功率达到 87%，长上下文任务成本下降 31%。这些指标说明模型能力正在从单点问答转向系统级表现。",
  },

  agent_sandbox: {
    name: "Agent 沙盒",
    purpose: "测试 agent_sandbox_25d 是否适合多智能体协作、工具调用、工作流解释。",
    recommendedTechniques: ["agent_sandbox_25d"],
    content:
      "Planner 负责拆解任务，Model 负责生成方案，Tool 负责执行外部动作，Memory 负责记录状态。多个 Agent 通过消息通道协作，并在失败时重新规划。",
  },

  code_typography: {
    name: "代码教程",
    purpose: "测试 kinetic_code_typography 是否适合 API 讲解、代码流程、开发者内容。",
    recommendedTechniques: ["kinetic_code_typography"],
    content:
      "调用模型 API 的核心步骤包括：构造 request，发送 prompt，解析 response，处理错误，并将日志写入终端。稳定的错误处理比一次成功调用更重要。",
  },
} as const;

// V1.2.7+: Visual Technique ID — used for family adaptation matrix
export type VisualTechniqueId =
  | "academic_sketch"
  | "blueprint"
  | "data_viz_dashboard"
  | "agent_sandbox_25d"
  | "kinetic_code_typography";

const ALL_VISUAL_TECHNIQUES: VisualTechniqueId[] = [
  "academic_sketch",
  "blueprint",
  "data_viz_dashboard",
  "agent_sandbox_25d",
  "kinetic_code_typography",
];

// V1.2.7+: Family list for adaptation testing (limited to 3 to avoid MAX_MATRIX_ITEMS overflow)
const FAMILY_ADAPTATION_FAMILIES = [
  { id: "data_news", name: "Data News", desc: "数据新闻 / 指标卡片" },
  { id: "timeline_news", name: "Timeline News", desc: "时间线 / 流程推进" },
  { id: "caption_story", name: "Caption Story", desc: "大字叙事 / 解释型内容" },
];

// V1.2.5+: Local-only visual acceptance state — front-end ephemeral, never persisted.
type LocalVisualAcceptance = "pending" | "accepted" | "partial" | "rejected";

const ACCEPTANCE_LABEL: Record<LocalVisualAcceptance, string> = {
  pending: "待验收",
  accepted: "通过",
  partial: "部分通过",
  rejected: "不通过",
};

const ACCEPTANCE_COLOR: Record<LocalVisualAcceptance, { bg: string; fg: string; border: string }> = {
  pending: { bg: "#f1f5f9", fg: "#64748b", border: "#cbd5e1" },
  accepted: { bg: "#dcfce7", fg: "#15803d", border: "#86efac" },
  partial: { bg: "#fef3c7", fg: "#a16207", border: "#fcd34d" },
  rejected: { bg: "#fee2e2", fg: "#b91c1c", border: "#fca5a5" },
};

// V1.2.5+: Visual Technique Matrix Component — upgraded to UI acceptance panel
function VisualTechniqueVariantMatrix({
  result,
  onReload,
  loading,
  clipSeconds,
  onClipSecondsChange,
  fixtureId,
  onFixtureIdChange,
  matrixMode,
  onMatrixModeChange,
  adaptationTechnique,
  onAdaptationTechniqueChange,
}: {
  result: VisualTechniqueMatrixResponse | null;
  onReload: () => void;
  loading: boolean;
  clipSeconds: number;
  onClipSecondsChange: (s: number) => void;
  fixtureId: VisualTechniqueFixtureId;
  onFixtureIdChange: (id: VisualTechniqueFixtureId) => void;
  matrixMode: "technique_compare" | "family_adaptation";
  onMatrixModeChange: (mode: "technique_compare" | "family_adaptation") => void;
  adaptationTechnique: VisualTechniqueId;
  onAdaptationTechniqueChange: (technique: VisualTechniqueId) => void;
}) {
  const resolveUrl = (u: string) =>
    u && u.startsWith("/runtime/")
      ? `${import.meta.env.VITE_API_BASE?.replace(/\/video-lab$/, "") ?? ""}${u}`
      : u || "";

  const fixture = VISUAL_TECHNIQUE_FIXTURES[fixtureId];

  // Local-only visual acceptance state — UI ephemeral, never persisted to backend.
  const [localAcceptance, setLocalAcceptance] = useState<Record<string, LocalVisualAcceptance>>({});

  const setAcceptance = (key: string, value: LocalVisualAcceptance) => {
    setLocalAcceptance((prev) => ({ ...prev, [key]: value }));
  };

  // Summary counts
  const totalCount = result?.items.length ?? 0;
  const summary = {
    accepted: Object.values(localAcceptance).filter((v) => v === "accepted").length,
    partial: Object.values(localAcceptance).filter((v) => v === "partial").length,
    rejected: Object.values(localAcceptance).filter((v) => v === "rejected").length,
    pending: result?.items.filter((it) => !localAcceptance[`${it.family}-${it.visualTechnique}`] ||
      localAcceptance[`${it.family}-${it.visualTechnique}`] === "pending").length ?? 0,
  };

  return (
    <div
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "1.25rem",
        marginBottom: "2.5rem",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.85rem", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
          视觉技法矩阵 · V1.2.7
        </h2>

        {/* Matrix mode selector */}
        <div style={{ display: "flex", gap: "0.3rem" }}>
          <button
            onClick={() => onMatrixModeChange("technique_compare")}
            disabled={loading}
            style={{
              background: matrixMode === "technique_compare" ? "#7c3aed" : "white",
              color: matrixMode === "technique_compare" ? "white" : "#475569",
              border: `1px solid ${matrixMode === "technique_compare" ? "#7c3aed" : "#cbd5e1"}`,
              borderRadius: "6px",
              padding: "0.2rem 0.6rem",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Technique 横向比较
          </button>
          <button
            onClick={() => onMatrixModeChange("family_adaptation")}
            disabled={loading}
            style={{
              background: matrixMode === "family_adaptation" ? "#7c3aed" : "white",
              color: matrixMode === "family_adaptation" ? "white" : "#475569",
              border: `1px solid ${matrixMode === "family_adaptation" ? "#7c3aed" : "#cbd5e1"}`,
              borderRadius: "6px",
              padding: "0.2rem 0.6rem",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Family 适配测试
          </button>
        </div>

        <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 999, padding: "0.15rem 0.55rem" }}>
          {matrixMode === "technique_compare"
            ? "1 family × 5 techniques = 5 clips"
            : `${FAMILY_ADAPTATION_FAMILIES.length} families × 1 technique = ${FAMILY_ADAPTATION_FAMILIES.length} clips`}
        </span>
        <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {result && (
            <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
              {result.items.filter((it) => it.success).length}/{result.items.length} 生成成功 · {result.totalElapsedMs}ms
            </span>
          )}
          <button
            onClick={onReload}
            disabled={loading}
            style={{
              background: loading ? "#94a3b8" : "#7c3aed",
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "0.45rem 1rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              cursor: loading ? "wait" : "pointer",
            }}
          >
            {loading ? "渲染中..." : "运行视觉技法矩阵"}
          </button>
        </div>
      </div>

      {/* Fixture Selector + Info Row */}
      <div
        style={{
          marginBottom: "1rem",
          padding: "0.75rem 1rem",
          background: "#eff6ff",
          border: "1px solid #bfdbfe",
          borderRadius: "8px",
          fontSize: "0.78rem",
          color: "#1e3a8a",
          lineHeight: 1.7,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: "0.5rem", color: "#1e40af" }}>
          🧪 当前测试模式：{clipSeconds}s {clipSeconds === 2 ? "冒烟预览" : clipSeconds === 6 ? "视觉预览" : "长预览"}
        </div>

        {/* Fixture selector */}
        <div style={{ marginBottom: "0.6rem" }}>
          <div style={{ fontWeight: 600, marginBottom: "0.3rem", color: "#1e40af" }}>
            测试内容：
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
            {(Object.keys(VISUAL_TECHNIQUE_FIXTURES) as VisualTechniqueFixtureId[]).map((id) => {
              const fix = VISUAL_TECHNIQUE_FIXTURES[id];
              const active = fixtureId === id;
              return (
                <button
                  key={id}
                  onClick={() => onFixtureIdChange(id)}
                  disabled={loading}
                  style={{
                    background: active ? "#7c3aed" : "white",
                    color: active ? "white" : "#475569",
                    border: `1px solid ${active ? "#7c3aed" : "#cbd5e1"}`,
                    borderRadius: "6px",
                    padding: "0.2rem 0.6rem",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}
                >
                  {fix.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Fixture info */}
        <div
          style={{
            background: "white",
            border: "1px solid #bfdbfe",
            borderRadius: "6px",
            padding: "0.5rem 0.75rem",
            marginBottom: "0.5rem",
          }}
        >
          <div style={{ fontWeight: 700, color: "#1e40af", marginBottom: "0.2rem" }}>
            {fixture.name}
          </div>
          <div style={{ color: "#475569", marginBottom: "0.25rem" }}>{fixture.purpose}</div>
          <div style={{ fontSize: "0.7rem", color: "#64748b", marginBottom: "0.25rem" }}>
            推荐 technique：
            <span style={{ fontWeight: 600, color: "#7c3aed" }}>
              {fixture.recommendedTechniques.join(" / ")}
            </span>
          </div>
          <div style={{ fontSize: "0.7rem", color: "#64748b" }}>
            测试文案：
            <span style={{ fontStyle: "italic", color: "#334155" }}>
              {fixture.content.length > 80 ? fixture.content.slice(0, 80) + "…" : fixture.content}
            </span>
          </div>
        </div>

        <div style={{ color: "#b91c1c", fontWeight: 600 }}>
          测试内容会影响视觉判断。通用内容适合冒烟测试；专属内容更适合判断某个 technique 是否真正成立。
        </div>
        <div style={{ marginTop: "0.2rem", color: "#64748b", fontSize: "0.72rem" }}>
          当前仍是 lab-only，不进入 Style Sweep，不进入 Style Gallery。
        </div>

        {/* Technique selector for family adaptation mode */}
        {matrixMode === "family_adaptation" && (
          <div style={{ marginTop: "0.75rem", paddingTop: "0.6rem", borderTop: "1px dashed #bfdbfe" }}>
            <div style={{ fontWeight: 600, marginBottom: "0.3rem", color: "#1e40af" }}>
              固定 technique（将被测试的版式）：
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
              {ALL_VISUAL_TECHNIQUES.map((tech) => {
                const active = adaptationTechnique === tech;
                const meta = VISUAL_TECHNIQUE_META[tech];
                return (
                  <button
                    key={tech}
                    onClick={() => onAdaptationTechniqueChange(tech)}
                    disabled={loading}
                    style={{
                      background: active ? "#7c3aed" : "white",
                      color: active ? "white" : "#475569",
                      border: `1px solid ${active ? "#7c3aed" : "#cbd5e1"}`,
                      borderRadius: "6px",
                      padding: "0.2rem 0.6rem",
                      fontSize: "0.72rem",
                      fontWeight: 600,
                      cursor: loading ? "not-allowed" : "pointer",
                    }}
                  >
                    {meta?.name ?? tech}
                  </button>
                );
              })}
            </div>
            <div style={{ marginTop: "0.4rem", fontSize: "0.7rem", color: "#64748b" }}>
              当前固定：<b style={{ color: "#7c3aed" }}>{VISUAL_TECHNIQUE_META[adaptationTechnique]?.name ?? adaptationTechnique}</b>
              {" "}×{" "}
              {FAMILY_ADAPTATION_FAMILIES.map((f) => f.name).join(" / ")}
            </div>
          </div>
        )}

        {/* Mode-specific summary */}
        {matrixMode === "technique_compare" ? (
          <div style={{ marginTop: "0.25rem" }}>
            目的：横向对比 5 个 technique 在同一 family 下的适配度差异。
          </div>
        ) : (
          <div style={{ marginTop: "0.25rem" }}>
            目的：判断同一 technique 在不同 family 版式下的适配度是否成立。
          </div>
        )}
      </div>

      {/* Acceptance summary bar */}
      {result && result.items.length > 0 && (
        <div
          style={{
            marginBottom: "1rem",
            padding: "0.55rem 0.85rem",
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            display: "flex",
            alignItems: "center",
            gap: "0.8rem",
            flexWrap: "wrap",
            fontSize: "0.78rem",
          }}
        >
          <span style={{ fontWeight: 700, color: "#1e293b" }}>视觉验收汇总：</span>
          <span style={{ color: "#15803d" }}>通过 <b>{summary.accepted}</b></span>
          <span style={{ color: "#a16207" }}>部分通过 <b>{summary.partial}</b></span>
          <span style={{ color: "#b91c1c" }}>不通过 <b>{summary.rejected}</b></span>
          <span style={{ color: "#64748b" }}>待验收 <b>{summary.pending}</b></span>
          <span style={{ marginLeft: "auto", fontSize: "0.7rem", color: "#94a3b8" }}>
            当前汇总仅保存在前端页面刷新前，用于本轮人工观察
          </span>
        </div>
      )}

      {/* Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {(result?.items ?? []).map((item) => {
          const hasVideo = item.success && Boolean(item.videoUrl);
          const key = `${item.family}-${item.visualTechnique}`;
          const meta = VISUAL_TECHNIQUE_META[item.visualTechnique];
          const acceptance: LocalVisualAcceptance = localAcceptance[key] ?? "pending";
          const accColor = ACCEPTANCE_COLOR[acceptance];

          return (
            <div
              key={key}
              style={{
                border: `1px solid ${accColor.border}`,
                borderRadius: "10px",
                overflow: "hidden",
                background: "white",
                display: "flex",
                flexDirection: "column",
              }}
            >
              {/* Header: family × technique + Chinese name + source */}
              <div
                style={{
                  background: "linear-gradient(135deg, #d4a57418 0%, #faf7f2 100%)",
                  borderBottom: `1px solid ${accColor.border}`,
                  padding: "0.55rem 0.75rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.2rem" }}>
                  <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#92400e" }}>
                    {item.family}
                  </span>
                  <span style={{ color: "#d4a574", fontSize: "0.65rem" }}>×</span>
                  <span style={{ fontSize: "0.75rem", color: "#b45309", fontFamily: "monospace" }}>
                    {item.visualTechnique}
                  </span>
                </div>
                {meta && (
                  <>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1e293b" }}>
                      {meta.name}
                    </div>
                    <div style={{ fontSize: "0.66rem", color: "#94a3b8" }}>{meta.source}</div>
                  </>
                )}
              </div>

              {/* Video */}
              <div style={{ padding: "0.4rem", background: "#faf7f2" }}>
                {hasVideo ? (
                  <video
                    controls
                    src={resolveUrl(item.videoUrl)}
                    style={{
                      width: "100%",
                      height: "200px",
                      objectFit: "contain",
                      display: "block",
                      borderRadius: "6px",
                      background: "#1e1a14",
                    }}
                  />
                ) : (
                  <div
                    style={{
                      height: "200px",
                      background: "#f5f0e8",
                      borderRadius: "6px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "0.72rem",
                      color: "#b45309",
                      textAlign: "center",
                      padding: "0.5rem",
                    }}
                  >
                    {item.message ? `失败：${item.message}` : "待渲染"}
                  </div>
                )}
              </div>

              {/* Status row */}
              <div
                style={{
                  padding: "0.4rem 0.75rem",
                  borderTop: "1px solid #e2e8f0",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontSize: "0.7rem",
                  flexWrap: "wrap",
                  gap: "0.3rem",
                }}
              >
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <span style={{ color: item.success ? "#16a34a" : "#ef4444", fontWeight: 600 }}>
                    {item.success ? "✓ 生成成功" : "✗ 生成失败"}
                  </span>
                  <span style={{ color: "#94a3b8" }}>·</span>
                  <span style={{ color: "#94a3b8" }}>视觉：待人工验收</span>
                </div>
                <span style={{ color: "#94a3b8" }}>{item.elapsedMs}ms</span>
              </div>

              {/* Description */}
              {meta && (
                <div style={{ padding: "0.5rem 0.75rem 0.3rem", fontSize: "0.72rem", color: "#475569", lineHeight: 1.55 }}>
                  {meta.description}
                </div>
              )}

              {/* Fixture content match */}
              <div style={{ padding: "0.3rem 0.75rem", fontSize: "0.7rem", color: "#64748b" }}>
                <div>
                  当前测试内容：<span style={{ fontWeight: 600, color: "#1e40af" }}>{fixture.name}</span>
                </div>
                <div>
                  内容匹配：
                  {fixture.recommendedTechniques.includes(item.visualTechnique) ? (
                    <span style={{ color: "#15803d", fontWeight: 600 }}>推荐</span>
                  ) : (
                    <span style={{ color: "#b45309", fontWeight: 600 }}>非推荐，仅作横向对比</span>
                  )}
                </div>
              </div>

              {/* Family adaptation mode: show family description */}
              {matrixMode === "family_adaptation" && (
                <div
                  style={{
                    padding: "0.3rem 0.75rem",
                    fontSize: "0.7rem",
                    color: "#475569",
                    background: "#fef9f0",
                    borderTop: "1px dashed #fed7aa",
                    borderBottom: "1px dashed #fed7aa",
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#92400e", marginBottom: "0.2rem" }}>
                    Family 说明：
                  </div>
                  {FAMILY_ADAPTATION_FAMILIES.filter((f) => f.id === item.family).map((f) => (
                    <div key={f.id}>
                      <b>{f.name}</b>：{f.desc}
                    </div>
                  ))}
                  <div style={{ marginTop: "0.3rem", color: "#b45309", fontSize: "0.68rem" }}>
                    观察：该 technique 在当前 family 下是否仍然成立，是否只是背景换皮？
                  </div>
                </div>
              )}

              {/* Suitable For chips */}
              {meta && meta.suitableFor.length > 0 && (
                <div style={{ padding: "0.25rem 0.75rem", display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                  {meta.suitableFor.map((s) => (
                    <span
                      key={s}
                      style={{
                        fontSize: "0.62rem",
                        background: "#e0e7ff",
                        color: "#3730a3",
                        borderRadius: 999,
                        padding: "0.1rem 0.5rem",
                      }}
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}

              {/* Observe points */}
              {meta && meta.observePoints.length > 0 && (
                <div
                  style={{
                    padding: "0.4rem 0.75rem 0.5rem",
                    fontSize: "0.7rem",
                    color: "#475569",
                    lineHeight: 1.5,
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#92400e", marginBottom: "0.2rem" }}>观察点：</div>
                  <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
                    {meta.observePoints.map((p) => (
                      <li key={p}>{p}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Acceptance buttons */}
              <div
                style={{
                  padding: "0.5rem 0.75rem",
                  borderTop: "1px solid #e2e8f0",
                  background: "#fafafa",
                }}
              >
                <div
                  style={{
                    fontSize: "0.7rem",
                    color: "#475569",
                    marginBottom: "0.3rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  <span style={{ fontWeight: 600 }}>本地人工验收：</span>
                  <span
                    style={{
                      background: accColor.bg,
                      color: accColor.fg,
                      border: `1px solid ${accColor.border}`,
                      borderRadius: 999,
                      padding: "0.05rem 0.5rem",
                      fontWeight: 600,
                    }}
                  >
                    {ACCEPTANCE_LABEL[acceptance]}
                  </span>
                </div>
                <div style={{ display: "flex", gap: "0.4rem" }}>
                  {(["accepted", "partial", "rejected"] as LocalVisualAcceptance[]).map((v) => {
                    const c = ACCEPTANCE_COLOR[v];
                    const active = acceptance === v;
                    return (
                      <button
                        key={v}
                        onClick={() => setAcceptance(key, v)}
                        style={{
                          flex: 1,
                          background: active ? c.bg : "white",
                          color: active ? c.fg : "#475569",
                          border: `1px solid ${active ? c.border : "#cbd5e1"}`,
                          borderRadius: "6px",
                          padding: "0.3rem 0.4rem",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        {ACCEPTANCE_LABEL[v]}
                      </button>
                    );
                  })}
                </div>
                <div style={{ fontSize: "0.62rem", color: "#94a3b8", marginTop: "0.3rem" }}>
                  本地状态：仅当前页面刷新前有效，不写后端，不进入 Style Gallery
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Acceptance summary footer */}
      {result && result.items.length > 0 && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.7rem 1rem",
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            fontSize: "0.78rem",
            color: "#475569",
            lineHeight: 1.6,
          }}
        >
          <div style={{ fontWeight: 600, color: "#1e293b", marginBottom: "0.3rem" }}>
            本轮视觉验收汇总
            {matrixMode === "technique_compare" ? "（Technique 横向比较）" : "（Family 适配测试）"}：
          </div>
          <div>
            通过 <b style={{ color: "#15803d" }}>{summary.accepted}</b> ·
            部分通过 <b style={{ color: "#a16207" }}>{summary.partial}</b> ·
            不通过 <b style={{ color: "#b91c1c" }}>{summary.rejected}</b> ·
            待验收 <b style={{ color: "#64748b" }}>{summary.pending}</b>
            <span style={{ color: "#94a3b8" }}> / 共 {totalCount} 个</span>
          </div>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginTop: "0.2rem" }}>
            当前汇总仅保存在前端页面刷新前，用于本轮人工观察。生成成功不等于视觉通过。
          </div>
        </div>
      )}

      {/* Extension path */}
      <div
        style={{
          marginTop: "1rem",
          padding: "0.7rem 1rem",
          background: "#faf7f2",
          borderRadius: "8px",
          fontSize: "0.78rem",
          color: "#475569",
          lineHeight: 1.6,
        }}
      >
        <div style={{ fontWeight: 600, color: "#92400e", marginBottom: "0.3rem" }}>扩展路径：</div>
        <ol style={{ margin: 0, paddingLeft: "1.3rem" }}>
          <li>2s 冒烟预览：验证是否能生成和形成差异（当前）</li>
          <li>6~8s 视觉预览：验证动效、可读性和节奏（未来）</li>
          <li>单 technique × 多 family：验证适配不同版式（未来）</li>
          <li>完整 Recipe 样片：进入后续 Style Sweep / Style Gallery 候选（未来）</li>
        </ol>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function RemotionStyleFamilyPage() {
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [compareError, setCompareError] = useState("");

  // V1.2.3: Background Variant Matrix state
  const [matrixLoading, setMatrixLoading] = useState(false);
  const [matrixResult, setMatrixResult] = useState<MatrixResponse | null>(null);
  const [matrixError, setMatrixError] = useState("");
  const [transitionMatrixLoading, setTransitionMatrixLoading] = useState(false);
  const [transitionMatrixResult, setTransitionMatrixResult] = useState<TransitionMatrixResponse | null>(null);
  const [transitionMatrixError, setTransitionMatrixError] = useState("");
  // V1.2.4: Visual Style Preset Matrix state
  const [visualStyleMatrixLoading, setVisualStyleMatrixLoading] = useState(false);
  const [visualStyleMatrixResult, setVisualStyleMatrixResult] = useState<VisualStyleMatrixResponse | null>(null);
  const [visualStyleMatrixError, setVisualStyleMatrixError] = useState("");
  // V1.2.4: Visual Technique Matrix state
  const [visualTechniqueMatrixLoading, setVisualTechniqueMatrixLoading] = useState(false);
  const [visualTechniqueMatrixResult, setVisualTechniqueMatrixResult] = useState<VisualTechniqueMatrixResponse | null>(null);
  const [visualTechniqueMatrixError, setVisualTechniqueMatrixError] = useState("");
  // V1.2.5+: Visual Technique clip length selector (default 2s = smoke preview)
  const [visualTechniqueClipSeconds, setVisualTechniqueClipSeconds] = useState(2);
  // V1.2.6+: Visual Technique fixture selector (default = generic_ai_eval)
  const [visualTechniqueFixtureId, setVisualTechniqueFixtureId] = useState<VisualTechniqueFixtureId>("generic_ai_eval");
  // V1.2.7+: Visual Technique Matrix mode (technique_compare = default, family_adaptation = new)
  const [visualTechniqueMatrixMode, setVisualTechniqueMatrixMode] = useState<"technique_compare" | "family_adaptation">("technique_compare");
  // V1.2.7+: Selected technique for family adaptation mode (default = academic_sketch)
  const [familyAdaptationTechnique, setFamilyAdaptationTechnique] = useState<VisualTechniqueId>("academic_sketch");

  const runCompare = async () => {
    setCompareLoading(true);
    setCompareError("");
    setCompareResult(null);
    try {
      const resp = await fetch(`${API_BASE}/style-family/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setCompareResult(data);
    } catch (e) {
      setCompareError(String(e));
    } finally {
      setCompareLoading(false);
    }
  };

  // V1.2.3: Background Variant Matrix
  const runMatrix = async () => {
    setMatrixLoading(true);
    setMatrixError("");
    setMatrixResult(null);
    try {
      const resp = await fetch(`${API_BASE}/style-family/background-matrix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: "",
          params: { clipSeconds: 3, keyPointCount: 3 },
          matrix: {
            families: MATRIX_FAMILIES.map((family) => family.id),
            backgroundPresets: MATRIX_BACKGROUNDS.map((background) => background.id),
          },
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setMatrixResult(data);
    } catch (e) {
      setMatrixError(String(e));
    } finally {
      setMatrixLoading(false);
    }
  };

  const runTransitionMatrix = async () => {
    setTransitionMatrixLoading(true);
    setTransitionMatrixError("");
    setTransitionMatrixResult(null);
    try {
      const resp = await fetch(`${API_BASE}/style-family/transition-matrix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: "",
          params: {
            clipSeconds: 3,
            keyPointCount: 3,
            backgroundPreset: "tech_grid_dark",
          },
          matrix: {
            families: DEFAULT_TRANSITION_FAMILY.map((family) => family.id),
            transitionStyles: DEFAULT_TRANSITION_STYLES.map((transition) => transition.id),
          },
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setTransitionMatrixResult(data);
    } catch (e) {
      setTransitionMatrixError(String(e));
    } finally {
      setTransitionMatrixLoading(false);
    }
  };

  // V1.2.4: Visual Style Preset Matrix
  const runVisualStyleMatrix = async () => {
    setVisualStyleMatrixLoading(true);
    setVisualStyleMatrixError("");
    setVisualStyleMatrixResult(null);
    try {
      const resp = await fetch(`${API_BASE}/style-family/visual-style-matrix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: "OpenAI 发布新一代多模态模型，重点提升语音、图像和视频理解能力。",
          params: { clipSeconds: 2, keyPointCount: 2 },
          matrix: {
            families: VISUAL_STYLE_MATRIX_FAMILIES.map((f) => f.id),
            visualStylePresets: VISUAL_STYLE_PRESETS.map((p) => p.id),
          },
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setVisualStyleMatrixResult(data);
    } catch (e) {
      setVisualStyleMatrixError(String(e));
    } finally {
      setVisualStyleMatrixLoading(false);
    }
  };

  // V1.2.4: Visual Technique Matrix
  const runVisualTechniqueMatrix = async () => {
    setVisualTechniqueMatrixLoading(true);
    setVisualTechniqueMatrixError("");
    setVisualTechniqueMatrixResult(null);
    try {
      const fixture = VISUAL_TECHNIQUE_FIXTURES[visualTechniqueFixtureId];
      const matrix =
        visualTechniqueMatrixMode === "technique_compare"
          ? {
              families: ["data_news"],
              visualTechniques: [
                "academic_sketch",
                "blueprint",
                "data_viz_dashboard",
                "agent_sandbox_25d",
                "kinetic_code_typography",
              ],
            }
          : {
              families: FAMILY_ADAPTATION_FAMILIES.map((f) => f.id),
              visualTechniques: [familyAdaptationTechnique],
            };
      const resp = await fetch(`${API_BASE}/style-family/visual-technique-matrix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: fixture.content,
          params: {
            clipSeconds: visualTechniqueClipSeconds,
            keyPointCount: 2,
            visualStylePreset: "warm_paper",
            backgroundPreset: "warm_cinematic",
            transitionStyle: "slide_fade",
          },
          matrix,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? `${resp.status}`);
      setVisualTechniqueMatrixResult(data);
    } catch (e) {
      setVisualTechniqueMatrixError(String(e));
    } finally {
      setVisualTechniqueMatrixLoading(false);
    }
  };

  const resolveUrl = (u: string) =>
    u && u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u || "";

  const compareItems = compareResult ? [
    { key: "dataNews", name: "Data News", color: "#7c3aed", note: "数字指标 / 新闻卡片", result: compareResult.dataNews },
    { key: "cardStack", name: "Card Stack", color: "#2563eb", note: "卡片堆叠 / 信息流", result: compareResult.cardStack },
    { key: "timelineNews", name: "Timeline", color: "#0891b2", note: "事件演进 / 时间线", result: compareResult.timelineNews },
    { key: "dashboardBrief", name: "Dashboard", color: "#f59e0b", note: "指标看板 / 排行", result: compareResult.dashboardBrief },
    { key: "captionStory", name: "Caption Story", color: "#ec4899", note: "大字旁白 / 叙事", result: compareResult.captionStory },
  ].filter((item): item is {
    key: string;
    name: string;
    color: string;
    note: string;
    result: CompareResult;
  } => Boolean(item.result)) : [];

  return (
    <div style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          Remotion 表现范式研究台 · V0.8.8
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.95rem" }}>
          将 Remotion 从单一路线升级为可编程视频表现系统 — 本页是"设计方向研究"，批量生成验证请去 Style Sweep，沉淀样片请去 Style Gallery。
        </p>
      </div>

      <CapabilitySummaryPanel />

      <ModuleOptimizationPanel />

      {/* V0.8.8: 主流程入口 */}
      <div
        data-testid="remotion-family-top-entries"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem",
          marginBottom: "2.5rem",
        }}
      >
        <Link
          to="/video-lab/style-sweep"
          style={{
            background: "#8b5cf6",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
            fontWeight: 600,
          }}
        >
          进入 Style Sweep
        </Link>
        <Link
          to={REMOTION_GALLERY_BASE}
          style={{
            background: "#10b981",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
            fontWeight: 600,
          }}
        >
          进入 Style Gallery
        </Link>
        <Link
          to="/video-lab"
          style={{
            background: "#64748b",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
            fontWeight: 600,
          }}
        >
          返回 Video Lab
        </Link>
        <div
          style={{
            marginLeft: "auto",
            fontSize: "0.8rem",
            color: "#94a3b8",
            alignSelf: "center",
          }}
        >
          Style Family = 设计方向研究 · Style Sweep = 批量生成验证 · Style Gallery = 沉淀样片
        </div>
      </div>

      {/* Section 1: Family Cards */}
      <div id="style-family-overview" style={{ marginBottom: "3rem" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          范式总览
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "1.25rem",
          }}
        >
          {FAMILIES.map((f) => (
            <FamilyCard key={f.id} family={f} />
          ))}
        </div>
      </div>

      {/* V0.8.8: 当前实现覆盖度（避免用户误以为 family 都已可生成） */}
      <CoveragePanel />

      {/* V0.8.8: 下一步最小实验推荐 */}
      <NextExperimentPanel />

      {/* V0.8.8: 参考样例 → 可落地范式 映射表 */}
      <ReferenceMappingPanel />

      <StyleDimensionsPanel />

      <ExpandedStyleSamplesPanel />

      {/* Section 2: Comparison Matrix */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "16px",
          padding: "1.25rem",
          marginBottom: "2.5rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          范式对比矩阵
        </h2>
        <ComparisonTable />
        <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.5rem", textAlign: "right" }}>
          注：★ 越高越强
        </div>
      </div>

      {/* Section 3: Priority Roadmap */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "16px",
          padding: "1.25rem",
          marginBottom: "2.5rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          推荐推进顺序
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          {PRIORITY_ROADMAP.map((item) => (
            <div
              key={item.step}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "0.85rem",
              }}
            >
              <div
                style={{
                  background: "#7c3aed",
                  color: "white",
                  borderRadius: "999px",
                  width: "28px",
                  height: "28px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  flexShrink: 0,
                }}
              >
                {item.step}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginBottom: "0.3rem" }}>
                  {item.families.map((fid) => {
                    const fam = FAMILIES.find((f) => f.id === fid);
                    return (
                      <span
                        key={fid}
                        style={{
                          background: `${fam?.accentColor}15`,
                          color: fam?.accentColor,
                          border: `1px solid ${fam?.accentColor}35`,
                          borderRadius: "6px",
                          padding: "0.1rem 0.5rem",
                          fontSize: "0.82rem",
                          fontWeight: 600,
                        }}
                      >
                        {fam?.name ?? fid}
                      </span>
                    );
                  })}
                </div>
                <div style={{ fontSize: "0.82rem", color: "#64748b", lineHeight: 1.5 }}>
                  {item.reason}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary reasoning */}
        <div
          style={{
            marginTop: "1.25rem",
            paddingTop: "1rem",
            borderTop: "1px solid #e2e8f0",
            fontSize: "0.85rem",
            color: "#64748b",
            lineHeight: 1.6,
          }}
        >
          <strong style={{ color: "#475569" }}>理由：</strong>
          Data News 与当前 AI 新闻场景最贴近；Card Stack 最像短视频信息流；
          Timeline 适合解释复杂事件；Dashboard 容易过度复杂；
          Subtitle Story 更适合另一个文案/情绪视频产品线。
        </div>
      </div>

      {/* Section 4: Min Sample */}
      <div
        style={{
          background: "linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)",
          borderRadius: "16px",
          padding: "1.25rem 1.5rem",
          color: "white",
          marginBottom: "2.5rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1rem" }}>
          本轮最小验证
        </h2>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
          <span style={{ fontSize: "1.5rem" }}>🗂️</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1rem" }}>{MIN_SAMPLE.family}</div>
            <div style={{ fontSize: "0.82rem", opacity: 0.8 }}>Remotion Card Stack 最小样片</div>
          </div>
        </div>

        <div style={{ fontSize: "0.85rem", lineHeight: 1.6, marginBottom: "0.75rem", opacity: 0.9 }}>
          <div style={{ fontWeight: 600, marginBottom: "0.3rem", opacity: 1 }}>选择理由：</div>
          {MIN_SAMPLE.reason.split("\n").map((line, i) => (
            <div key={i} style={{ paddingLeft: "0.5rem" }}>
              {line}
            </div>
          ))}
        </div>

        <div
          style={{
            background: "rgba(255,255,255,0.15)",
            borderRadius: "8px",
            padding: "0.6rem 0.85rem",
            fontSize: "0.82rem",
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: "0.2rem" }}>状态：{MIN_SAMPLE.status}</div>
          {MIN_SAMPLE.detail?.split("\n").map((line, i) => (
            <div key={i} style={{ paddingLeft: "0.5rem" }}>{line}</div>
          ))}
        </div>
      </div>

      {/* Section 5: Actual Preview Comparison - V0.6.4 */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "16px",
          padding: "1.25rem",
          marginBottom: "2.5rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.5rem", color: "#1e293b" }}>
          实际预览对比 · V0.6.5.2
        </h2>
        <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "1rem" }}>
          点击「生成对比预览」同时渲染 Data News 和 Card Stack 两种范式的实际效果。Card Stack V0.6.5.2 已进一步强化 prev/next 图层可见性（更大偏移、更强透明度、蓝色/青色边框标识），验证期加入 PREV/NEXT 角标，可在右侧视频中清晰看到三层卡片堆叠。
        </p>

        {/* Generate Button */}
        <button
          onClick={runCompare}
          disabled={compareLoading}
          style={{
            background: compareLoading ? "#94a3b8" : "#7c3aed",
            color: "white",
            border: "none",
            borderRadius: "8px",
            padding: "0.65rem 1.25rem",
            fontSize: "0.9rem",
            fontWeight: 600,
            cursor: compareLoading ? "wait" : "pointer",
            marginBottom: "1.25rem",
          }}
        >
          {compareLoading ? "渲染中（约 20-40 秒）..." : "生成对比预览"}
        </button>

        {compareError && (
          <div style={{ color: "#ef4444", fontSize: "0.82rem", marginBottom: "1rem", padding: "0.75rem", background: "#fef2f2", borderRadius: "8px" }}>
            错误：{compareError}
          </div>
        )}

        {/* Results */}
        {compareResult && (
          <>
            {/* Stats bar */}
            <div style={{ display: "flex", gap: "1rem", marginBottom: "1.25rem", fontSize: "0.78rem", color: "#64748b" }}>
              <span>总耗时：{compareResult.totalElapsedMs}ms</span>
              <span style={{ color: compareResult.dataNews.success ? "#16a34a" : "#ef4444" }}>
                Data News：{compareResult.dataNews.success ? "成功" : "失败"}
              </span>
              <span style={{ color: compareResult.cardStack.success ? "#16a34a" : "#ef4444" }}>
                Card Stack：{compareResult.cardStack.success ? "成功" : "失败"}
              </span>
            </div>

            {/* Video comparison grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
              {/* Data News */}
              <div style={{ border: "1px solid #e2e8f0", borderRadius: "12px", overflow: "hidden" }}>
                <div style={{ background: "linear-gradient(135deg, #7c3aed18 0%, #7c3aed08 100%)", padding: "0.75rem 1rem", borderBottom: "1px solid #e2e8f0" }}>
                  <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "#7c3aed" }}>📊 Data News</div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>单一居中卡片，数字滚动动画</div>
                </div>
                <div style={{ padding: "1rem" }}>
                  {compareResult.dataNews.success && compareResult.dataNews.videoUrl ? (
                    <>
                      <video
                        controls
                        src={resolveUrl(compareResult.dataNews.videoUrl)}
                        style={{ width: "100%", borderRadius: "8px", background: "#0f172a" }}
                      />
                      <div style={{ marginTop: "0.5rem", fontSize: "0.72rem", color: "#64748b" }}>
                        {compareResult.dataNews.clipSeconds}s · {compareResult.dataNews.elapsedMs}ms
                      </div>
                    </>
                  ) : (
                    <div style={{ color: "#ef4444", fontSize: "0.82rem", padding: "1rem", textAlign: "center" }}>
                      渲染失败：{compareResult.dataNews.message}
                    </div>
                  )}
                  <div style={{ marginTop: "0.5rem", fontSize: "0.7rem", color: "#94a3b8", wordBreak: "break-all" }}>
                    ID：{compareResult.dataNews.experimentId || "—"}
                  </div>
                </div>
              </div>

              {/* Card Stack */}
              <div style={{ border: "1px solid #e2e8f0", borderRadius: "12px", overflow: "hidden" }}>
                <div style={{ background: "linear-gradient(135deg, #2563eb18 0%, #2563eb08 100%)", padding: "0.75rem 1rem", borderBottom: "1px solid #e2e8f0" }}>
                  <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "#2563eb" }}>🗂️ Card Stack</div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>V0.6.5.2 强化：prev/next 更大偏移 + 边框标识 + PREV/NEXT 角标</div>
                </div>
                <div style={{ padding: "1rem" }}>
                  {compareResult.cardStack.success && compareResult.cardStack.videoUrl ? (
                    <>
                      <video
                        controls
                        src={resolveUrl(compareResult.cardStack.videoUrl)}
                        style={{ width: "100%", borderRadius: "8px", background: "#0f172a" }}
                      />
                      <div style={{ marginTop: "0.5rem", fontSize: "0.72rem", color: "#64748b" }}>
                        {compareResult.cardStack.clipSeconds}s · {compareResult.cardStack.elapsedMs}ms
                      </div>
                    </>
                  ) : (
                    <div style={{ color: "#ef4444", fontSize: "0.82rem", padding: "1rem", textAlign: "center" }}>
                      渲染失败：{compareResult.cardStack.message}
                    </div>
                  )}
                  <div style={{ marginTop: "0.5rem", fontSize: "0.7rem", color: "#94a3b8", wordBreak: "break-all" }}>
                    ID：{compareResult.cardStack.experimentId || "—"}
                  </div>
                </div>
              </div>
            </div>

            {compareItems.length > 2 && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1.25rem", marginTop: "1.25rem" }}>
                {compareItems.slice(2).map((item) => (
                  <div key={item.key} style={{ border: "1px solid #e2e8f0", borderRadius: "12px", overflow: "hidden" }}>
                    <div style={{ background: `linear-gradient(135deg, ${item.color}18 0%, ${item.color}08 100%)`, padding: "0.75rem 1rem", borderBottom: "1px solid #e2e8f0" }}>
                      <div style={{ fontWeight: 700, fontSize: "0.9rem", color: item.color }}>{item.name}</div>
                      <div style={{ fontSize: "0.72rem", color: "#64748b" }}>{item.note}</div>
                    </div>
                    <div style={{ padding: "1rem" }}>
                      {item.result.success && item.result.videoUrl ? (
                        <>
                          <video
                            controls
                            src={resolveUrl(item.result.videoUrl)}
                            style={{ width: "100%", borderRadius: "8px", background: "#0f172a" }}
                          />
                          <div style={{ marginTop: "0.5rem", fontSize: "0.72rem", color: "#64748b" }}>
                            {item.result.clipSeconds}s · {item.result.elapsedMs}ms
                          </div>
                        </>
                      ) : (
                        <div style={{ color: "#ef4444", fontSize: "0.82rem", padding: "1rem", textAlign: "center" }}>
                          渲染失败：{item.result.message}
                        </div>
                      )}
                      <div style={{ marginTop: "0.5rem", fontSize: "0.7rem", color: "#94a3b8", wordBreak: "break-all" }}>
                        ID：{item.result.experimentId || "—"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Comparison summary */}
            <div
              style={{
                marginTop: "1.25rem",
                padding: "1rem",
                background: "#f8fafc",
                borderRadius: "8px",
                fontSize: "0.82rem",
                color: "#475569",
                lineHeight: 1.6,
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: "0.4rem", color: "#1e293b" }}>视觉差异结论：</div>
              <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
                <li>Data News：单一居中卡片，数字滚动动画和数据条更突出，适合需要强调数据的场景。</li>
                <li>Card Stack V0.6.5.2：主卡（z=2）居中，前一张（z=1）在右上角露出（蓝色边框+PREV角标），后一张（z=0）在左下角预览（青色边框+NEXT角标），形成明确的三层卡片堆叠。</li>
                <li>强化效果：prev offsetX=220/offsetY=-130，next offsetX=-220/offsetY=110；prev opacity=0.75，next opacity=0.60；prev 蓝色边框+PREV角标，next 青色边框+NEXT角标。</li>
                <li>当前判断：V0.6.5.2 通过边框标识和更大偏移，使 prev/next 层在抽帧和播放中均可辨识。</li>
              </ul>
            </div>
          </>
        )}

        {!compareResult && !compareLoading && !compareError && (
          <div style={{ textAlign: "center", padding: "2rem", color: "#94a3b8", fontSize: "0.85rem" }}>
            点击上方按钮开始渲染对比
          </div>
        )}
      </div>

      <PromotedStylePresets />

      {/* V1.2.3: Background Variant Matrix */}
      <div id="background-matrix">
        <BackgroundVariantMatrix
          result={matrixResult}
          onReload={runMatrix}
          loading={matrixLoading}
        />
      </div>

      {matrixError && (
        <div style={{ color: "#ef4444", fontSize: "0.82rem", marginBottom: "1rem", padding: "0.75rem", background: "#fef2f2", borderRadius: "8px" }}>
          错误：{matrixError}
        </div>
      )}

      <div id="transition-matrix">
        <TransitionVariantMatrix
          result={transitionMatrixResult}
          onReload={runTransitionMatrix}
          loading={transitionMatrixLoading}
        />
      </div>

      {transitionMatrixError && (
        <div style={{ color: "#ef4444", fontSize: "0.82rem", marginBottom: "1rem", padding: "0.75rem", background: "#fef2f2", borderRadius: "8px" }}>
          错误：{transitionMatrixError}
        </div>
      )}

      {/* V1.2.4: Visual Style Preset Matrix */}
      <div id="visual-style-matrix">
        <VisualStyleVariantMatrix
          result={visualStyleMatrixResult}
          onReload={runVisualStyleMatrix}
          loading={visualStyleMatrixLoading}
        />
      </div>

      {visualStyleMatrixError && (
        <div style={{ color: "#ef4444", fontSize: "0.82rem", marginBottom: "1rem", padding: "0.75rem", background: "#fef2f2", borderRadius: "8px" }}>
          错误：{visualStyleMatrixError}
        </div>
      )}

      {/* V1.2.4: Visual Technique Matrix */}
      <div id="visual-technique-matrix">
        <VisualTechniqueVariantMatrix
          result={visualTechniqueMatrixResult}
          onReload={runVisualTechniqueMatrix}
          loading={visualTechniqueMatrixLoading}
          clipSeconds={visualTechniqueClipSeconds}
          onClipSecondsChange={setVisualTechniqueClipSeconds}
          fixtureId={visualTechniqueFixtureId}
          onFixtureIdChange={setVisualTechniqueFixtureId}
          matrixMode={visualTechniqueMatrixMode}
          onMatrixModeChange={setVisualTechniqueMatrixMode}
          adaptationTechnique={familyAdaptationTechnique}
          onAdaptationTechniqueChange={setFamilyAdaptationTechnique}
        />
      </div>

      {visualTechniqueMatrixError && (
        <div style={{ color: "#ef4444", fontSize: "0.82rem", marginBottom: "1rem", padding: "0.75rem", background: "#fef2f2", borderRadius: "8px" }}>
          错误：{visualTechniqueMatrixError}
        </div>
      )}

      {/* Back link */}
      <div style={{ textAlign: "center" }}>
        <Link
          to="/video-lab"
          style={{
            color: "#64748b",
            textDecoration: "none",
            fontSize: "0.85rem",
          }}
        >
          ← 返回 Video Lab 首页
        </Link>
      </div>
    </div>
  );
}
