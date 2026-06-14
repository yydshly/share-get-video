// ExperimentSummaryPanel - Experiment conclusion and summary component

import type { VideoExperimentResult, VideoExperimentEvaluation } from "../types";
import { buildExperimentSummary } from "../domain/experimentSummary";

interface Props {
  result: VideoExperimentResult;
  evaluation?: VideoExperimentEvaluation | null;
}

export default function ExperimentSummaryPanel({ result, evaluation }: Props) {
  const summary = buildExperimentSummary(result, evaluation);

  const REC_COLORS: Record<string, { bg: string; color: string }> = {
    高: { bg: "#f0fdf4", color: "#16a34a" },
    中: { bg: "#fffbeb", color: "#d97706" },
    低: { bg: "#fef2f2", color: "#dc2626" },
  };
  const recStyle = REC_COLORS[summary.recommendation] ?? REC_COLORS["中"];

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.75rem", color: "#1e293b" }}>
        实验结论
      </div>

      {/* Recommendation badge */}
      <div
        style={{
          background: recStyle.bg,
          border: `1px solid ${recStyle.color}30`,
          borderRadius: "8px",
          padding: "0.75rem 1rem",
          marginBottom: "0.75rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <span
          style={{
            fontSize: "1.1rem",
            fontWeight: 700,
            color: recStyle.color,
          }}
        >
          {summary.recommendationLabel}
        </span>
        <span style={{ fontSize: "0.85rem", color: "#475569" }}>
          {summary.reasoning}
        </span>
      </div>

      {/* Strengths */}
      {summary.mainStrengths.length > 0 && (
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#10b981", marginBottom: "0.3rem" }}>
            优点
          </div>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem", color: "#475569" }}>
            {summary.mainStrengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Problems */}
      {summary.mainProblems.length > 0 && (
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#ef4444", marginBottom: "0.3rem" }}>
            问题
          </div>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem", color: "#475569" }}>
            {summary.mainProblems.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Next steps */}
      {summary.nextSteps.length > 0 && (
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#3b82f6", marginBottom: "0.3rem" }}>
            下一步建议
          </div>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem", color: "#475569" }}>
            {summary.nextSteps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Productization note */}
      <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.5rem" }}>
        {summary.productizationWorthy
          ? "✓ 该方案具备产品化价值，可进入下一阶段优化"
          : "✗ 该方案暂不具备产品化价值，需先解决已知问题"}
      </div>
    </div>
  );
}
