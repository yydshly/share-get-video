// Video Methods Page - 生成方案页

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
  const labels: Record<string, string> = {
    available: "已可用",
    mock: "模拟",
    reserved: "预留",
    not_configured: "未配置",
  };
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
      {labels[status] ?? status}
    </span>
  );
}

export default function VideoMethodsPage() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          生成方案
        </h1>
        <p style={{ color: "#64748b" }}>
          6 类视频生成技术路线，包含本地合成、程序化渲染和 AI 生成等不同路径
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {SEED_VIDEO_METHODS.map((method) => (
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
        ))}
      </div>
    </div>
  );
}
