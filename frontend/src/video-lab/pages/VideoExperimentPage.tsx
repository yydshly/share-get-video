// Video Experiment Page - 创建并运行实验

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { SEED_TEST_CASES, SEED_VIDEO_METHODS, METHOD_CATEGORY_LABELS } from "../seedData";
import type {
  VideoExperiment,
  VideoExperimentResult,
  CreateExperimentResponse,
} from "../types";
import ProductionStepsTimeline from "../components/ProductionStepsTimeline";

const STATUS_COLORS: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  running: "#3b82f6",
  pending: "#94a3b8",
};

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

  // V0.2.5: Generation parameters for local_frame_compose
  const [genParams, setGenParams] = useState({
    targetDuration: 45,
    keyPointCount: 6,
    highlightMode: "auto",
    transitionEnabled: true,
    transitionFrames: 4,
    stylePreset: "ai_frontier_dark",
  });

  const navigate = useNavigate();
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
          params: selectedMethod === "method_local_frame_compose"
            ? {
                targetDuration: genParams.targetDuration,
                aspectRatio: "9:16",
                keyPointCount: genParams.keyPointCount,
                highlightMode: genParams.highlightMode,
                transitionEnabled: genParams.transitionEnabled,
                transitionFrames: genParams.transitionFrames,
                stylePreset: genParams.stylePreset,
              }
            : {},
        }),
      });

      let data: CreateExperimentResponse;
      if (!resp.ok) {
        const errBody = await resp.json().catch(() => ({}));
        throw new Error(`${resp.status} ${resp.statusText}: ${errBody.detail ?? ""}`);
      }
      data = await resp.json();
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

        {/* V0.2.5: Generation parameters panel - only for local_frame_compose */}
        {selectedMethod === "method_local_frame_compose" && (
          <div style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            padding: "1rem",
            marginBottom: "1.25rem",
          }}>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem", color: "#1e293b" }}>
              生成参数
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
              {/* targetDuration */}
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", color: "#64748b", marginBottom: "0.2rem" }}>
                  目标时长 (秒)
                </label>
                <input
                  type="number"
                  min={15}
                  max={90}
                  value={genParams.targetDuration}
                  onChange={(e) => setGenParams(p => ({ ...p, targetDuration: parseInt(e.target.value) || 45 }))}
                  style={{
                    width: "100%",
                    padding: "0.35rem 0.5rem",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    fontSize: "0.85rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              {/* keyPointCount */}
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", color: "#64748b", marginBottom: "0.2rem" }}>
                  关键点数
                </label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={genParams.keyPointCount}
                  onChange={(e) => setGenParams(p => ({ ...p, keyPointCount: parseInt(e.target.value) || 6 }))}
                  style={{
                    width: "100%",
                    padding: "0.35rem 0.5rem",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    fontSize: "0.85rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              {/* highlightMode */}
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", color: "#64748b", marginBottom: "0.2rem" }}>
                  高亮模式
                </label>
                <select
                  value={genParams.highlightMode}
                  onChange={(e) => setGenParams(p => ({ ...p, highlightMode: e.target.value }))}
                  style={{
                    width: "100%",
                    padding: "0.35rem 0.5rem",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    fontSize: "0.85rem",
                    boxSizing: "border-box",
                  }}
                >
                  <option value="auto">自动</option>
                  <option value="numbers">仅数字</option>
                  <option value="none">无</option>
                </select>
              </div>
              {/* transitionFrames */}
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", color: "#64748b", marginBottom: "0.2rem" }}>
                  转场帧数
                </label>
                <input
                  type="number"
                  min={0}
                  max={8}
                  value={genParams.transitionFrames}
                  onChange={(e) => setGenParams(p => ({ ...p, transitionFrames: parseInt(e.target.value) || 0 }))}
                  style={{
                    width: "100%",
                    padding: "0.35rem 0.5rem",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    fontSize: "0.85rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              {/* transitionEnabled */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <input
                  type="checkbox"
                  id="transitionEnabled"
                  checked={genParams.transitionEnabled}
                  onChange={(e) => setGenParams(p => ({ ...p, transitionEnabled: e.target.checked }))}
                  style={{ width: "16px", height: "16px" }}
                />
                <label htmlFor="transitionEnabled" style={{ fontSize: "0.85rem", color: "#475569", cursor: "pointer" }}>
                  启用转场
                </label>
              </div>
              {/* stylePreset */}
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", color: "#64748b", marginBottom: "0.2rem" }}>
                  视觉风格
                </label>
                <select
                  value={genParams.stylePreset}
                  onChange={(e) => setGenParams(p => ({ ...p, stylePreset: e.target.value }))}
                  style={{
                    width: "100%",
                    padding: "0.35rem 0.5rem",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    fontSize: "0.85rem",
                    boxSizing: "border-box",
                  }}
                >
                  <option value="ai_frontier_dark">AI Frontier Dark</option>
                </select>
              </div>
            </div>
          </div>
        )}

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
                color: STATUS_COLORS[lastResult.experiment.status] ?? "#64748b",
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

              {/* Cover Preview (no video) */}
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
              {lastResult.result.productionSteps.length > 0 && (
                <ProductionStepsTimeline steps={lastResult.result.productionSteps} />
              )}
            </>
          )}

          {/* Navigation buttons */}
          <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <button
              onClick={() => navigate(`/video-lab/experiments/${lastResult.experiment.id}`)}
              style={{
                background: "#3b82f6",
                color: "white",
                border: "none",
                borderRadius: "8px",
                padding: "0.4rem 0.9rem",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              查看详情
            </button>
            <Link
              to="/video-lab/compare"
              style={{
                background: "#10b981",
                color: "white",
                textDecoration: "none",
                borderRadius: "8px",
                padding: "0.4rem 0.9rem",
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
