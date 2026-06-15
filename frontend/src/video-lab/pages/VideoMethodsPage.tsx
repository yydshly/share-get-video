// Video Methods Page - 视频生成方案参考页
// V0.8.5: 明确这是「方案参考页 / 路线库」，不是当前生成主入口
// V0.8.5: 增加主流程快捷入口 + 状态说明 + 每类路线的"当前定位"

import { Link } from "react-router-dom";
import { SEED_VIDEO_METHODS, METHOD_CATEGORY_LABELS } from "../seedData";

const STATUS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  available: { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
  mock: { bg: "#fffbeb", text: "#d97706", border: "#fde68a" },
  reserved: { bg: "#eff6ff", text: "#2563eb", border: "#bfdbfe" },
  not_configured: { bg: "#f8fafc", text: "#94a3b8", border: "#e2e8f0" },
};

const LEVEL_COLORS: Record<string, string> = {
  low: "#ef4444",
  medium: "#f59e0b",
  high: "#10b981",
  very_high: "#dc2626",
};

const LEVEL_LABELS: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
  very_high: "极高",
};

const STATUS_LABELS: Record<string, string> = {
  available: "已可用",
  mock: "模拟",
  reserved: "预留",
  not_configured: "未配置",
};

function LevelBadge({ level }: { level: string }) {
  const color = LEVEL_COLORS[level] ?? "#64748b";
  const label = LEVEL_LABELS[level] ?? level;
  return (
    <span
      style={{
        background: `${color}15`,
        color,
        border: `1px solid ${color}30`,
        borderRadius: "4px",
        padding: "0.1rem 0.4rem",
        fontSize: "0.8rem",
      }}
    >
      {label}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors = STATUS_COLORS[status] ?? STATUS_COLORS.not_configured;
  const label = STATUS_LABELS[status] ?? status;
  return (
    <span
      style={{
        background: colors.bg,
        color: colors.text,
        border: `1px solid ${colors.border}`,
        borderRadius: "999px",
        padding: "0.15rem 0.6rem",
        fontSize: "0.8rem",
      }}
    >
      {label}
    </span>
  );
}

// V0.8.5: 每类路线在"当前主流程"中的实际定位。
// 规则：不夸大、明确区分"主流程可验证 / 部分验证 / 方案参考 / 后续预留"。
function getMethodRuntimePosition(id: string, status: string): string {
  if (id === "method_template_programmatic_render") {
    return "主流程重点验证：对应 Remotion 动态模板路线，是 Style Sweep 当前主推路线";
  }
  if (id === "method_local_frame_compose") {
    return "方案参考 / 已部分使用：对应 Pillow / 本地图像帧能力；Workbench 与视觉对比页可见，但不是 Style Sweep 主推路线";
  }
  if (id === "method_ai_asset_then_compose") {
    return "部分验证：AI 素材路线已在 Style Sweep 提供实验，但仍非 Workbench 默认可用路线（preview_only）";
  }
  if (id === "method_ai_video_direct") {
    return "后续预留：当前未接入主流程；如需生成需额外接入文生视频模型";
  }
  if (id === "method_hybrid_pipeline") {
    return "后续预留：当前未接入主流程；规划中的多模态自动编排能力";
  }
  if (id === "method_local_media_compose") {
    return "方案参考：用于说明 MoviePy / FFmpeg 素材拼接方向；当前未被主流程直接选用";
  }
  if (status === "reserved") return "后续预留：当前不作为主流程生成能力";
  if (status === "mock") return "方案参考：用于技术路线建模，不代表稳定生产能力";
  return "未配置或待接入";
}

// V0.8.5: 主流程快捷入口
const MAIN_FLOW_LINKS = [
  { to: "/video-lab/workbench", label: "进入 Workbench", desc: "单路线出片 + 人工确认 + 保存样片" },
  { to: "/video-lab/style-sweep", label: "进入 Style Sweep", desc: "同内容并排比较同路线下不同样式" },
  { to: "/video-lab/style-gallery", label: "进入 Style Gallery", desc: "查看与对比已保存样片" },
];

// V0.8.5: 状态说明（用同一文案风格放在页面顶部）
const STATUS_LEGEND: { status: string; desc: string }[] = [
  { status: "available", desc: "已接入主流程或可直接生成" },
  { status: "mock", desc: "当前主要用于方案建模 / UI 验证 / 参数参考，不等于稳定可用" },
  { status: "reserved", desc: "属于后续规划路线，当前不作为主流程能力" },
  { status: "not_configured", desc: "需要额外配置或尚未接入" },
];

export default function VideoMethodsPage() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      {/* 顶部定位（V0.8.5） */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          视频生成路线库
        </h1>
        <p style={{ color: "#475569", fontSize: "0.95rem", marginBottom: "0.75rem" }}>
          视频生成方案参考页：用于比较 6 类技术路线的适用场景、成本、可控性和产品化潜力。
        </p>
        <p style={{ color: "#dc2626", fontSize: "0.9rem", fontWeight: 500 }}>
          ⚠️ 注意：并非所有路线都已接入当前主流程。当前可验证主线请优先使用
          <strong> Workbench</strong>、<strong>Style Sweep</strong>、<strong>Style Gallery</strong>。
        </p>
      </div>

      {/* V0.8.5: 主流程快捷入口 */}
      <div
        style={{
          background: "#fdf4ff",
          border: "1px solid #f0abfc",
          borderRadius: 12,
          padding: "1rem 1.25rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: "0.75rem", color: "#a21caf", fontSize: "0.9rem" }}>
          🚀 当前主流程入口
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem" }}>
          {MAIN_FLOW_LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              title={l.desc}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.5rem 1rem",
                borderRadius: 8,
                fontSize: "0.85rem",
                fontWeight: 600,
                background: "white",
                color: "#a21caf",
                border: "1px solid #f0abfc",
                textDecoration: "none",
              }}
            >
              {l.label}
              <span style={{ fontSize: "0.7rem", color: "#94a3b8", fontWeight: 400 }}>· {l.desc}</span>
            </Link>
          ))}
          <Link
            to="/video-lab"
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "0.5rem 1rem",
              borderRadius: 8,
              fontSize: "0.85rem",
              background: "white",
              color: "#64748b",
              border: "1px solid #e2e8f0",
              textDecoration: "none",
            }}
          >
            ↩ 返回 Video Lab 总控台
          </Link>
        </div>
      </div>

      {/* V0.8.5: 状态说明 */}
      <div
        style={{
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: 10,
          padding: "1rem 1.25rem",
          marginBottom: "1.5rem",
          fontSize: "0.82rem",
          color: "#475569",
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: "0.5rem", color: "#334155" }}>状态说明</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.4rem 1rem" }}>
          {STATUS_LEGEND.map((row) => (
            <div key={row.status} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <StatusBadge status={row.status} />
              <span>{row.desc}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: "0.5rem", color: "#94a3b8", fontSize: "0.78rem" }}>
          📌 当前主流程渲染器只接入了 <strong>Pillow 静态卡</strong> 与 <strong>Remotion 动效</strong> 两条；AI 素材路线在 Style Sweep 提供实验。其它"模拟/预留"路线仅作方案对比参考，不在主流程中调用。
        </div>
      </div>

      {/* 路线卡片列表（V0.8.5: 标题软化 + 每张卡片加"当前定位"） */}
      <div style={{ marginBottom: "1rem", fontSize: "0.9rem", color: "#475569" }}>
        6 类视频生成路线参考（不表示都已在主流程中可调用）：
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {SEED_VIDEO_METHODS.map((method) => {
          const position = getMethodRuntimePosition(method.id, method.implementationStatus);
          return (
            <div
              key={method.id}
              style={{
                background: "white",
                border: "1px solid #e2e8f0",
                borderRadius: "12px",
                padding: "1.5rem",
              }}
            >
              {/* Header */}
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "1rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.25rem" }}>
                    <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>{method.name}</h3>
                    <StatusBadge status={method.implementationStatus} />
                  </div>
                  <p style={{ fontSize: "0.85rem", color: "#64748b" }}>
                    {METHOD_CATEGORY_LABELS[method.category] ?? method.category}
                  </p>
                </div>
              </div>

              {/* V0.8.5: 当前定位（在 description 之上提示，避免误导） */}
              <div
                style={{
                  background: "#eff6ff",
                  border: "1px solid #bfdbfe",
                  borderRadius: 8,
                  padding: "0.5rem 0.75rem",
                  fontSize: "0.82rem",
                  color: "#1e40af",
                  marginBottom: "1rem",
                }}
              >
                当前定位：{position}
              </div>

              <p style={{ fontSize: "0.9rem", color: "#475569", marginBottom: "1rem", lineHeight: 1.6 }}>
                {method.description}
              </p>

              {/* Levels */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>成本</span>
                  <LevelBadge level={method.costLevel} />
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>可控性</span>
                  <LevelBadge level={method.controlLevel} />
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>稳定性</span>
                  <LevelBadge level={method.stabilityLevel} />
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>产品化</span>
                  <LevelBadge level={method.productizationLevel} />
                </div>
              </div>

              {/* Scenarios */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", fontSize: "0.85rem" }}>
                <div>
                  <div style={{ fontWeight: 500, color: "#10b981", marginBottom: "0.3rem" }}>✓ 适合场景</div>
                  <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "#475569" }}>
                    {method.suitableScenarios.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div style={{ fontWeight: 500, color: "#ef4444", marginBottom: "0.3rem" }}>✗ 不适合场景</div>
                  <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "#475569" }}>
                    {method.unsuitableScenarios.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
                <span style={{ color: "#94a3b8" }}>输入要求：</span>
                <span style={{ color: "#475569" }}>{method.inputRequirements}</span>
                <span style={{ marginLeft: "1rem", color: "#94a3b8" }}>输出：</span>
                <span style={{ color: "#475569" }}>{method.outputType}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
