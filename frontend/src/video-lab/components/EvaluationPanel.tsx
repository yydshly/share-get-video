// EvaluationPanel - Human evaluation form and display component

import { useState } from "react";
import type { VideoExperimentEvaluation } from "../types";

const DIMENSIONS: { key: keyof Omit<VideoExperimentEvaluation, "experimentId" | "notes" | "averageScore">; label: string }[] = [
  { key: "informationAccuracy", label: "信息准确性" },
  { key: "readability", label: "可读性" },
  { key: "visualQuality", label: "视觉质量" },
  { key: "pacing", label: "节奏" },
  { key: "shareability", label: "分享价值" },
  { key: "stability", label: "稳定性" },
  { key: "productizationValue", label: "产品化价值" },
];

interface Props {
  experimentId: string;
  existingEvaluation?: VideoExperimentEvaluation | null;
  apiBase: string;
  onEvaluationSaved?: (evaluation: VideoExperimentEvaluation) => void;
}

function StarRating({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div style={{ display: "flex", gap: "0.25rem", alignItems: "center" }}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => onChange(n)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "1.1rem",
            color: n <= value ? "#f59e0b" : "#d1d5db",
            padding: "0 2px",
          }}
        >
          ★
        </button>
      ))}
      <span style={{ fontSize: "0.8rem", color: "#64748b", marginLeft: "0.25rem" }}>
        {value}/5
      </span>
    </div>
  );
}

function EvaluationDisplay({ evaluation }: { evaluation: VideoExperimentEvaluation }) {
  const dims = DIMENSIONS.filter((d) => d.key !== "notes");
  const scores = dims.map((d) => (evaluation as Record<string, unknown>)[d.key] as number).filter(Boolean);
  const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) : "—";

  return (
    <div
      style={{
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        padding: "1rem",
      }}
    >
      <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem", color: "#1e293b" }}>
        已保存评分
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem" }}>
        {DIMENSIONS.filter((d) => d.key !== "notes").map((dim) => {
          const score = (evaluation as Record<string, unknown>)[dim.key] as number;
          return (
            <div key={dim.key} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem" }}>
              <span style={{ color: "#64748b" }}>{dim.label}</span>
              <span style={{ fontWeight: 600, color: score >= 4 ? "#10b981" : score >= 3 ? "#f59e0b" : "#ef4444" }}>
                {score > 0 ? `${score}/5` : "—"}
              </span>
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.5rem" }}>
        平均分：<strong style={{ color: "#1e293b" }}>{avg}</strong>
      </div>

      {evaluation.notes && (
        <div style={{ fontSize: "0.82rem", color: "#475569", fontStyle: "italic" }}>
          备注：{evaluation.notes}
        </div>
      )}
    </div>
  );
}

export default function EvaluationPanel({ experimentId, existingEvaluation, apiBase, onEvaluationSaved }: Props) {
  const [scores, setScores] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {};
    DIMENSIONS.forEach((d) => { init[d.key] = 0; });
    if (existingEvaluation) {
      DIMENSIONS.forEach((d) => {
        const v = (existingEvaluation as Record<string, unknown>)[d.key];
        if (typeof v === "number") init[d.key] = v;
      });
    }
    return init;
  });
  const [notes, setNotes] = useState(existingEvaluation?.notes ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(!!existingEvaluation);

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const resp = await fetch(`${apiBase}/experiments/${experimentId}/evaluation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...scores, notes }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(`${resp.status}: ${err.detail ?? resp.statusText}`);
      }
      const data = await resp.json();
      setSaved(true);
      onEvaluationSaved?.(data as VideoExperimentEvaluation);
    } catch (err) {
      setError(String(err));
    } finally {
      setIsSaving(false);
    }
  };

  if (saved && !error) {
    return (
      <div style={{ marginTop: "1.5rem" }}>
        <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.75rem", color: "#1e293b" }}>
          人工评分
        </div>
        <EvaluationDisplay
          evaluation={{
            experimentId,
            ...scores,
            notes,
            averageScore: 0,
          } as VideoExperimentEvaluation}
        />
        <button
          onClick={() => setSaved(false)}
          style={{
            marginTop: "0.75rem",
            fontSize: "0.82rem",
            color: "#64748b",
            background: "none",
            border: "1px solid #e2e8f0",
            borderRadius: "6px",
            padding: "0.3rem 0.75rem",
            cursor: "pointer",
          }}
        >
          重新评分
        </button>
      </div>
    );
  }

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.75rem", color: "#1e293b" }}>
        人工评分
      </div>
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          padding: "1rem",
        }}
      >
        {DIMENSIONS.filter((d) => d.key !== "notes").map((dim) => (
          <div
            key={dim.key}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "0.6rem",
            }}
          >
            <span style={{ fontSize: "0.85rem", color: "#475569", minWidth: "80px" }}>
              {dim.label}
            </span>
            <StarRating
              value={scores[dim.key] ?? 0}
              onChange={(v) => setScores((s) => ({ ...s, [dim.key]: v }))}
            />
          </div>
        ))}

        {/* Notes */}
        <div style={{ marginTop: "0.75rem", marginBottom: "0.75rem" }}>
          <label style={{ display: "block", fontSize: "0.82rem", color: "#64748b", marginBottom: "0.25rem" }}>
            备注
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            placeholder="评分备注（可选）"
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "0.4rem",
              fontSize: "0.82rem",
              border: "1px solid #e2e8f0",
              borderRadius: "6px",
              resize: "vertical",
              fontFamily: "inherit",
            }}
          />
        </div>

        {error && (
          <div style={{ fontSize: "0.82rem", color: "#ef4444", marginBottom: "0.5rem" }}>
            保存失败: {error}
          </div>
        )}

        <button
          onClick={handleSave}
          disabled={isSaving || Object.values(scores).every((v) => v === 0)}
          style={{
            background: "#10b981",
            color: "white",
            border: "none",
            borderRadius: "6px",
            padding: "0.45rem 1rem",
            fontSize: "0.85rem",
            cursor: "pointer",
            opacity: Object.values(scores).every((v) => v === 0) ? 0.5 : 1,
          }}
        >
          {isSaving ? "保存中..." : "保存评分"}
        </button>
      </div>
    </div>
  );
}
