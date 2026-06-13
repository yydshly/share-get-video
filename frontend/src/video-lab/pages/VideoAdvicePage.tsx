// Video Advice Page - 总结建议页

import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { SEED_TEST_CASES, getMethodById, METHOD_CATEGORY_LABELS } from "../seedData";
import { ADVISOR_RULES } from "../methodAdvice";
import type { VideoMethodAdvice } from "../types";

const LEVEL_COLORS: Record<string, string> = {
  low: "#ef4444",
  medium: "#f59e0b",
  high: "#10b981",
};

function MethodTag({ methodId, label }: { methodId: string; label: string }) {
  const method = getMethodById(methodId);
  return (
    <div
      style={{
        background: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "8px",
        padding: "0.5rem 0.75rem",
        fontSize: "0.85rem",
      }}
    >
      <div style={{ fontWeight: 500, color: "#1e40af" }}>{label}</div>
      <div style={{ color: "#3b82f6" }}>
        {method?.name ?? methodId}
        {method && (
          <span style={{ marginLeft: "0.4rem", fontSize: "0.8rem", color: "#93c5fd" }}>
            ({METHOD_CATEGORY_LABELS[method.category]})
          </span>
        )}
      </div>
    </div>
  );
}

export default function VideoAdvicePage() {
  const [searchParams] = useSearchParams();
  const scenarioParam = searchParams.get("scenario");

  const [selectedScenario, setSelectedScenario] = useState(scenarioParam ?? "all");

  const visibleScenarios = selectedScenario === "all"
    ? SEED_TEST_CASES
    : SEED_TEST_CASES.filter((tc) => tc.id === selectedScenario);

  // Merge seed data with advice rules
  const getAdviceForCase = (caseId: string): VideoMethodAdvice | null => {
    const rule = ADVISOR_RULES[caseId];
    const tc = SEED_TEST_CASES.find((t) => t.id === caseId);
    if (!tc) return null;
    if (!rule) {
      return {
        scenario: tc.name,
        recommendedMethodId: "method_template_programmatic_render",
        backupMethodIds: ["method_ai_asset_then_compose"],
        notRecommendedMethodIds: ["method_ai_video_direct"],
        reasoning: "默认推荐模板化渲染路线，可控性最强。",
        productizationLevel: "medium",
        suggestedStack: ["Remotion", "FFmpeg"],
        riskNotes: ["需评估具体场景适配性"],
        nextActions: ["补充场景特征定义"],
      };
    }
    return { scenario: tc.name, ...rule };
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          总结建议
        </h1>
        <p style={{ color: "#64748b" }}>
          根据场景输出方案推荐、备选方案、不推荐方案及技术栈建议
        </p>
      </div>

      {/* Filter */}
      <div style={{ marginBottom: "2rem" }}>
        <select
          value={selectedScenario}
          onChange={(e) => setSelectedScenario(e.target.value)}
          style={{
            padding: "0.5rem 0.75rem",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            fontSize: "0.9rem",
          }}
        >
          <option value="all">全部场景</option>
          {SEED_TEST_CASES.map((tc) => (
            <option key={tc.id} value={tc.id}>{tc.name}</option>
          ))}
        </select>
      </div>

      {/* Advice Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {visibleScenarios.map((tc) => {
          const advice = getAdviceForCase(tc.id);
          if (!advice) return null;
          return (
            <div
              key={tc.id}
              style={{
                background: "white",
                border: "1px solid #e2e8f0",
                borderRadius: "12px",
                padding: "1.5rem",
              }}
            >
              {/* Scenario Header */}
              <div style={{ marginBottom: "1rem" }}>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                  {tc.name}
                </h2>
                <p style={{ fontSize: "0.85rem", color: "#64748b" }}>{tc.description}</p>
              </div>

              {/* Recommendations */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
                <MethodTag methodId={advice.recommendedMethodId} label="✓ 推荐" />
                {advice.backupMethodIds.map((mid) => (
                  <MethodTag key={mid} methodId={mid} label="○ 备选" />
                ))}
              </div>

              {/* Not Recommended */}
              {advice.notRecommendedMethodIds.length > 0 && (
                <div style={{ marginBottom: "1rem" }}>
                  <div style={{ fontSize: "0.8rem", color: "#ef4444", fontWeight: 500, marginBottom: "0.4rem" }}>
                    ✗ 不推荐
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                    {advice.notRecommendedMethodIds.map((mid) => {
                      const m = getMethodById(mid);
                      return (
                        <span
                          key={mid}
                          style={{
                            background: "#fef2f2",
                            color: "#ef4444",
                            border: "1px solid #fecaca",
                            borderRadius: "6px",
                            padding: "0.25rem 0.6rem",
                            fontSize: "0.8rem",
                          }}
                        >
                          {m?.name ?? mid}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Reasoning */}
              <div
                style={{
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                  padding: "1rem",
                  marginBottom: "1rem",
                  fontSize: "0.9rem",
                  color: "#475569",
                  lineHeight: 1.6,
                }}
              >
                <div style={{ fontWeight: 500, marginBottom: "0.4rem", color: "#1e293b" }}>推荐原因</div>
                {advice.reasoning}
              </div>

              {/* Bottom Row */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem", fontSize: "0.85rem" }}>
                <div>
                  <div style={{ fontWeight: 500, marginBottom: "0.3rem", color: "#1e293b" }}>推荐技术栈</div>
                  {advice.suggestedStack.map((s) => (
                    <div key={s} style={{ color: "#475569" }}>
                      · {s}
                    </div>
                  ))}
                </div>
                <div>
                  <div style={{ fontWeight: 500, marginBottom: "0.3rem", color: "#1e293b" }}>风险提示</div>
                  {advice.riskNotes.map((r) => (
                    <div key={r} style={{ color: "#ef4444" }}>
                      · {r}
                    </div>
                  ))}
                </div>
                <div>
                  <div style={{ fontWeight: 500, marginBottom: "0.3rem", color: "#1e293b" }}>下一步动作</div>
                  {advice.nextActions.map((a) => (
                    <div key={a} style={{ color: "#10b981" }}>
                      · {a}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
