// RouteScorePanel - V0.3.0: Score panel for route benchmark results

import { useState } from "react";
import type { RouteResult } from "../types";

interface Props {
  results: RouteResult[];
}

const DIMENSIONS = [
  { key: "informationClarity", label: "信息表达清楚度" },
  { key: "visualQuality", label: "视觉质量" },
  { key: "pacing", label: "节奏感" },
  { key: "shareability", label: "分享价值" },
  { key: "stability", label: "稳定性" },
  { key: "implementationCost", label: "实现复杂度" },
  { key: "productizationPotential", label: "产品化潜力" },
  { key: "worthDeeperExploration", label: "值得继续深挖" },
] as const;

type ScoreDimension = typeof DIMENSIONS[number]["key"];

export interface RouteScores {
  routeId: string;
  scores: Record<ScoreDimension, number | null>;
  notes: string;
}

interface RouteScorePanelProps {
  results: RouteResult[];
  onScoresChange?: (scores: RouteScores[]) => void;
}

export default function RouteScorePanel({ results, onScoresChange }: RouteScorePanelProps) {
  const [scores, setScores] = useState<RouteScores[]>(
    results.map((r) => ({
      routeId: r.routeId,
      scores: Object.fromEntries(DIMENSIONS.map((d) => [d.key, null])) as Record<ScoreDimension, number | null>,
      notes: "",
    }))
  );

  const updateScore = (routeId: string, dimension: ScoreDimension, value: number | null) => {
    const updated = scores.map((s) =>
      s.routeId === routeId ? { ...s, scores: { ...s.scores, [dimension]: value } } : s
    );
    setScores(updated);
    onScoresChange?.(updated);
  };

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "1rem", color: "#1e293b" }}>
        路线评分
      </div>

      {results.map((result) => {
        const routeScore = scores.find((s) => s.routeId === result.routeId);
        const statusColor =
          result.status === "succeeded" ? "#10b981"
          : result.status === "mock" ? "#f59e0b"
          : result.status === "reserved" ? "#94a3b8"
          : "#ef4444";

        return (
          <div
            key={result.routeId}
            style={{
              background: "white",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "1rem",
              marginBottom: "1rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
              <span
                style={{
                  background: `${statusColor}15`,
                  color: statusColor,
                  borderRadius: "4px",
                  padding: "0.15rem 0.5rem",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  textTransform: "uppercase",
                }}
              >
                {result.status}
              </span>
              <strong style={{ fontSize: "0.9rem" }}>{result.routeId}</strong>
              <span style={{ fontSize: "0.8rem", color: "#64748b" }}>{result.summary}</span>
            </div>

            {result.status === "succeeded" ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem" }}>
                {DIMENSIONS.map((dim) => (
                  <div key={dim.key} style={{ fontSize: "0.75rem" }}>
                    <div style={{ color: "#64748b", marginBottom: "0.2rem" }}>{dim.label}</div>
                    <select
                      value={routeScore?.scores[dim.key] ?? ""}
                      onChange={(e) =>
                        updateScore(
                          result.routeId,
                          dim.key,
                          e.target.value ? Number(e.target.value) : null
                        )
                      }
                      style={{
                        width: "100%",
                        padding: "0.25rem",
                        border: "1px solid #e2e8f0",
                        borderRadius: "4px",
                        fontSize: "0.8rem",
                      }}
                    >
                      <option value="">-</option>
                      {[1, 2, 3, 4, 5].map((v) => (
                        <option key={v} value={v}>{v}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: "0.8rem", color: "#94a3b8", fontStyle: "italic" }}>
                {result.warnings?.[0] || "非真实路线，无需评分"}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
