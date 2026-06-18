// Video Lab - Home Page
// V1.2.3: 视频生成能力实验室 · Style Gallery Validation Center
// 三层结构：主工作台 / 样片库 / 高级实验区
// 目标：让用户清楚"从哪里开始生成视频 / 哪里看历史 / 哪里做实验"

import { Link } from "react-router-dom";

interface SectionProps {
  title: string;
  description: string;
  emoji: string;
  children: React.ReactNode;
}

function Section({ title, description, emoji, children }: SectionProps) {
  return (
    <section style={{ marginBottom: "1.75rem" }}>
      <div style={{ marginBottom: "0.6rem" }}>
        <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#0f172a", margin: 0 }}>
          {emoji} {title}
        </h2>
        <p style={{ fontSize: "0.82rem", color: "#64748b", margin: "0.25rem 0 0 0", lineHeight: 1.55 }}>
          {description}
        </p>
      </div>
      {children}
    </section>
  );
}

interface EntryCardProps {
  to: string;
  title: string;
  desc: string;
  icon: string;
  emphasis?: "primary" | "secondary" | "normal";
}

function EntryCard({ to, title, desc, icon, emphasis = "normal" }: EntryCardProps) {
  const isPrimary = emphasis === "primary";
  const isSecondary = emphasis === "secondary";

  const colors = isPrimary
    ? { bg: "#0f766e", border: "#0f766e", iconBg: "#0f766e", titleColor: "#0f172a" }
    : isSecondary
    ? { bg: "#7c3aed", border: "#7c3aed", iconBg: "#7c3aed", titleColor: "#0f172a" }
    : { bg: "white", border: "#e2e8f0", iconBg: "#f1f5f9", titleColor: "#1e293b" };

  return (
    <Link
      to={to}
      style={{ textDecoration: "none", color: "inherit", display: "block", height: "100%" }}
    >
      <div
        style={{
          background: colors.bg === "white" ? "white" : colors.bg,
          color: colors.bg === "white" ? "#1e293b" : "white",
          border: `1px solid ${colors.border}40`,
          borderRadius: 12,
          padding: isPrimary || isSecondary ? "1.5rem" : "1.1rem",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          gap: "0.55rem",
          transition: "box-shadow 0.2s, transform 0.2s",
          cursor: "pointer",
          boxSizing: "border-box",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.boxShadow = `0 4px 20px ${colors.iconBg}30`;
          e.currentTarget.style.transform = "translateY(-2px)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = "none";
          e.currentTarget.style.transform = "none";
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <div
            style={{
              fontSize: isPrimary || isSecondary ? "1.8rem" : "1.4rem",
              width: isPrimary || isSecondary ? 44 : 36,
              height: isPrimary || isSecondary ? 44 : 36,
              borderRadius: 8,
              background: isPrimary || isSecondary ? "rgba(255,255,255,0.18)" : colors.iconBg,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {icon}
          </div>
          <h3
            style={{
              fontSize: isPrimary || isSecondary ? "1.1rem" : "0.95rem",
              fontWeight: 700,
              margin: 0,
              color: colors.bg === "white" ? colors.titleColor : "white",
            }}
          >
            {title}
          </h3>
        </div>
        <p
          style={{
            fontSize: "0.82rem",
            color: colors.bg === "white" ? "#475569" : "rgba(255,255,255,0.9)",
            margin: 0,
            lineHeight: 1.55,
          }}
        >
          {desc}
        </p>
        <div
          style={{
            fontSize: "0.7rem",
            color: colors.bg === "white" ? "#94a3b8" : "rgba(255,255,255,0.7)",
            marginTop: "auto",
            fontFamily: "monospace",
          }}
        >
          {to}
        </div>
      </div>
    </Link>
  );
}

// ─── 主组件 ───────────────────────────────────────────────────────────────

export default function VideoLabHome() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      {/* ① 顶部说明区 — 当前阶段、定位、推荐路径 */}
      <div
        style={{
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f766e 100%)",
          color: "white",
          borderRadius: 16,
          padding: "1.75rem",
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
            marginBottom: "0.5rem",
          }}
        >
          <h1 style={{ fontSize: "1.55rem", fontWeight: 700, margin: 0 }}>
            Video Lab · 视频生成能力实验室
          </h1>
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
            V1.2.3 · Style Gallery Validation Center
          </span>
        </div>
        <p style={{ fontSize: "0.92rem", color: "rgba(255,255,255,0.88)", lineHeight: 1.65, margin: 0 }}>
          <strong>主流程：</strong>输入内容 → 生成 preview/full video → 保存样片 → 复制复现参数 → 加入对比 → 保存对比包。
          建议从 <strong>主工作台</strong> 开始，再将有效样片保存到 <strong>样片库</strong>。
        </p>
        <p style={{ fontSize: "0.78rem", color: "rgba(255,255,255,0.7)", lineHeight: 1.6, margin: "0.5rem 0 0 0" }}>
          ⚠️ 高级实验区为调试/探索工具，不是主流程必经步骤。
        </p>
      </div>

      {/* ② 主工作台 — 1 个最显眼的入口 */}
      <Section
        emoji="🧪"
        title="主工作台"
        description="一次完整的视频生成验证入口。从一段内容开始，先生成 preview，确认后再生成完整视频。"
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "1rem",
          }}
        >
          <EntryCard
            to="/video-lab/workbench"
            title="开始生成视频"
            desc="从一段内容开始，生成 preview 或完整视频，查看 artifacts / logs / manifest。"
            icon="🧪"
            emphasis="primary"
          />
        </div>
      </Section>

      {/* ③ 样片库 — 第二入口 */}
      <Section
        emoji="🎞️"
        title="样片库"
        description="保存和观察历史样片，用于人工对比不同路线和风格的实际效果。"
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1rem",
          }}
        >
          <EntryCard
            to="/video-lab/style-gallery?tab=gallery&source=workbench"
            title="查看样片库"
            desc="查看 Workbench 保存的样片，按来源筛选，播放视频，进入对比面板并排比较。"
            icon="🎞️"
            emphasis="secondary"
          />
        </div>
      </Section>

      {/* ④ 高级实验区 — 7 个工具入口分组 */}
      <Section
        emoji="🔬"
        title="高级实验区"
        description="面向路线、样式、质量、Remotion family 的实验工具集合。供人工实验与对比使用，不在主流程主路径上。"
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "0.85rem",
          }}
        >
          <EntryCard
            to="/video-lab/style-sweep"
            title="Style Sweep"
            desc="同一路线下批量测试多种样式。"
            icon="🎨"
          />
          <EntryCard
            to="/video-lab/technique-probe"
            title="Technique Probe"
            desc="同一内容下比较多条生成路线。"
            icon="🔎"
          />
          <EntryCard
            to="/video-lab/remotion-style-family"
            title="Remotion 表现范式"
            desc="观察 Remotion 不同表现范式的差异。"
            icon="🎞️"
          />
          <EntryCard
            to="/video-lab/remotion-lab"
            title="Remotion 能力探索中心"
            desc="探索背景、转场、视觉风格和候选模板。"
            icon="🔬"
          />
          <EntryCard
            to="/video-lab/quality-history"
            title="Quality History"
            desc="查看历史质量评分和路线趋势。"
            icon="📈"
          />
          <EntryCard
            to="/video-lab/frame-preview"
            title="Frame Preview"
            desc="快速预览单帧版式。"
            icon="🖼️"
          />
          <EntryCard
            to="/video-lab/visual-compose"
            title="Visual Compose"
            desc="直接调试完整合成链路。"
            icon="🎥"
          />
          <EntryCard
            to="/video-lab/route-baseline-comparison"
            title="Route Baseline"
            desc="查看路线基线对比。"
            icon="📋"
          />
        </div>
      </Section>

      {/* ⑤ 其它参考页面 — 明显降级 */}
      <Section
        emoji="🗄️"
        title="其它参考 / 历史 / 静态页"
        description="这些页面不是当前主流程，主要用于参考、旧实验回看或后续清理。"
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "0.7rem",
          }}
        >
          {[
            { to: "/video-lab/experiments/new", title: "创建实验（旧）", desc: "选择测试用例和方案（旧版手动流程）。" },
            { to: "/video-lab/route-benchmark", title: "多路线验证（旧）", desc: "多技术路线横向对比（旧版报告）。" },
            { to: "/video-lab/route-playground", title: "链路测试台", desc: "用同一份样例测试各视频生成路线。" },
            { to: "/video-lab/compare", title: "结果对比", desc: "对比不同方案的实验结果（静态报告页）。" },
            { to: "/video-lab/advice", title: "总结建议", desc: "Advisor 推荐（弱数据驱动，谨慎采纳）。" },
            { to: "/video-lab/methods", title: "生成方案说明", desc: "查看 6 类视频生成技术路线说明。" },
            { to: "/video-lab/test-cases", title: "测试用例", desc: "查看内置标准测试场景。" },
          ].map((item) => (
            <Link
              key={item.to}
              to={item.to}
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <div
                style={{
                  background: "white",
                  border: "1px solid #e2e8f0",
                  borderRadius: 8,
                  padding: "0.75rem 0.9rem",
                  opacity: 0.78,
                  transition: "box-shadow 0.2s, transform 0.2s",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = "0 2px 8px rgba(100,116,139,0.15)";
                  e.currentTarget.style.transform = "translateY(-1px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = "none";
                  e.currentTarget.style.transform = "none";
                }}
              >
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#475569", marginBottom: 2 }}>
                  {item.title}
                </div>
                <div style={{ fontSize: "0.74rem", color: "#94a3b8", lineHeight: 1.4 }}>
                  {item.desc}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </Section>
    </div>
  );
}
