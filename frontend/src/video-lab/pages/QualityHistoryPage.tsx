// QualityHistoryPage - 质量评分趋势（留痕，看版本间涨跌）
// Path: /video-lab/quality-history

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const KIND_LABEL: Record<string, string> = { structural: "结构层", perceptual: "感知层" };

interface KindSummary { latest: number | null; previous: number | null; delta: number | null; count: number; }
type Summary = Record<string, Record<string, KindSummary>>;

interface Record_ {
  isoTime: string; route: string; kind: string; overall: number | null;
  dimensions?: Record<string, number>; status?: string;
}

function deltaBadge(delta: number | null) {
  if (delta === null) return <span style={{ color: "#94a3b8" }}>—</span>;
  if (delta > 0) return <span style={{ color: "#16a34a" }}>▲ +{delta}</span>;
  if (delta < 0) return <span style={{ color: "#ef4444" }}>▼ {delta}</span>;
  return <span style={{ color: "#94a3b8" }}>＝ 0</span>;
}

export default function QualityHistoryPage() {
  const [summary, setSummary] = useState<Summary>({});
  const [records, setRecords] = useState<Record_[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/quality-summary`).then((r) => r.json()),
      fetch(`${API_BASE}/quality-history?limit=80`).then((r) => r.json()),
    ]).then(([s, h]) => {
      setSummary(s);
      setRecords(Array.isArray(h) ? h.slice().reverse() : []);
    }).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const routes = Object.keys(summary);

  return (
    <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <Link to="/video-lab" style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}>← 返回首页</Link>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>质量评分趋势</h1>
        <button onClick={load} style={{ background: "none", border: "1px solid #e2e8f0", borderRadius: 8, padding: "0.4rem 0.9rem", fontSize: "0.82rem", cursor: "pointer" }}>刷新</button>
      </div>
      <p style={{ color: "#64748b", fontSize: "0.9rem", marginTop: "0.25rem" }}>
        每次生成（结构层）和 AI 视觉评分（感知层）都会留痕，这里看每条路线最新分 + 与上一次的涨跌，防止改版静默退化。
      </p>

      {loading && <div style={{ color: "#64748b", padding: "2rem 0" }}>加载中...</div>}

      {!loading && routes.length === 0 && (
        <div style={{ color: "#64748b", padding: "3rem 0", textAlign: "center" }}>
          还没有评分记录。去「视频生成对比」生成几条、点 AI 视觉评分，这里就会出现趋势。
        </div>
      )}

      {/* 汇总卡 */}
      {!loading && routes.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem", marginTop: "1.5rem" }}>
          {routes.map((route) => (
            <div key={route} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1rem" }}>
              <div style={{ fontFamily: "monospace", fontSize: "0.85rem", fontWeight: 700, marginBottom: "0.6rem" }}>{route}</div>
              {["structural", "perceptual"].map((kind) => {
                const k = summary[route][kind];
                if (!k) return null;
                return (
                  <div key={kind} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.82rem", padding: "0.3rem 0", borderTop: "1px solid #f1f5f9" }}>
                    <span style={{ color: "#64748b" }}>{KIND_LABEL[kind] ?? kind}</span>
                    <span>
                      <b style={{ fontSize: "1rem" }}>{k.latest ?? "—"}</b>
                      <span style={{ fontSize: "0.78rem", marginLeft: 8 }}>{deltaBadge(k.delta)}</span>
                      <span style={{ color: "#cbd5e1", fontSize: "0.72rem", marginLeft: 8 }}>×{k.count}</span>
                    </span>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}

      {/* 明细 */}
      {!loading && records.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "0.75rem" }}>最近记录</h2>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "#64748b", borderBottom: "1px solid #e2e8f0" }}>
                  <th style={{ padding: "0.4rem" }}>时间</th>
                  <th style={{ padding: "0.4rem" }}>路线</th>
                  <th style={{ padding: "0.4rem" }}>类型</th>
                  <th style={{ padding: "0.4rem" }}>综合</th>
                  <th style={{ padding: "0.4rem" }}>维度</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "0.4rem", color: "#94a3b8", whiteSpace: "nowrap" }}>{r.isoTime?.replace("T", " ").slice(5, 19)}</td>
                    <td style={{ padding: "0.4rem", fontFamily: "monospace", fontSize: "0.72rem" }}>{r.route}</td>
                    <td style={{ padding: "0.4rem" }}>{KIND_LABEL[r.kind] ?? r.kind}</td>
                    <td style={{ padding: "0.4rem", fontWeight: 700 }}>{r.overall ?? "—"}</td>
                    <td style={{ padding: "0.4rem", color: "#64748b" }}>
                      {r.dimensions ? Object.entries(r.dimensions).map(([k, v]) => `${k.slice(0, 4)}:${v}`).join("  ") : ""}
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
