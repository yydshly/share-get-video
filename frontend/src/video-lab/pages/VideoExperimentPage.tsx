// Video Experiment Page - 创建并运行实验

import { useState } from "react";
import { Link } from "react-router-dom";
import { SEED_TEST_CASES, SEED_VIDEO_METHODS, METHOD_CATEGORY_LABELS } from "../seedData";
import type {
  VideoExperiment,
  VideoExperimentResult,
  CreateExperimentResponse,
  VideoProductionStep,
} from "../types";

const STEP_STATUS_COLORS: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  running: "#3b82f6",
  pending: "#94a3b8",
  skipped: "#f59e0b",
};

function ArtifactDetail({ art }: { art: { id: string; type: string; title: string; summary: string; payload: Record<string, unknown> } }) {
  const hasPath = Boolean(art.payload?.path || art.payload?.url);
  return (
    <div
      style={{
        background: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "6px",
        padding: "0.5rem",
        marginBottom: "0.3rem",
      }}
    >
      <div style={{ fontSize: "0.8rem", fontWeight: 500, color: "#1e40af", marginBottom: "0.2rem" }}>
        {art.title || art.type}
      </div>
      <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
        {art.summary}
      </div>
      {hasPath && (
        <div style={{ fontSize: "0.7rem", color: "#93c5fd", marginTop: "0.2rem", fontFamily: "monospace" }}>
          {(art.payload?.url as string) || (art.payload?.path as string)}
        </div>
      )}
    </div>
  );
}

function StepsTimeline({ steps }: { steps: VideoProductionStep[] }) {
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
                border: `1px solid ${STEP_STATUS_COLORS[step.status] ?? "#e2e8f0"}30`,
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
                    width: "20px",
                    height: "20px",
                    borderRadius: "50%",
                    background: STEP_STATUS_COLORS[step.status] ?? "#94a3b8",
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.7rem",
                    flexShrink: 0,
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
                    background: `${STEP_STATUS_COLORS[step.status] ?? "#94a3b8"}15`,
                    color: STEP_STATUS_COLORS[step.status] ?? "#94a3b8",
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
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>产物（{step.artifacts.length}）：</span>
                      <div style={{ marginTop: "0.3rem" }}>
                        {step.artifacts.map((art) => (
                          <ArtifactDetail key={art.id} art={art as { id: string; type: string; title: string; summary: string; payload: Record<string, unknown> }} />
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

export default function VideoExperimentPage() {
  const [selectedTestCase, setSelectedTestCase] = useState("");
  const [selectedMethod, setSelectedMethod] = useState("");
  const [title, setTitle] = useState("");
  const [inputPayload, setInputPayload] = useState('{"content": ""}');
  const [isRunning, setIsRunning] = useState(false);
  const [lastResult, setLastResult] = useState<{
    experiment: VideoExperiment;
    result?: VideoExperimentResult;
    error?: string;
  } | null>(null);

  const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

  const handleTestCaseChange = (testCaseId: string) => {
    setSelectedTestCase(testCaseId);
    const tc = SEED_TEST_CASES.find((t) => t.id === testCaseId);
    if (tc?.defaultInput) {
      setInputPayload(tc.defaultInput);
    }
  };

  const handleRun = async () => {
    if (!selectedTestCase || !selectedMethod || !title.trim()) {
      alert("请填写完整信息");
      return;
    }

    setIsRunning(true);
    setLastResult(null);

    try {
      const payload = JSON.parse(inputPayload);
      const resp = await fetch(`${API_BASE}/experiments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          testCaseId: selectedTestCase,
          methodId: selectedMethod,
          title: title.trim(),
          inputPayload: payload,
          params: {},
        }),
      });
      const data: CreateExperimentResponse = await resp.json();
      setLastResult(data);

      const stored = JSON.parse(localStorage.getItem("vl_experiments") ?? "[]");
      stored.push(data);
      localStorage.setItem("vl_experiments", JSON.stringify(stored));
    } catch (err) {
      setLastResult({
        experiment: {
          id: "error",
          testCaseId: selectedTestCase,
          methodId: selectedMethod,
          title: title.trim(),
          inputPayload: {},
          params: {},
          status: "failed",
          createdAt: new Date().toISOString(),
          startedAt: null,
          finishedAt: null,
          elapsedMs: null,
          errorMessage: String(err),
        },
        error: String(err),
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          创建实验
        </h1>
        <p style={{ color: "#64748b" }}>
          选择测试用例和生成方案，运行能力验证实验
        </p>
      </div>

      {/* Form */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ marginBottom: "1.25rem" }}>
          <label style={{ display: "block", fontSize: "0.9rem", fontWeight: 500, marginBottom: "0.4rem" }}>
            实验标题
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="例如: AI资讯视频-LocalFrame方案测试"
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              fontSize: "0.9rem",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <label style={{ display: "block", fontSize: "0.9rem", fontWeight: 500, marginBottom: "0.4rem" }}>
            测试用例
          </label>
          <select
            value={selectedTestCase}
            onChange={(e) => handleTestCaseChange(e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              fontSize: "0.9rem",
            }}
          >
            <option value="">-- 选择测试用例 --</option>
            {SEED_TEST_CASES.map((tc) => (
              <option key={tc.id} value={tc.id}>
                {tc.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <label style={{ display: "block", fontSize: "0.9rem", fontWeight: 500, marginBottom: "0.4rem" }}>
            生成方案
          </label>
          <select
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              fontSize: "0.9rem",
            }}
          >
            <option value="">-- 选择生成方案 --</option>
            {SEED_VIDEO_METHODS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({METHOD_CATEGORY_LABELS[m.category]})
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <label style={{ display: "block", fontSize: "0.9rem", fontWeight: 500, marginBottom: "0.4rem" }}>
            输入内容 (JSON)
          </label>
          <textarea
            value={inputPayload}
            onChange={(e) => setInputPayload(e.target.value)}
            rows={6}
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              fontSize: "0.85rem",
              fontFamily: "monospace",
              boxSizing: "border-box",
            }}
          />
        </div>

        <button
          onClick={handleRun}
          disabled={isRunning}
          style={{
            background: isRunning ? "#93c5fd" : "#3b82f6",
            color: "white",
            border: "none",
            borderRadius: "8px",
            padding: "0.6rem 1.5rem",
            fontSize: "0.95rem",
            cursor: isRunning ? "not-allowed" : "pointer",
          }}
        >
          {isRunning ? "运行中..." : "Run Experiment"}
        </button>
      </div>

      {/* Result */}
      {lastResult && (
        <div
          style={{
            background: "white",
            border: `1px solid ${lastResult.error ? "#fca5a5" : "#bbf7d0"}`,
            borderRadius: "12px",
            padding: "1.5rem",
          }}
        >
          <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem" }}>实验结果</h3>

          <div style={{ fontSize: "0.9rem", color: "#475569", marginBottom: "0.5rem" }}>
            <strong>实验ID：</strong> {lastResult.experiment.id}
          </div>
          <div style={{ fontSize: "0.9rem", color: "#475569", marginBottom: "0.5rem" }}>
            <strong>状态：</strong>{" "}
            <span
              style={{
                color:
                  lastResult.experiment.status === "succeeded"
                    ? "#10b981"
                    : lastResult.experiment.status === "failed"
                    ? "#ef4444"
                    : "#64748b",
              }}
            >
              {lastResult.experiment.status}
            </span>
          </div>
          {lastResult.experiment.elapsedMs && (
            <div style={{ fontSize: "0.9rem", color: "#475569", marginBottom: "0.5rem" }}>
              <strong>耗时：</strong> {lastResult.experiment.elapsedMs}ms
            </div>
          )}
          {lastResult.experiment.errorMessage && (
            <div style={{ fontSize: "0.9rem", color: "#ef4444", marginBottom: "0.5rem" }}>
              <strong>错误：</strong> {lastResult.experiment.errorMessage}
            </div>
          )}

          {lastResult.result && (
            <>
              <div style={{ marginTop: "1rem" }}>
                <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.5rem" }}>
                  <strong>Provider:</strong> {lastResult.result.provider}
                </div>
                <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.5rem" }}>
                  <strong>Adapter:</strong> {lastResult.result.adapter}
                </div>
              </div>

              {/* Video Preview */}
              {lastResult.result.videoUrl && (
                <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 500, color: "#1e293b", marginBottom: "0.5rem" }}>
                    视频预览
                  </div>
                  <div
                    style={{
                      background: "#1e293b",
                      borderRadius: "8px",
                      maxHeight: "400px",
                      overflow: "hidden",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <video
                      controls
                      src={lastResult.result.videoUrl}
                      style={{
                        maxWidth: "100%",
                        maxHeight: "400px",
                        objectFit: "contain",
                      }}
                    />
                  </div>
                  <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    <a
                      href={lastResult.result.videoUrl}
                      download
                      style={{
                        background: "#3b82f6",
                        color: "white",
                        textDecoration: "none",
                        borderRadius: "6px",
                        padding: "0.3rem 0.8rem",
                        fontSize: "0.8rem",
                      }}
                    >
                      下载视频
                    </a>
                    {lastResult.result.coverUrl && (
                      <a
                        href={lastResult.result.coverUrl}
                        download
                        style={{
                          background: "#8b5cf6",
                          color: "white",
                          textDecoration: "none",
                          borderRadius: "6px",
                          padding: "0.3rem 0.8rem",
                          fontSize: "0.8rem",
                        }}
                      >
                        下载封面
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Cover Preview */}
              {lastResult.result.coverUrl && !lastResult.result.videoUrl && (
                <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 500, color: "#1e293b", marginBottom: "0.5rem" }}>
                    封面预览
                  </div>
                  <img
                    src={lastResult.result.coverUrl}
                    alt="cover"
                    style={{ maxWidth: "200px", maxHeight: "350px", borderRadius: "8px", objectFit: "contain" }}
                  />
                </div>
              )}

              {/* Production Steps Timeline */}
              {lastResult.result.productionSteps && lastResult.result.productionSteps.length > 0 && (
                <StepsTimeline steps={lastResult.result.productionSteps} />
              )}
            </>
          )}

          <div style={{ marginTop: "1rem" }}>
            <Link
              to="/video-lab/compare"
              style={{
                background: "#10b981",
                color: "white",
                textDecoration: "none",
                borderRadius: "8px",
                padding: "0.4rem 0.8rem",
                fontSize: "0.85rem",
              }}
            >
              查看对比页
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
