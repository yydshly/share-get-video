// TemplateReviewPanel - V0.2.5 Template acceptance suggestions component

import type { VideoExperimentResult, VideoExperimentEvaluation } from "../types";
import { buildTemplateReview } from "../domain/templateReview";

interface Props {
  result: VideoExperimentResult;
  evaluation?: VideoExperimentEvaluation | null;
}

const STATUS_CONFIG = {
  usable: {
    label: "模板可用",
    bg: "#f0fdf4",
    border: "#10b98130",
    color: "#16a34a",
    icon: "✓",
  },
  needs_tuning: {
    label: "需要调参",
    bg: "#fffbeb",
    border: "#f59e0b30",
    color: "#d97706",
    icon: "⚡",
  },
  not_ready: {
    label: "暂不推荐",
    bg: "#fef2f2",
    border: "#ef444430",
    color: "#dc2626",
    icon: "✗",
  },
};

export default function TemplateReviewPanel({ result, evaluation }: Props) {
  const review = buildTemplateReview(result, evaluation);
  const status = STATUS_CONFIG[review.templateStatus];

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.75rem", color: "#1e293b" }}>
        模板验收建议
      </div>

      {/* Status badge */}
      <div
        style={{
          background: status.bg,
          border: `1px solid ${status.border}`,
          borderRadius: "8px",
          padding: "0.75rem 1rem",
          marginBottom: "0.75rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <span style={{ fontSize: "1.1rem" }}>{status.icon}</span>
        <span style={{ fontSize: "0.95rem", fontWeight: 600, color: status.color }}>
          {status.label}
        </span>
        <span style={{ fontSize: "0.85rem", color: "#475569" }}>
          {review.scoreSummary}
        </span>
      </div>

      {/* Parameter suggestions */}
      {review.parameterSuggestions.length > 0 && (
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#8b5cf6", marginBottom: "0.3rem" }}>
            参数调整建议
          </div>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem", color: "#475569" }}>
            {review.parameterSuggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Next actions */}
      {review.nextActions.length > 0 && (
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#3b82f6", marginBottom: "0.3rem" }}>
            下一步行动
          </div>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem", color: "#475569" }}>
            {review.nextActions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
