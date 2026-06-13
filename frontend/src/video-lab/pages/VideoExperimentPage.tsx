// Video Experiment Page - 创建并运行实验

import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { SEED_TEST_CASES, SEED_VIDEO_METHODS, METHOD_CATEGORY_LABELS } from "../seedData";
import type {
  VideoExperiment,
  VideoExperimentResult,
  CreateExperimentResponse,
  ExperimentWithResult,
} from "../types";

export default function VideoExperimentPage() {
  const navigate = useNavigate();
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

  const API_BASE = "http://localhost:8000/video-lab";

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

      // Also store in local state for compare page
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
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
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
            placeholder="例如: AI资讯视频-Remotion方案测试"
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
            onChange={(e) => setSelectedTestCase(e.target.value)}
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
            rows={4}
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
            <div style={{ marginTop: "1rem" }}>
              <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.5rem" }}>
                Provider: {lastResult.result.provider}
              </div>
              <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.5rem" }}>
                Adapter: {lastResult.result.adapter}
              </div>
              <div style={{ fontSize: "0.85rem", color: "#64748b" }}>Video URL: {lastResult.result.videoUrl || "(空)"}</div>

              {lastResult.result.logs && lastResult.result.logs.length > 0 && (
                <div style={{ marginTop: "1rem" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 500, marginBottom: "0.4rem" }}>执行日志：</div>
                  <div
                    style={{
                      background: "#f8fafc",
                      border: "1px solid #e2e8f0",
                      borderRadius: "6px",
                      padding: "0.75rem",
                      fontSize: "0.8rem",
                      fontFamily: "monospace",
                    }}
                  >
                    {lastResult.result.logs.map((log, i) => (
                      <div key={i} style={{ color: "#475569" }}>
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
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
