// ProductionStepsTimeline - Reusable production steps timeline component

import { useState } from "react";
import type { VideoProductionStep } from "../types";
import ArtifactViewer from "./ArtifactViewer";

const STATUS_COLORS: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  running: "#3b82f6",
  pending: "#94a3b8",
  skipped: "#f59e0b",
};

interface Props {
  steps: VideoProductionStep[];
}

export default function ProductionStepsTimeline({ steps }: Props) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "1rem", color: "#1e293b" }}>
        Production Steps Timeline
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {steps.map((step, idx) => {
          const isExpanded = expandedStep === step.id;
          return (
            <div
              key={step.id}
              style={{
                background: isExpanded ? "#f8fafc" : "white",
                border: `1px solid ${STATUS_COLORS[step.status] ?? "#e2e8f0"}30`,
                borderRadius: "8px",
                overflow: "hidden",
              }}
            >
              {/* Step header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "0.6rem 0.75rem",
                  cursor: "pointer",
                  gap: "0.75rem",
                }}
                onClick={() => setExpandedStep(isExpanded ? null : step.id)}
              >
                <span
                  style={{
                    width: "22px",
                    height: "22px",
                    borderRadius: "50%",
                    background: STATUS_COLORS[step.status] ?? "#94a3b8",
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.7rem",
                    flexShrink: 0,
                    fontWeight: 600,
                  }}
                >
                  {idx + 1}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 500, color: "#1e293b" }}>
                    {step.name}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
                    {step.outputSummary ?? step.status}
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "0.75rem",
                    background: `${STATUS_COLORS[step.status] ?? "#94a3b8"}15`,
                    color: STATUS_COLORS[step.status] ?? "#94a3b8",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "4px",
                  }}
                >
                  {step.status}
                </span>
                <span style={{ color: "#94a3b8", fontSize: "0.75rem" }}>
                  {isExpanded ? "▲" : "▼"}
                </span>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div
                  style={{
                    padding: "0.75rem",
                    borderTop: "1px solid #e2e8f0",
                    background: "#f8fafc",
                  }}
                >
                  {step.inputSummary && (
                    <div style={{ marginBottom: "0.5rem" }}>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>输入：</span>
                      <span style={{ fontSize: "0.8rem", color: "#475569" }}>{step.inputSummary}</span>
                    </div>
                  )}
                  {step.outputSummary && (
                    <div style={{ marginBottom: "0.5rem" }}>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>输出：</span>
                      <span style={{ fontSize: "0.8rem", color: "#475569" }}>{step.outputSummary}</span>
                    </div>
                  )}
                  {step.keyData && Object.keys(step.keyData).length > 0 && (
                    <div style={{ marginBottom: "0.5rem" }}>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>关键数据：</span>
                      <div
                        style={{
                          background: "#1e293b",
                          color: "#e2e8f0",
                          borderRadius: "4px",
                          padding: "0.4rem",
                          fontSize: "0.75rem",
                          fontFamily: "monospace",
                          marginTop: "0.25rem",
                          overflow: "auto",
                          maxHeight: "120px",
                        }}
                      >
                        {JSON.stringify(step.keyData, null, 2)}
                      </div>
                    </div>
                  )}
                  {step.artifacts && step.artifacts.length > 0 && (
                    <div style={{ marginBottom: "0.5rem" }}>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                        产物（{step.artifacts.length}）：
                      </span>
                      <div style={{ marginTop: "0.3rem" }}>
                        {step.artifacts.map((art) => (
                          <ArtifactViewer key={art.id} artifact={art} />
                        ))}
                      </div>
                    </div>
                  )}
                  {step.logs && step.logs.length > 0 && (
                    <div>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>日志：</span>
                      <div
                        style={{
                          background: "#1e293b",
                          color: "#e2e8f0",
                          borderRadius: "4px",
                          padding: "0.4rem",
                          fontSize: "0.75rem",
                          fontFamily: "monospace",
                          marginTop: "0.25rem",
                          maxHeight: "100px",
                          overflow: "auto",
                        }}
                      >
                        {step.logs.map((log, i) => (
                          <div key={i}>{log}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
