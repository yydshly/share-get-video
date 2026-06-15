// Video Capability Lab - Home Page
// V0.7.4: 视频生成流程总控台 — 不再是「功能卡片堆叠」
// 目标：让用户一眼看懂当前主线 / 哪些流程已通 / 哪些只是验证 / 哪些是历史

import { Link } from "react-router-dom";

type EntryStatus =
  | "主线入口 · 已通"
  | "产物沉淀 · 已通"
  | "样式验证 · 已通但质量待排查"
  | "可用"
  | "可用 / 高级"
  | "历史入口"
  | "参考页"
  | "静态页"
  | "待清理"
  | "待接真实数据";

interface NavCard {
  to: string;
  title: string;
  desc: string;
  icon: string;
  color: string;
  status: EntryStatus;
  /** status 的强调色（与卡片主色一致或更柔和） */
  statusColor: string;
  /** status 的背景色 */
  statusBg: string;
  /** 大区块分组 */
  group: "main" | "verify" | "history";
}

// ─── 主线流程入口（3 个，最显眼） ────────────────────────────────────────────

const MAIN_ENTRIES: NavCard[] = [
  {
    to: "/video-lab/workbench",
    title: "视频生成实验台",
    desc: "输入内容，选择路线，生成完整视频，人工确认，通过后保存样片并加入对比。",
    icon: "🧪",
    color: "#0f766e",
    status: "主线入口 · 已通",
    statusColor: "#0f766e",
    statusBg: "#f0fdfa",
    group: "main",
  },
  {
    to: "/video-lab/style-gallery?tab=gallery&source=workbench",
    title: "样片库 / 对比面板",
    desc: "查看 Workbench 保存的样片，按来源筛选，播放视频，进入对比面板并排比较。",
    icon: "🎞️",
    color: "#7c3aed",
    status: "产物沉淀 · 已通",
    statusColor: "#7c3aed",
    statusBg: "#faf5ff",
    group: "main",
  },
  {
    to: "/video-lab/style-sweep",
    title: "样式对比台",
    desc: "同一内容批量生成多个样式，用来观察不同风格差异。当前已发现 Remotion 样式差异偏小、部分成片缺图或音画不对应，先记录，后续逐项排查。",
    icon: "🎨",
    color: "#c026d3",
    status: "样式验证 · 已通但质量待排查",
    statusColor: "#b45309",
    statusBg: "#fffbeb",
    group: "main",
  },
];

// ─── 验证工具入口（第二组） ─────────────────────────────────────────────────

const VERIFY_ENTRIES: NavCard[] = [
  {
    to: "/video-lab/technique-probe",
    title: "技术探测台",
    desc: "一份内容 → 三路线各出整片 → 统一打分排名 → 推荐最佳。",
    icon: "🔎",
    color: "#0ea5e9",
    status: "可用",
    statusColor: "#0e7490",
    statusBg: "#ecfeff",
    group: "verify",
  },
  {
    to: "/video-lab/visual-compose",
    title: "视频生成对比",
    desc: "直接调用 visual-compose，跑单条路线端到端出片。",
    icon: "🎥",
    color: "#2563eb",
    status: "可用 / 高级",
    statusColor: "#1d4ed8",
    statusBg: "#eff6ff",
    group: "verify",
  },
  {
    to: "/video-lab/frame-preview",
    title: "调试台",
    desc: "单帧 / clip 秒级预览，调版式 / 参数 / 强调词。",
    icon: "🛠️",
    color: "#0891b2",
    status: "可用",
    statusColor: "#0e7490",
    statusBg: "#ecfeff",
    group: "verify",
  },
  {
    to: "/video-lab/quality-history",
    title: "评分趋势",
    desc: "查看历史评分趋势 / 各路线分位。",
    icon: "📈",
    color: "#14b8a6",
    status: "可用",
    statusColor: "#0f766e",
    statusBg: "#f0fdfa",
    group: "verify",
  },
];

// ─── 历史 / 待清理入口（第三组，明显降级） ─────────────────────────────────

const HISTORY_ENTRIES: NavCard[] = [
  {
    to: "/video-lab/experiments/new",
    title: "创建实验",
    desc: "选择测试用例和生成方案运行实验（旧版手动流程）。",
    icon: "🧪",
    color: "#94a3b8",
    status: "历史入口",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/route-benchmark",
    title: "多路线验证",
    desc: "多技术路线横向对比（旧版报告）。",
    icon: "🔀",
    color: "#94a3b8",
    status: "历史入口",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/route-playground",
    title: "链路测试台",
    desc: "用同一份样例测试各视频生成路线。",
    icon: "🎬",
    color: "#94a3b8",
    status: "历史入口",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/route-baseline-comparison",
    title: "路线对比矩阵",
    desc: "Pillow / Remotion / AI 素材 三路线 baseline 对比（纯硬编码静态页，零后端调用）。",
    icon: "📋",
    color: "#94a3b8",
    status: "静态页",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/compare",
    title: "结果对比",
    desc: "对比不同方案的实验结果（静态报告页）。",
    icon: "📊",
    color: "#94a3b8",
    status: "静态页",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/advice",
    title: "总结建议",
    desc: "Advisor 推荐（目前为硬编码 / 弱数据驱动，谨慎采纳）。",
    icon: "💡",
    color: "#94a3b8",
    status: "待接真实数据",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/methods",
    title: "生成方案",
    desc: "查看 6 类视频生成技术路线说明（说明页）。",
    icon: "⚙️",
    color: "#94a3b8",
    status: "参考页",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/test-cases",
    title: "测试用例",
    desc: "查看内置标准测试场景（说明页）。",
    icon: "📋",
    color: "#94a3b8",
    status: "参考页",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
  {
    to: "/video-lab/remotion-style-family",
    title: "Remotion 表现范式",
    desc: "Data News / Card Stack 等范式对比（旧版 demo）。",
    icon: "🎞️",
    color: "#94a3b8",
    status: "待清理",
    statusColor: "#64748b",
    statusBg: "#f1f5f9",
    group: "history",
  },
];

// ─── 已知问题清单（首页底部展示，不在主流程里修复） ───────────────────────────

const KNOWN_ISSUES: { tag: "P0" | "P1" | "P2"; text: string }[] = [
  { tag: "P0", text: "Remotion 样式差异偏小：当前更像换色/换字体，不是真正不同 Composition。" },
  { tag: "P0", text: "Remotion 成片可能缺图片/素材。" },
  { tag: "P0", text: "部分视频存在音画不对应。" },
  { tag: "P0", text: "结构评分不等于人工观看质量。" },
  { tag: "P1", text: "Advisor / 总结建议仍可能是硬编码或弱数据驱动。" },
  { tag: "P1", text: "部分旧对比页面仍是静态或历史页面（本轮已分组降级，未清理）。" },
  { tag: "P2", text: "AI 素材路线尚未成为 Workbench 默认可用路线。" },
];

// ─── 主线流程 5 步（横向展示） ───────────────────────────────────────────────

const MAIN_FLOW_STEPS = [
  { idx: 1, title: "Workbench 生成完整视频", status: "已通" },
  { idx: 2, title: "人工观察确认", status: "已通" },
  { idx: 3, title: "保存为样片", status: "已通" },
  { idx: 4, title: "加入对比", status: "已通" },
  { idx: 5, title: "Style Gallery 查看与比较", status: "已通" },
];

// ─── 卡片渲染组件 ─────────────────────────────────────────────────────────

function StatusBadge({ status, color, bg }: { status: EntryStatus; color: string; bg: string }) {
  return (
    <span
      style={{
        fontSize: "0.7rem",
        color,
        background: bg,
        border: `1px solid ${color}40`,
        borderRadius: 999,
        padding: "2px 9px",
        fontWeight: 600,
        whiteSpace: "nowrap",
      }}
    >
      {status}
    </span>
  );
}

function NavCard({ card, dimmed }: { card: NavCard; dimmed?: boolean }) {
  return (
    <Link
      to={card.to}
      style={{ textDecoration: "none", color: "inherit", display: "block", height: "100%" }}
    >
      <div
        style={{
          background: "white",
          border: `1px solid ${dimmed ? "#e2e8f0" : `${card.color}40`}`,
          borderRadius: 12,
          padding: "1.25rem",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          gap: "0.6rem",
          opacity: dimmed ? 0.85 : 1,
          transition: "box-shadow 0.2s, transform 0.2s",
          cursor: "pointer",
          boxSizing: "border-box",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.boxShadow = `0 4px 20px ${card.color}30`;
          e.currentTarget.style.transform = "translateY(-2px)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = "none";
          e.currentTarget.style.transform = "none";
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
          <div style={{ fontSize: "1.6rem" }}>{card.icon}</div>
          <StatusBadge status={card.status} color={card.statusColor} bg={card.statusBg} />
        </div>
        <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "#1e293b" }}>
          {card.title}
        </h3>
        <p style={{ fontSize: "0.82rem", color: "#475569", margin: 0, lineHeight: 1.55 }}>
          {card.desc}
        </p>
        <div style={{ fontSize: "0.72rem", color: "#94a3b8", marginTop: "auto", fontFamily: "monospace" }}>
          {card.to}
        </div>
      </div>
    </Link>
  );
}

// ─── 主组件 ───────────────────────────────────────────────────────────────

export default function VideoLabHome() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      {/* ① 顶部状态区 */}
      <div
        style={{
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f766e 100%)",
          color: "white",
          borderRadius: 16,
          padding: "1.75rem 1.75rem 1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            flexWrap: "wrap",
            marginBottom: "0.6rem",
          }}
        >
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, margin: 0 }}>
            Video Lab · 视频生成流程总控台
          </h1>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <span
              style={{
                fontSize: "0.72rem",
                background: "rgba(255,255,255,0.12)",
                border: "1px solid rgba(255,255,255,0.25)",
                borderRadius: 999,
                padding: "3px 10px",
                fontWeight: 600,
              }}
            >
              阶段：UI 主流程打通 + 问题记录
            </span>
            <span
              style={{
                fontSize: "0.72rem",
                background: "#0f766e",
                color: "white",
                borderRadius: 999,
                padding: "3px 10px",
                fontWeight: 700,
              }}
            >
              V0.7.4
            </span>
          </div>
        </div>
        <p style={{ fontSize: "0.92rem", color: "rgba(255,255,255,0.85)", lineHeight: 1.6, margin: 0 }}>
          用于验证"AI 信息获取后，如何生成可分享的视频内容"。当前阶段优先打通 UI 主流程，不急于修复所有生成质量细节。
        </p>
      </div>

      {/* ② 当前主线流程 */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: 12,
          padding: "1.25rem 1.25rem 1rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1e293b", margin: 0 }}>
            🚦 当前主线流程
          </h2>
          <span style={{ fontSize: "0.72rem", color: "#16a34a", fontWeight: 600 }}>
            主线 5 步全部已通
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: "0.5rem",
            marginBottom: "1rem",
          }}
        >
          {MAIN_FLOW_STEPS.map((step) => (
            <div
              key={step.idx}
              style={{
                background: "#f0fdf4",
                border: "1px solid #bbf7d0",
                borderRadius: 10,
                padding: "0.6rem 0.6rem",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "0.7rem", color: "#16a34a", fontWeight: 700, marginBottom: 4 }}>
                {step.idx}. {step.status}
              </div>
              <div style={{ fontSize: "0.8rem", color: "#166534", fontWeight: 600, lineHeight: 1.35 }}>
                {step.title}
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
          <Link
            to="/video-lab/workbench"
            style={{
              background: "#0f766e",
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              padding: "0.6rem 1.2rem",
              fontSize: "0.88rem",
              fontWeight: 600,
            }}
          >
            进入视频生成实验台 →
          </Link>
          <Link
            to="/video-lab/style-gallery?tab=gallery&source=workbench"
            style={{
              background: "#7c3aed",
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              padding: "0.6rem 1.2rem",
              fontSize: "0.88rem",
              fontWeight: 600,
            }}
          >
            查看 Workbench 样片 →
          </Link>
          {/* V0.7.7: 次级按钮 — 锚点跳到历史/参考/待清理区（不参与主流程） */}
          <a
            href="#legacy-entries"
            style={{
              background: "transparent",
              color: "#64748b",
              textDecoration: "none",
              border: "1px solid #cbd5e1",
              borderRadius: 8,
              padding: "0.55rem 1.05rem",
              fontSize: "0.82rem",
              fontWeight: 500,
            }}
            title="这些页面不是当前主流程，主要用于参考、旧实验回看或后续清理"
          >
            🗄️ 查看历史 / 参考 / 待清理页面 ↓
          </a>
        </div>
      </div>

      {/* ③ 主流程入口 — 3 个一级卡片 */}
      <div style={{ marginBottom: "1.75rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.75rem" }}>
          🧭 主流程入口
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1rem",
          }}
        >
          {MAIN_ENTRIES.map((card) => (
            <NavCard key={card.to} card={card} />
          ))}
        </div>
      </div>

      {/* ④ 验证工具入口 */}
      <div style={{ marginBottom: "1.75rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.75rem" }}>
          🔧 验证工具（已可用 — 不在主流程主路径上）
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "0.85rem",
          }}
        >
          {VERIFY_ENTRIES.map((card) => (
            <NavCard key={card.to} card={card} />
          ))}
        </div>
      </div>

      {/* ⑤ 历史 / 待清理入口 */}
      <div id="legacy-entries" style={{ marginBottom: "1.75rem", scrollMarginTop: "1rem" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.4rem" }}>
          🗄️ 历史 / 参考 / 待清理（不参与主流程）
        </h2>
        <p style={{ fontSize: "0.78rem", color: "#94a3b8", margin: "0 0 0.75rem 0" }}>
          这些页面不是当前主流程，主要用于参考、旧实验回看或后续清理。
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "0.75rem",
          }}
        >
          {HISTORY_ENTRIES.map((card) => (
            <NavCard key={card.to} card={card} dimmed />
          ))}
        </div>
      </div>

      {/* ⑥ 已知问题区（只记录，不在本轮修复） */}
      <div
        style={{
          background: "#fffbeb",
          border: "1px solid #fde68a",
          borderRadius: 12,
          padding: "1.25rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#92400e", margin: 0 }}>
            ⚠️ 已知问题，暂不阻塞主流程
          </h2>
          <Link
            to="https://github.com/yydshly/share-get-video/blob/feature/v0.3.6-b1-shotplan-standardization/docs/OPEN_ISSUES_VIDEO_LAB.md"
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: "0.78rem", color: "#92400e", textDecoration: "underline" }}
          >
            查看完整问题清单 →
          </Link>
        </div>
        <ul style={{ margin: "0.5rem 0 0 0", padding: "0 0 0 1.2rem", color: "#78350f", lineHeight: 1.7 }}>
          {KNOWN_ISSUES.map((it, i) => (
            <li key={i} style={{ fontSize: "0.85rem", marginBottom: 4 }}>
              <span
                style={{
                  display: "inline-block",
                  fontSize: "0.65rem",
                  fontWeight: 700,
                  color: it.tag === "P0" ? "#dc2626" : it.tag === "P1" ? "#d97706" : "#475569",
                  background: it.tag === "P0" ? "#fee2e2" : it.tag === "P1" ? "#fef3c7" : "#f1f5f9",
                  borderRadius: 4,
                  padding: "1px 6px",
                  marginRight: 8,
                }}
              >
                {it.tag}
              </span>
              {it.text}
            </li>
          ))}
        </ul>
        <div
          style={{
            marginTop: "0.85rem",
            padding: "0.5rem 0.75rem",
            background: "white",
            border: "1px solid #fde68a",
            borderRadius: 6,
            fontSize: "0.8rem",
            color: "#92400e",
            fontStyle: "italic",
          }}
        >
          当前策略：先打通 UI 主流程，再按问题清单逐项排查。
        </div>
      </div>
    </div>
  );
}
