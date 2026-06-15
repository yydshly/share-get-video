// Route Baseline Comparison Page - V0.6.0
// 三路线 Pillow / Remotion / AI素材 baseline 结果对比面板

import { Link } from "react-router-dom";

// ─── Route Card ───────────────────────────────────────────────────────────────

interface RouteCardProps {
  routeKey: string;
  routeName: string;
  displayName: string;
  tagline: string;
  status: string;
  experimentId: string;
  duration: string;
  strengths: string[];
  weaknesses: string[];
  suitable: string[];
  recommendation: string;
  accentColor: string;
  icon: string;
}

function RouteCard({
  routeKey,
  routeName,
  displayName,
  tagline,
  status,
  experimentId,
  duration,
  strengths,
  weaknesses,
  suitable,
  recommendation,
  accentColor,
  icon,
}: RouteCardProps) {
  return (
    <div
      style={{
        background: "white",
        border: `1px solid #e2e8f0`,
        borderRadius: "16px",
        overflow: "hidden",
        boxShadow: `0 2px 8px ${accentColor}15`,
      }}
    >
      {/* Card Header */}
      <div
        style={{
          background: `linear-gradient(135deg, ${accentColor}18 0%, ${accentColor}08 100%)`,
          borderBottom: `1px solid ${accentColor}30`,
          padding: "1.25rem 1.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "1.75rem" }}>{icon}</span>
          <div>
            <div style={{ fontSize: "0.75rem", color: "#64748b", fontFamily: "monospace" }}>
              {routeKey}
            </div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b" }}>
              {displayName}
            </div>
          </div>
        </div>
        <div style={{ fontSize: "0.9rem", color: "#475569", fontStyle: "italic" }}>
          {tagline}
        </div>
      </div>

      {/* Card Body */}
      <div style={{ padding: "1.25rem 1.5rem" }}>
        {/* Status & Meta */}
        <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem", flexWrap: "wrap" }}>
          <span
            style={{
              background: "#f0fdf4",
              color: "#16a34a",
              border: "1px solid #bbf7d0",
              borderRadius: "999px",
              padding: "0.2rem 0.65rem",
              fontSize: "0.78rem",
              fontWeight: 500,
            }}
          >
            {status}
          </span>
          <span
            style={{
              background: "#eff6ff",
              color: "#2563eb",
              border: "1px solid #bfdbfe",
              borderRadius: "999px",
              padding: "0.2rem 0.65rem",
              fontSize: "0.78rem",
              fontWeight: 500,
            }}
          >
            ⏱ {duration}
          </span>
        </div>

        <div style={{ fontSize: "0.78rem", color: "#94a3b8", marginBottom: "1rem", fontFamily: "monospace" }}>
          实验ID: {experimentId}
        </div>

        {/* Strengths */}
        <div style={{ marginBottom: "0.85rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#16a34a", marginBottom: "0.35rem" }}>
            ✓ 优势
          </div>
          {strengths.map((s) => (
            <div key={s} style={{ fontSize: "0.85rem", color: "#475569", lineHeight: 1.5, paddingLeft: "0.5rem" }}>
              · {s}
            </div>
          ))}
        </div>

        {/* Weaknesses */}
        <div style={{ marginBottom: "0.85rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#dc2626", marginBottom: "0.35rem" }}>
            ✗ 问题
          </div>
          {weaknesses.map((w) => (
            <div key={w} style={{ fontSize: "0.85rem", color: "#475569", lineHeight: 1.5, paddingLeft: "0.5rem" }}>
              · {w}
            </div>
          ))}
        </div>

        {/* Suitable */}
        <div style={{ marginBottom: "1rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#7c3aed", marginBottom: "0.35rem" }}>
            ◆ 适合场景
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
            {suitable.map((s) => (
              <span
                key={s}
                style={{
                  background: "#f5f3ff",
                  color: "#6d28d9",
                  border: "1px solid #ddd6fe",
                  borderRadius: "6px",
                  padding: "0.15rem 0.5rem",
                  fontSize: "0.78rem",
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </div>

        {/* Recommendation Badge */}
        <div
          style={{
            background: `${accentColor}12`,
            border: `1px solid ${accentColor}35`,
            borderRadius: "8px",
            padding: "0.6rem 0.85rem",
            fontSize: "0.85rem",
            fontWeight: 600,
            color: accentColor,
            textAlign: "center",
          }}
        >
          {recommendation}
        </div>
      </div>
    </div>
  );
}

// ─── Scoring Matrix ───────────────────────────────────────────────────────────

const SCORE_STAR = (filled: number, total = 5) => {
  return Array.from({ length: total }, (_, i) => (
    <span key={i} style={{ color: i < filled ? "#f59e0b" : "#e2e8f0", fontSize: "0.9rem" }}>
      ★
    </span>
  ));
};

interface ScoreRow {
  dimension: string;
  pillow: number;
  remotion: number;
  aiAsset: number;
  note?: string;
}

const SCORE_MATRIX: ScoreRow[] = [
  { dimension: "可读性", pillow: 5, remotion: 4, aiAsset: 4 },
  { dimension: "成片感", pillow: 2, remotion: 5, aiAsset: 4 },
  { dimension: "视觉氛围", pillow: 2, remotion: 4, aiAsset: 5 },
  { dimension: "信息密度", pillow: 4, remotion: 4, aiAsset: 4 },
  { dimension: "字幕干扰", pillow: 5, remotion: 4, aiAsset: 5 },
  { dimension: "生成速度", pillow: 5, remotion: 2, aiAsset: 3 },
  { dimension: "稳定性", pillow: 5, remotion: 3, aiAsset: 3 },
  { dimension: "成本风险", pillow: 5, remotion: 3, aiAsset: 2 },
];

const SUITABLE_ROW = { dimension: "适合场景", pillow: "日常快讯", remotion: "精品动效", aiAsset: "视觉增强" };
const RECOMMEND_ROW = { dimension: "默认推荐", pillow: "批量默认", remotion: "精品默认", aiAsset: "可选增强" };

function ScoringMatrix() {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
        <thead>
          <tr style={{ background: "#f8fafc" }}>
            <th style={thStyle}>维度</th>
            <th style={{ ...thStyle, color: "#0891b2" }}>Pillow</th>
            <th style={{ ...thStyle, color: "#7c3aed" }}>Remotion</th>
            <th style={{ ...thStyle, color: "#059669" }}>AI素材</th>
          </tr>
        </thead>
        <tbody>
          {SCORE_MATRIX.map((row) => (
            <tr key={row.dimension} style={{ borderBottom: "1px solid #f1f5f9" }}>
              <td style={tdLabelStyle}>{row.dimension}</td>
              <td style={tdCenterStyle}>{SCORE_STAR(row.pillow)}</td>
              <td style={tdCenterStyle}>{SCORE_STAR(row.remotion)}</td>
              <td style={tdCenterStyle}>{SCORE_STAR(row.aiAsset)}</td>
            </tr>
          ))}
          <tr style={{ borderBottom: "1px solid #e2e8f0", background: "#f8fafc" }}>
            <td style={{ ...tdLabelStyle, fontWeight: 600 }}>{SUITABLE_ROW.dimension}</td>
            <td style={{ ...tdCenterStyle, color: "#0891b2", fontWeight: 500 }}>{SUITABLE_ROW.pillow}</td>
            <td style={{ ...tdCenterStyle, color: "#7c3aed", fontWeight: 500 }}>{SUITABLE_ROW.remotion}</td>
            <td style={{ ...tdCenterStyle, color: "#059669", fontWeight: 500 }}>{SUITABLE_ROW.aiAsset}</td>
          </tr>
          <tr style={{ background: "#eff6ff" }}>
            <td style={{ ...tdLabelStyle, fontWeight: 700 }}>{RECOMMEND_ROW.dimension}</td>
            <td style={{ ...tdCenterStyle, color: "#0891b2", fontWeight: 700 }}>{RECOMMEND_ROW.pillow}</td>
            <td style={{ ...tdCenterStyle, color: "#7c3aed", fontWeight: 700 }}>{RECOMMEND_ROW.remotion}</td>
            <td style={{ ...tdCenterStyle, color: "#059669", fontWeight: 700 }}>{RECOMMEND_ROW.aiAsset}</td>
          </tr>
        </tbody>
      </table>
      <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.5rem", textAlign: "right" }}>
        注：★ 越高越好（成本风险维度：越高 = 风险越低 / 成本越低）
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: "0.6rem 0.85rem",
  textAlign: "center",
  fontWeight: 600,
  fontSize: "0.85rem",
  borderBottom: "2px solid #e2e8f0",
};

const tdLabelStyle: React.CSSProperties = {
  padding: "0.6rem 0.85rem",
  fontWeight: 500,
  color: "#475569",
};

const tdCenterStyle: React.CSSProperties = {
  padding: "0.6rem 0.85rem",
  textAlign: "center",
};

// ─── Conclusion Section ───────────────────────────────────────────────────────

const NEXT_STEPS = [
  {
    scenario: "批量资讯",
    priority: "Pillow",
    color: "#0891b2",
    detail: "稳定快速，适合每日资讯、批量快讯、技术摘要",
  },
  {
    scenario: "精品视频",
    priority: "Remotion",
    color: "#7c3aed",
    detail: "动效丰富，成片感强，适合重要选题、需要视频感的内容",
  },
  {
    scenario: "重要选题 / 氛围增强",
    priority: "AI素材",
    color: "#059669",
    detail: "视觉氛围最强，科技感突出，适合深度分析、重大发布",
  },
];

// ─── Report Links ─────────────────────────────────────────────────────────────

const REPORT_LINKS = [
  {
    title: "V0.5.8 Pillow 完整音频链路对比报告",
    path: "docs/PILLOW_FULL_AUDIO_CHAIN_V0.5.8.md",
    desc: "Pillow 路线完整成片验证，含 56.8s 成片分析",
  },
  {
    title: "V0.5.9 AI素材路线 Baseline 体检报告",
    path: "docs/AI_ASSET_ROUTE_BASELINE_V0.5.9.md",
    desc: "AI素材路线首次完整链路验证，72s 成片，4张 AI 背景",
  },
  {
    title: "V0.5.7 跨模型交接说明",
    path: "docs/HANDOFF_V0.5.7.md",
    desc: "跨版本交接文档，含 Remotion 路线验证结论",
  },
];

// ─── Page ────────────────────────────────────────────────────────────────────

const ROUTE_CARDS: RouteCardProps[] = [
  {
    routeKey: "local_frame_compose",
    routeName: "Pillow",
    displayName: "Pillow 信息卡路线",
    tagline: "稳定批量信息卡路线",
    status: "完整链路已验证",
    experimentId: "web_local_frame_compose_fca5e1f8",
    duration: "56.8s",
    strengths: [
      "生成最快（秒级）",
      "稳定性最高",
      "可读性最好",
      "成本最低",
      "文字 100% 可控",
    ],
    weaknesses: [
      "成片感弱",
      "Ken Burns 几不可感知",
      "总结页停留偏短",
      "视觉单调",
    ],
    suitable: ["每日资讯", "批量快讯", "技术摘要"],
    recommendation: "批量默认路线",
    accentColor: "#0891b2",
    icon: "🖼️",
  },
  {
    routeKey: "template_programmatic_render",
    routeName: "Remotion",
    displayName: "Remotion 动效模板路线",
    tagline: "动效精品模板路线",
    status: "完整链路已验证",
    experimentId: "web_template_programmatic_render_fb270ca2",
    duration: "85.3s",
    strengths: [
      "成片感最强",
      "卡片入场动画明显",
      "数字强调醒目",
      "封面感强",
      "动效丰富",
    ],
    weaknesses: [
      "生成慢",
      "构建链路更复杂",
      "KP2 时长偏长",
      "节奏需继续优化",
    ],
    suitable: ["精品单片", "重要选题", "需要视频感的内容"],
    recommendation: "精品默认路线",
    accentColor: "#7c3aed",
    icon: "🎬",
  },
  {
    routeKey: "ai_asset_then_compose",
    routeName: "AI素材",
    displayName: "AI素材 视觉增强路线",
    tagline: "AI 视觉氛围增强路线",
    status: "完整链路已验证",
    experimentId: "ai_asset_full_95e8de24",
    duration: "72.1s",
    strengths: [
      "视觉氛围最强",
      "科技感突出",
      "AI 背景增强电影感",
      "信息卡仍保持可读",
    ],
    weaknesses: [
      "调用 MiniMax 图像 API",
      "成本高于 Pillow / Remotion",
      "背景一致性需要控制",
      "非科技内容适配性未知",
    ],
    suitable: ["重大发布", "深度分析", "需要视觉氛围的视频"],
    recommendation: "视觉增强可选路线",
    accentColor: "#059669",
    icon: "✨",
  },
];

export default function RouteBaselineComparisonPage() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "2.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          路线对比矩阵 · V0.6.0
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.95rem" }}>
          基于 Pillow / Remotion / AI素材 三条路线的真实成片 baseline 结果
        </p>
      </div>

      {/* Route Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "1.5rem",
          marginBottom: "3rem",
        }}
      >
        {ROUTE_CARDS.map((card) => (
          <RouteCard key={card.routeKey} {...card} />
        ))}
      </div>

      {/* Scoring Matrix */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "16px",
          padding: "1.5rem",
          marginBottom: "2.5rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          评分矩阵
        </h2>
        <ScoringMatrix />
      </div>

      {/* Conclusion */}
      <div
        style={{
          background: "linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)",
          borderRadius: "16px",
          padding: "1.5rem 2rem",
          marginBottom: "2.5rem",
          color: "white",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1rem" }}>
          当前推荐策略
        </h2>
        <p style={{ fontSize: "0.9rem", opacity: 0.9, marginBottom: "1.25rem", lineHeight: 1.6 }}>
          当前不应该选唯一默认路线，而应该按场景分配路线：
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          {NEXT_STEPS.map((step) => (
            <div
              key={step.scenario}
              style={{
                background: "rgba(255,255,255,0.1)",
                borderRadius: "10px",
                padding: "0.85rem 1.1rem",
                display: "flex",
                alignItems: "flex-start",
                gap: "0.75rem",
              }}
            >
              <span
                style={{
                  background: step.color,
                  color: "white",
                  borderRadius: "6px",
                  padding: "0.15rem 0.55rem",
                  fontSize: "0.8rem",
                  fontWeight: 700,
                  whiteSpace: "nowrap",
                  minWidth: "80px",
                  textAlign: "center",
                }}
              >
                {step.priority}
              </span>
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "0.2rem" }}>
                  {step.scenario}
                </div>
                <div style={{ fontSize: "0.8rem", opacity: 0.85 }}>
                  {step.detail}
                </div>
              </div>
            </div>
          ))}
        </div>
        <div
          style={{
            marginTop: "1.25rem",
            paddingTop: "1rem",
            borderTop: "1px solid rgba(255,255,255,0.2)",
            fontSize: "0.85rem",
            opacity: 0.85,
            lineHeight: 1.6,
          }}
        >
          <strong>后续重点：</strong>探索 Remotion 多表现范式，以及 AI背景 + Remotion 信息卡混合模式
        </div>
      </div>

      {/* Report Links */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "16px",
          padding: "1.5rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1rem", color: "#1e293b" }}>
          Baseline 报告链接
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {REPORT_LINKS.map((report) => (
            <div
              key={report.path}
              style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "10px",
                padding: "0.85rem 1.1rem",
              }}
            >
              <div style={{ fontWeight: 600, fontSize: "0.9rem", color: "#1e293b", marginBottom: "0.25rem" }}>
                {report.title}
              </div>
              <div style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.25rem" }}>
                {report.desc}
              </div>
              <div
                style={{
                  fontSize: "0.78rem",
                  color: "#93c5fd",
                  fontFamily: "monospace",
                  background: "#1e3a5f",
                  borderRadius: "4px",
                  padding: "0.2rem 0.5rem",
                  display: "inline-block",
                }}
              >
                {report.path}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Back link */}
      <div style={{ marginTop: "2rem", textAlign: "center" }}>
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
