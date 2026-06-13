// Video Compare Page - 结果对比页

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { SEED_TEST_CASES, getMethodById, METHOD_CATEGORY_LABELS } from "../seedData";
import type { CreateExperimentResponse } from "../types";

export default function VideoComparePage() {
  const [experiments, setExperiments] = useState<CreateExperimentResponse[]>([]);

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("vl_experiments") ?? "[]");
    setExperiments(stored);
  }, []);

  const STATUS_COLORS: Record<string, string> = {
    succeeded: "#10b981",
    failed: "#ef4444",
    running: "#3b82f6",
    pending: "#94a3b8",
  };

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
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
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

                        {/* Video Preview Placeholder */}
                        <div
                          style={{
                            marginTop: "1rem",
                            background: "#f1f5f9",
                            border: "1px solid #e2e8f0",
                            borderRadius: "8px",
                            height: "120px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "#94a3b8",
                            fontSize: "0.85rem",
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

                        {/* Logs */}
                        {exp.result?.logs && exp.result.logs.length > 0 && (
                          <div style={{ marginTop: "0.75rem" }}>
                            <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.3rem" }}>日志摘要：</div>
                            <div
                              style={{
                                background: "#f8fafc",
                                border: "1px solid #e2e8f0",
                                borderRadius: "6px",
                                padding: "0.5rem",
                                fontSize: "0.75rem",
                                fontFamily: "monospace",
                                maxHeight: "80px",
                                overflow: "auto",
                              }}
                            >
                              {exp.result.logs.slice(0, 3).map((log, i) => (
                                <div key={i} style={{ color: "#64748b" }}>
                                  {log}
                                </div>
                              ))}
                              {exp.result.logs.length > 3 && (
                                <div style={{ color: "#94a3b8" }}>
                                  ...还有 {exp.result.logs.length - 3} 行
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Assets */}
                        {exp.result?.assets && Object.keys(exp.result.assets).length > 0 && (
                          <div style={{ marginTop: "0.75rem" }}>
                            <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.3rem" }}>输出信息：</div>
                            <div style={{ fontSize: "0.8rem", color: "#475569", fontFamily: "monospace" }}>
                              {JSON.stringify(exp.result.assets)}
                            </div>
                          </div>
                        )}

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
