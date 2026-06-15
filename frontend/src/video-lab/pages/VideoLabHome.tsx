// Video Capability Lab - Home Page

import { Link } from "react-router-dom";

const NAV_CARDS = [
  {
    to: "/video-lab/technique-probe",
    title: "最佳技术探测台",
    desc: "一份内容 → 三技术各出整片 → 统一打分排名 → 推荐最佳，并排比成片",
    icon: "🔎",
    color: "#0ea5e9",
  },
  {
    to: "/video-lab/workbench",
    title: "视频生成实验台",
    desc: "V0.7.0 · 输入内容，选择路线，生成预览，人工观察确认",
    icon: "🧪",
    color: "#0f766e",
  },
  {
    to: "/video-lab/style-gallery",
    title: "风格样片库",
    desc: "V0.3.7 · 每条路线独立风格探索 · 预置风格一键生成",
    icon: "🎨",
    color: "#ec4899",
  },
  {
    to: "/video-lab/visual-compose",
    title: "视频生成对比",
    desc: "投报告 → 多技术各出片 → 质量分对比",
    icon: "🎥",
    color: "#2563eb",
  },
  {
    to: "/video-lab/frame-preview",
    title: "调试台",
    desc: "单帧秒级预览，调版式/参数/强调词",
    icon: "🛠️",
    color: "#0ea5e9",
  },
  {
    to: "/video-lab/quality-history",
    title: "评分趋势",
    desc: "质量评分留痕，看版本间涨跌、防退化",
    icon: "📈",
    color: "#14b8a6",
  },
  {
    to: "/video-lab/test-cases",
    title: "测试用例",
    desc: "查看内置标准测试场景",
    icon: "📋",
    color: "#3b82f6",
  },
  {
    to: "/video-lab/methods",
    title: "生成方案",
    desc: "了解 6 类视频生成技术路线",
    icon: "⚙️",
    color: "#8b5cf6",
  },
  {
    to: "/video-lab/experiments/new",
    title: "创建实验",
    desc: "选择测试用例和生成方案运行实验",
    icon: "🧪",
    color: "#10b981",
  },
  {
    to: "/video-lab/route-benchmark",
    title: "多路线验证",
    desc: "多技术路线横向对比",
    icon: "🔀",
    color: "#06b6d4",
  },
  {
    to: "/video-lab/route-playground",
    title: "链路测试台",
    desc: "用同一份样例测试各视频生成路线",
    icon: "🎬",
    color: "#ec4899",
  },
  {
    to: "/video-lab/route-baseline-comparison",
    title: "路线对比矩阵",
    desc: "V0.6.0 · Pillow / Remotion / AI素材 三路线 baseline 对比",
    icon: "📋",
    color: "#0891b2",
  },
  {
    to: "/video-lab/remotion-style-family",
    title: "Remotion 表现范式",
    desc: "V0.6.1 · Data News / Timeline / Card Stack / Dashboard / Subtitle Story",
    icon: "🎞️",
    color: "#7c3aed",
  },
  {
    to: "/video-lab/compare",
    title: "结果对比",
    desc: "对比不同方案的实验结果",
    icon: "📊",
    color: "#f59e0b",
  },
  {
    to: "/video-lab/advice",
    title: "总结建议",
    desc: "查看各场景的方案推荐",
    icon: "💡",
    color: "#ef4444",
  },
];

export default function VideoLabHome() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "3rem" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          Video Capability Lab
        </h1>
        <p style={{ fontSize: "1.1rem", color: "#64748b", marginBottom: "1rem" }}>
          视频生成能力验证平台
        </p>
        <p style={{ color: "#475569", lineHeight: 1.7 }}>
          本平台用于系统化验证不同视频生成技术路线的
          <strong>效果、成本、稳定性、可控性和产品化价值</strong>。
          当前验证目标是比较 6 类视频生成方案在不同场景下的适配性。
        </p>
      </div>

      {/* First Goal Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "2rem",
          color: "white",
        }}
      >
        <div style={{ fontSize: "0.85rem", opacity: 0.85, marginBottom: "0.5rem" }}>
          第一目标
        </div>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 600, marginBottom: "0.5rem" }}>
          验证 AI 信息获取后的共享视频制作能力
        </h2>
        <p style={{ fontSize: "0.9rem", opacity: 0.9, marginBottom: "0.75rem" }}>
          当前优先场景：<strong>AI 资讯共享短视频</strong>（竖屏 9:16，30-45 秒）
        </p>
        <p style={{ fontSize: "0.85rem", opacity: 0.8 }}>
          第一阶段重点：流程可解释、步骤可追踪、方案可对比
        </p>
      </div>

      {/* Core Metrics */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "1rem",
          marginBottom: "3rem",
        }}
      >
        {[
          { label: "效果", key: "Effectiveness" },
          { label: "成本", key: "Cost" },
          { label: "稳定性", key: "Stability" },
          { label: "可控性", key: "Controllability" },
          { label: "产品化", key: "Productization" },
        ].map((m) => (
          <div
            key={m.key}
            style={{
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "1rem",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>{m.label}</div>
            <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>{m.key}</div>
          </div>
        ))}
      </div>

      {/* Navigation Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "1.5rem",
        }}
      >
        {NAV_CARDS.map((card) => (
          <Link
            key={card.to}
            to={card.to}
            style={{
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div
              style={{
                background: "white",
                border: "1px solid #e2e8f0",
                borderRadius: "12px",
                padding: "1.5rem",
                transition: "box-shadow 0.2s, transform 0.2s",
                cursor: "pointer",
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
              <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>{card.icon}</div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.5rem" }}>
                {card.title}
              </h3>
              <p style={{ fontSize: "0.9rem", color: "#64748b" }}>{card.desc}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Technology Routes Summary */}
      <div style={{ marginTop: "3rem" }}>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 600, marginBottom: "1rem" }}>
          当前验证的 8 类技术路线
        </h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {[
            "本地图像帧合成",
            "本地媒体素材合成",
            "Remotion 程序化模板",
            "大模型直接生成视频",
            "AI 素材 + 本地合成",
            "混合编排流水线",
          ].map((name, i) => (
            <span
              key={i}
              style={{
                background: "#eff6ff",
                color: "#3b82f6",
                border: "1px solid #bfdbfe",
                borderRadius: "999px",
                padding: "0.25rem 0.75rem",
                fontSize: "0.85rem",
              }}
            >
              {name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
