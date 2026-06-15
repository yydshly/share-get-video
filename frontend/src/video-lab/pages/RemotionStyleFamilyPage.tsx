// Remotion Style Family Page - V0.6.1
// Remotion 多表现范式探索页面

import { Link } from "react-router-dom";

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
    currentStatus: "V0.6.2 已验证 — CardStackLayer 已实现，支持 remotionFamily 参数",
    priority: "P1",
    priorityReason: "短视频感最强，适合 AI 新闻信息流方向",
    accentColor: "#2563eb",
    icon: "🗂️",
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
    currentStatus: "待探索 — 需要 Timeline 专用组件",
    priority: "P1",
    priorityReason: "适合解释复杂事件，与 Data News 正交",
    accentColor: "#0891b2",
    icon: "📅",
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
    currentStatus: "待探索 — 复杂度较高，需谨慎投入",
    priority: "P2",
    priorityReason: "信息密度高但复杂度也高，容易过度设计",
    accentColor: "#f59e0b",
    icon: "🖥️",
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
    currentStatus: "待探索 — 更适合另一个文案/情绪视频产品线",
    priority: "P2",
    priorityReason: "更偏向情绪内容，与当前 AI 新闻定位差异较大",
    accentColor: "#ec4899",
    icon: "💬",
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
  status: "V0.6.3 已完成实际样片验证",
  experimentId: "clip_4f6e00b7",
  detail: "remotionFamily=card_stack 时，主卡后层叠加一张 prev 卡片（右下角露出），形成堆叠视觉效果。\n实际渲染验证：secondary card layer 确实出现在主卡右下角，与 Data News 有可见差异。",
};

// ─── Component ───────────────────────────────────────────────────────────────

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
  return (
    <div style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "2.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          Remotion 表现范式 · V0.6.1
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.95rem" }}>
          将 Remotion 从单一路线升级为可编程视频表现系统
        </p>
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
