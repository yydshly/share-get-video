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

// ─── Page ────────────────────────────────────────────────────────────────────

export default function RemotionStyleFamilyPage() {
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [compareError, setCompareError] = useState("");

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
      <div style={{ marginBottom: "3rem" }}>
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
