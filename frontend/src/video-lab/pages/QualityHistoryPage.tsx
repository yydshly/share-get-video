// QualityHistoryPage - 质量评分趋势（友好名 + 量纲 + 随时间折线）
// Path: /video-lab/quality-history

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const KIND_LABEL: Record<string, string> = { structural: "结构分", perceptual: "视觉分" };

// 机器路线 ID → 友好名（用户看得懂）
const ROUTE_NAME: Record<string, string> = {
  local_frame_compose: "Pillow 静态卡",
  template_programmatic_render: "Remotion 动效",
  ai_asset_then_compose: "AI 素材 + 合成",
};
const routeName = (id: string) => ROUTE_NAME[id] ?? id;

// 维度 → 中文
const DIM_LABEL: Record<string, string> = {
  layout: "排版", readability: "可读", hierarchy: "层级", aesthetics: "美观", consistency: "一致",
  accuracy: "准确", completeness: "完整", timing: "时长", subtitle: "字幕",
};
const dimLabel = (k: string) => DIM_LABEL[k] ?? k;

interface KindSummary { latest: number | null; previous: number | null; delta: number | null; count: number; }
type Summary = Record<string, Record<string, KindSummary>>;

interface Record_ {
  isoTime: string; route: string; kind: string; overall: number | null;
  dimensions?: Record<string, number>; status?: string;
}

// 0-5 量纲 → 颜色（好=绿，中=琥珀，差=红）
function scoreColor(v: number | null): string {
  if (v === null || v === undefined) return "#94a3b8";
  if (v >= 4) return "#16a34a";
  if (v >= 3) return "#d97706";
  return "#dc2626";
}

function deltaBadge(delta: number | null) {
  if (delta === null) return <span style={{ color: "#94a3b8" }}>持平/首次</span>;
  if (delta > 0) return <span style={{ color: "#16a34a" }}>▲ 涨 {delta}</span>;
  if (delta < 0) return <span style={{ color: "#ef4444" }}>▼ 跌 {Math.abs(delta)}</span>;
  return <span style={{ color: "#94a3b8" }}>＝ 持平</span>;
}

// 随时间的迷你折线（满分按 5 归一）
function Sparkline({ values, color }: { values: number[]; color: string }) {
  const W = 140, H = 34, P = 4, MAX = 5;
  if (values.length === 0) return <span style={{ color: "#cbd5e1", fontSize: "0.72rem" }}>暂无趋势</span>;
  if (values.length === 1) {
    const cy = H - P - (values[0] / MAX) * (H - 2 * P);
    return <svg width={W} height={H}><circle cx={W / 2} cy={cy} r={3} fill={color} /></svg>;
  }
  const step = (W - 2 * P) / (values.length - 1);
  const pts = values.map((v, i) => {
    const x = P + i * step;
    const y = H - P - (Math.max(0, Math.min(MAX, v)) / MAX) * (H - 2 * P);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const last = pts[pts.length - 1].split(",");
  return (
    <svg width={W} height={H} style={{ overflow: "visible" }}>
      <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke="#f1f5f9" />
      <polyline points={pts.join(" ")} fill="none" stroke={color} strokeWidth={1.8} strokeLinejoin="round" />
      <circle cx={last[0]} cy={last[1]} r={2.8} fill={color} />
    </svg>
  );
}

export default function QualityHistoryPage() {
  const [summary, setSummary] = useState<Summary>({});
  const [records, setRecords] = useState<Record_[]>([]); // 时间正序（旧→新）
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/quality-summary`).then((r) => r.json()),
      fetch(`${API_BASE}/quality-history?limit=200`).then((r) => r.json()),
    ]).then(([s, h]) => {
      setSummary(s);
      setRecords(Array.isArray(h) ? h : []);
    }).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const routes = Object.keys(summary);
  const seriesOf = (route: string, kind: string) =>
    records.filter((r) => r.route === route && r.kind === kind && typeof r.overall === "number").map((r) => r.overall as number);

  return (
    <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <Link to="/video-lab" style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}>← 返回首页</Link>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>质量评分趋势</h1>
        <button onClick={load} style={{ background: "none", border: "1px solid #e2e8f0", borderRadius: 8, padding: "0.4rem 0.9rem", fontSize: "0.82rem", cursor: "pointer" }}>刷新</button>
      </div>
      <p style={{ color: "#64748b", fontSize: "0.9rem", marginTop: "0.25rem" }}>
        每条路线每次出片都会记一笔评分（满分 5）。下面看<strong>当前分、跟上一次的涨跌、以及随时间的走势</strong>，防止改版后悄悄变差。
      </p>

      {loading && <div style={{ color: "#64748b", padding: "2rem 0" }}>加载中...</div>}

      {!loading && routes.length === 0 && (
        <div style={{ color: "#64748b", padding: "3rem 0", textAlign: "center" }}>
          还没有评分记录。去「技术探测台」或「视频生成对比」生成几条，这里就会出现走势。
        </div>
      )}

      {/* 汇总卡：友好名 + 量纲 + 颜色 + 折线 */}
      {!loading && routes.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1rem", marginTop: "1.5rem" }}>
          {routes.map((route) => (
            <div key={route} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1rem 1.1rem" }}>
              <div style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "0.7rem" }}>{routeName(route)}</div>
              {["structural", "perceptual"].map((kind) => {
                const k = summary[route][kind];
                if (!k) return null;
                const series = seriesOf(route, kind);
                return (
                  <div key={kind} style={{ padding: "0.5rem 0", borderTop: "1px solid #f1f5f9" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <span style={{ color: "#64748b", fontSize: "0.82rem" }}>{KIND_LABEL[kind] ?? kind}</span>
                      <span>
                        <b style={{ fontSize: "1.25rem", color: scoreColor(k.latest) }}>{k.latest ?? "—"}</b>
                        <span style={{ color: "#94a3b8", fontSize: "0.78rem" }}> /5</span>
                        <span style={{ fontSize: "0.76rem", marginLeft: 10 }}>{deltaBadge(k.delta)}</span>
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 2 }}>
                      <Sparkline values={series} color={scoreColor(k.latest)} />
                      <span style={{ color: "#cbd5e1", fontSize: "0.72rem" }}>共 {k.count} 次</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}

      {/* 明细（最近在上） */}
      {!loading && records.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "0.75rem" }}>最近记录</h2>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "#64748b", borderBottom: "1px solid #e2e8f0" }}>
                  <th style={{ padding: "0.4rem" }}>时间</th>
                  <th style={{ padding: "0.4rem" }}>路线</th>
                  <th style={{ padding: "0.4rem" }}>类型</th>
                  <th style={{ padding: "0.4rem" }}>综合(满分5)</th>
                  <th style={{ padding: "0.4rem" }}>维度</th>
                </tr>
              </thead>
              <tbody>
                {[...records].reverse().slice(0, 60).map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "0.4rem", color: "#94a3b8", whiteSpace: "nowrap" }}>{r.isoTime?.replace("T", " ").slice(5, 19)}</td>
                    <td style={{ padding: "0.4rem" }}>{routeName(r.route)}</td>
                    <td style={{ padding: "0.4rem" }}>{KIND_LABEL[r.kind] ?? r.kind}</td>
                    <td style={{ padding: "0.4rem", fontWeight: 700, color: scoreColor(r.overall) }}>{r.overall ?? "—"}</td>
                    <td style={{ padding: "0.4rem", color: "#64748b" }}>
                      {r.dimensions ? Object.entries(r.dimensions).map(([k, v]) => `${dimLabel(k)} ${v}`).join("　") : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
