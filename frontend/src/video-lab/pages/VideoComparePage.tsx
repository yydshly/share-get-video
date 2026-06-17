// Video Compare Page - 本地结果对比页（数据来自浏览器 localStorage）

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { SEED_TEST_CASES, getMethodById, METHOD_CATEGORY_LABELS } from "../seedData";
import type { CreateExperimentResponse } from "../types";
import { VideoAspectFrame } from "../components/VideoAspectFrame";

const STATUS_COLORS: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  running: "#3b82f6",
  pending: "#94a3b8",
};

const STORAGE_KEY = "vl_experiments";

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
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    setExperiments(stored);
  }, []);

  // 任务三：清空本地对比数据（带 confirm 二次确认）
  function handleClearLocal() {
    const ok = window.confirm(
      "确认清空当前浏览器中的本地实验对比数据？\n此操作不会删除后端产物或 runtime 文件。",
    );
    if (!ok) return;
    localStorage.removeItem(STORAGE_KEY);
    setExperiments([]);
  }

  // Group by test case
  const grouped: Record<string, CreateExperimentResponse[]> = {};
  for (const exp of experiments) {
    const key = exp.experiment.testCaseId;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(exp);
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      {/* 任务一：顶部"本地暂存数据"提示 */}
      <div
        data-testid="local-storage-banner"
        style={{
          background: "#fffbeb",
          border: "1px solid #fbbf24",
          borderRadius: "10px",
          padding: "1rem 1.25rem",
          marginBottom: "1.5rem",
          color: "#92400e",
          fontSize: "0.9rem",
          lineHeight: 1.6,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: "0.4rem" }}>
          ⚠️ 当前页面为本地暂存结果对比页
        </div>
        <div>
          数据来源：浏览器 <code style={{ background: "#fef3c7", padding: "0 0.25rem", borderRadius: "3px" }}>localStorage["vl_experiments"]</code>。
          它不是后端真实实验库，也不代表 Workbench / Style Sweep / Style Gallery 的全部最新结果。
          如果你想查看当前主流程产物，请优先进入 Style Gallery 或 Workbench。
        </div>
        <div style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
          {experiments.length === 0 ? (
            <span>当前浏览器暂无本地暂存实验数据。</span>
          ) : (
            <span>
              当前浏览器共读取到 <strong>{experiments.length}</strong> 条本地暂存实验
              （数据来源：localStorage，存储 key：<code>vl_experiments</code>）。
            </span>
          )}
        </div>
      </div>

      {/* 任务四：主流程快捷入口 */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem",
          marginBottom: "1.5rem",
        }}
      >
        <Link
          to="/video-lab/workbench"
          style={{
            background: "#3b82f6",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
          }}
        >
          进入 Workbench
        </Link>
        <Link
          to="/video-lab/style-sweep"
          style={{
            background: "#8b5cf6",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
          }}
        >
          进入 Style Sweep
        </Link>
        <Link
          to="/video-lab/style-gallery"
          style={{
            background: "#10b981",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
          }}
        >
          进入 Style Gallery
        </Link>
        <Link
          to="/video-lab"
          style={{
            background: "#64748b",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
          }}
        >
          返回 Video Lab 总控台
        </Link>
        {/* 任务三：清空本地对比数据按钮 */}
        <button
          type="button"
          onClick={handleClearLocal}
          data-testid="clear-local-compare"
          style={{
            background: "#fef2f2",
            color: "#dc2626",
            border: "1px solid #fecaca",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.9rem",
            cursor: "pointer",
            marginLeft: "auto",
          }}
          title="只清空当前浏览器 localStorage，不删除后端文件、不删除 runtime 视频。"
        >
          清空本地对比数据
        </button>
      </div>
      <div
        style={{
          fontSize: "0.8rem",
          color: "#94a3b8",
          marginTop: "-1rem",
          marginBottom: "1.5rem",
        }}
      >
        只清空当前浏览器 localStorage，不删除后端文件、不删除 runtime 视频。
      </div>

      {/* 任务六：标题/副标题明确"本地结果对比" */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          本地结果对比
        </h1>
        <p style={{ color: "#64748b" }}>
          按测试用例分组展示当前浏览器 localStorage 中的暂存实验结果
        </p>
      </div>

      {experiments.length === 0 ? (
        // 任务五：空状态文案改成"当前浏览器暂无本地暂存对比数据"
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
          <p style={{ marginBottom: "0.5rem", fontWeight: 500 }}>当前浏览器暂无本地暂存对比数据</p>
          <p style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "1.5rem" }}>
            这只表示 localStorage["vl_experiments"] 为空，不代表系统没有 Workbench 样片或 Style Sweep 结果。
          </p>
          <div style={{ display: "inline-flex", gap: "0.5rem", flexWrap: "wrap", justifyContent: "center" }}>
            <Link
              to="/video-lab/workbench"
              style={{
                background: "#3b82f6",
                color: "white",
                textDecoration: "none",
                borderRadius: "8px",
                padding: "0.5rem 1rem",
                fontSize: "0.9rem",
              }}
            >
              进入 Workbench
            </Link>
            <Link
              to="/video-lab/style-gallery"
              style={{
                background: "#10b981",
                color: "white",
                textDecoration: "none",
                borderRadius: "8px",
                padding: "0.5rem 1rem",
                fontSize: "0.9rem",
              }}
            >
              进入 Style Gallery
            </Link>
          </div>
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
                            <VideoAspectFrame aspectRatio="9:16" fitMode="contain" maxHeight={400}>
                              <video
                                src={exp.result.videoUrl}
                                controls
                              />
                            </VideoAspectFrame>
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
