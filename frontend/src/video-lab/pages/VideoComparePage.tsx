// Video Compare Page - 结果对比页

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { SEED_TEST_CASES, getMethodById, METHOD_CATEGORY_LABELS } from "../seedData";
import type { CreateExperimentResponse } from "../types";

const STATUS_COLORS: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  running: "#3b82f6",
  pending: "#94a3b8",
};

function RiskBadge({ label, level }: { label: string; level: string }) {
  const color = level === "high" || level === "very_high" ? "#ef4444" : level === "medium" ? "#f59e0b" : "#10b981";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.8rem" }}>
      <span style={{ color: "#94a3b8" }}>{label}：</span>
      <span style={{ color, fontWeight: 500 }}>{level}</span>
    </div>
  );
}

function ProductizationBadge({ recommendation }: { recommendation: string }) {
  const config: Record<string, { bg: string; color: string; label: string }> = {
    recommended: { bg: "#f0fdf4", color: "#16a34a", label: "✓ 推荐" },
    backup: { bg: "#fffbeb", color: "#d97706", label: "○ 备选" },
    not_recommended: { bg: "#fef2f2", color: "#dc2626", label: "✗ 不推荐" },
    future: { bg: "#eff6ff", color: "#2563eb", label: "○ 未来可选" },
    failed: { bg: "#fef2f2", color: "#dc2626", label: "✗ 失败" },
  };
  const c = config[recommendation] ?? { bg: "#f8fafc", color: "#64748b", label: recommendation };
  return (
    <span
      style={{
        background: c.bg,
        color: c.color,
        border: `1px solid ${c.color}30`,
        borderRadius: "999px",
        padding: "0.15rem 0.6rem",
        fontSize: "0.8rem",
        fontWeight: 500,
      }}
    >
      {c.label}
    </span>
  );
}

export default function VideoComparePage() {
  const [experiments, setExperiments] = useState<CreateExperimentResponse[]>([]);

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("vl_experiments") ?? "[]");
    setExperiments(stored);
  }, []);

  // Group by test case
  const grouped: Record<string, CreateExperimentResponse[]> = {};
  for (const exp of experiments) {
    const key = exp.experiment.testCaseId;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(exp);
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
            结果对比
          </h1>
          <p style={{ color: "#64748b" }}>
            按测试用例分组展示实验结果
          </p>
        </div>
        <Link
          to="/video-lab/experiments/new"
          style={{
            background: "#3b82f6",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
          }}
        >
          + 新建实验
        </Link>
      </div>

      {experiments.length === 0 ? (
        <div
          style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "12px",
            padding: "3rem",
            textAlign: "center",
            color: "#64748b",
          }}
        >
          <p style={{ marginBottom: "1rem" }}>暂无实验数据</p>
          <Link
            to="/video-lab/experiments/new"
            style={{
              background: "#3b82f6",
              color: "white",
              textDecoration: "none",
              borderRadius: "8px",
              padding: "0.5rem 1rem",
              fontSize: "0.9rem",
            }}
          >
            创建第一个实验
          </Link>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          {Object.entries(grouped).map(([testCaseId, exps]) => {
            const tc = SEED_TEST_CASES.find((t) => t.id === testCaseId);
            return (
              <div key={testCaseId}>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "1rem", color: "#1e293b" }}>
                  {tc?.name ?? testCaseId}
                </h2>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {exps.map((exp) => {
                    const method = getMethodById(exp.experiment.methodId);
                    const rawOutput = exp.result?.rawOutput as Record<string, unknown> | undefined;
                    const assets = exp.result?.assets as Record<string, unknown> | undefined;
                    const riskAssessment = rawOutput?.riskAssessment as Record<string, string> | undefined;
                    const recommendation = (rawOutput?.productizationRecommendation as string | undefined) ?? "";
                    const steps = exp.result?.productionSteps ?? [];
                    const succeededSteps = steps.filter((s: { status: string }) => s.status === "succeeded").length;

                    return (
                      <div
                        key={exp.experiment.id}
                        style={{
                          background: "white",
                          border: "1px solid #e2e8f0",
                          borderRadius: "10px",
                          padding: "1.25rem",
                        }}
                      >
                        {/* Header */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                          <div>
                            <div style={{ fontWeight: 500, marginBottom: "0.25rem" }}>
                              {exp.experiment.title}
                            </div>
                            <div style={{ fontSize: "0.85rem", color: "#64748b" }}>
                              {method?.name ?? exp.experiment.methodId}
                              {method && (
                                <span style={{ marginLeft: "0.5rem" }}>
                                  ({METHOD_CATEGORY_LABELS[method.category]})
                                </span>
                              )}
                            </div>
                          </div>
                          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.3rem" }}>
                            <span
                              style={{
                                background: `${STATUS_COLORS[exp.experiment.status] ?? "#94a3b8"}15`,
                                color: STATUS_COLORS[exp.experiment.status] ?? "#94a3b8",
                                borderRadius: "999px",
                                padding: "0.15rem 0.6rem",
                                fontSize: "0.8rem",
                              }}
                            >
                              {exp.experiment.status}
                            </span>
                            {exp.experiment.elapsedMs && (
                              <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                                {exp.experiment.elapsedMs}ms
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Key metrics row */}
                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "0.75rem",
                            alignItems: "center",
                            marginBottom: "0.75rem",
                          }}
                        >
                          {assets?.frameCount !== undefined && (
                            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                              <span style={{ color: "#94a3b8" }}>帧数：</span>
                              <strong style={{ color: "#1e293b" }}>{String(assets.frameCount)}</strong>
                            </span>
                          )}
                          {assets?.resolution !== undefined && (
                            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                              <span style={{ color: "#94a3b8" }}>分辨率：</span>
                              <strong style={{ color: "#1e293b" }}>{String(assets.resolution)}</strong>
                            </span>
                          )}
                          {assets?.ffmpegSuccess !== undefined && (
                            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                              <span style={{ color: "#94a3b8" }}>FFmpeg：</span>
                              <strong style={{ color: assets.ffmpegSuccess ? "#10b981" : "#ef4444" }}>
                                {assets.ffmpegSuccess ? "成功" : "失败"}
                              </strong>
                            </span>
                          )}
                          {!!assets?.visualPreset ? (
                            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                              <span style={{ color: "#94a3b8" }}>视觉：</span>
                              <strong style={{ color: "#8b5cf6" }}>{`${assets.visualPreset}`}</strong>
                            </span>
                          ) : null}
                          {!!assets?.templateVersion ? (
                            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                              <span style={{ color: "#94a3b8" }}>版本：</span>
                              <strong style={{ color: "#1e293b" }}>{`${assets.templateVersion}`}</strong>
                            </span>
                          ) : null}
                          {recommendation && (
                            <ProductizationBadge recommendation={recommendation} />
                          )}
                          {steps.length > 0 && (
                            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                              <span style={{ color: "#94a3b8" }}>步骤：</span>
                              <strong style={{ color: "#1e293b" }}>{succeededSteps}/{steps.length}</strong>
                            </span>
                          )}
                        </div>

                        {/* Risk + productization */}
                        {(riskAssessment || recommendation) && (
                          <div
                            style={{
                              background: "#f8fafc",
                              border: "1px solid #e2e8f0",
                              borderRadius: "8px",
                              padding: "0.75rem",
                              marginBottom: "0.75rem",
                              display: "flex",
                              flexWrap: "wrap",
                              gap: "0.75rem",
                              alignItems: "flex-start",
                            }}
                          >
                            {riskAssessment && (
                              <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                                <span style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 500 }}>风险评估</span>
                                {riskAssessment.accuracy && <RiskBadge label="准确性" level={riskAssessment.accuracy} />}
                                {riskAssessment.stability && <RiskBadge label="稳定性" level={riskAssessment.stability} />}
                                {riskAssessment.visualAppeal && <RiskBadge label="视觉" level={riskAssessment.visualAppeal} />}
                                {riskAssessment.productization && <RiskBadge label="产品化" level={riskAssessment.productization} />}
                              </div>
                            )}
                            {recommendation && (
                              <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                                <span style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 500 }}>产品化判断</span>
                                <ProductizationBadge recommendation={recommendation} />
                              </div>
                            )}
                          </div>
                        )}

                        {/* Video Preview */}
                        <div
                          style={{
                            background: "#f1f5f9",
                            border: "1px solid #e2e8f0",
                            borderRadius: "8px",
                            height: "100px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "#94a3b8",
                            fontSize: "0.85rem",
                            marginBottom: "0.75rem",
                          }}
                        >
                          {exp.result?.videoUrl ? (
                            <video
                              src={exp.result.videoUrl}
                              style={{ maxHeight: "100%", maxWidth: "100%" }}
                              controls
                            />
                          ) : (
                            <span>视频预览占位</span>
                          )}
                        </div>

                        {/* Footer actions */}
                        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                          <Link
                            to={`/video-lab/experiments/${exp.experiment.id}`}
                            style={{
                              background: "#3b82f6",
                              color: "white",
                              textDecoration: "none",
                              borderRadius: "6px",
                              padding: "0.3rem 0.75rem",
                              fontSize: "0.8rem",
                            }}
                          >
                            查看详情
                          </Link>
                          {exp.result?.videoUrl && (
                            <a
                              href={exp.result.videoUrl}
                              download
                              style={{
                                background: "#10b981",
                                color: "white",
                                textDecoration: "none",
                                borderRadius: "6px",
                                padding: "0.3rem 0.75rem",
                                fontSize: "0.8rem",
                              }}
                            >
                              下载视频
                            </a>
                          )}
                        </div>

                        {exp.error && (
                          <div style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "#ef4444" }}>
                            错误: {exp.error}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
