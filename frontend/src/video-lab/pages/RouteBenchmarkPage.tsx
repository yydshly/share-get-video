// RouteBenchmarkPage - V0.3.0: Multi-route horizontal benchmark page

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { SEED_TEST_CASES } from "../seedData";
import type { RouteDefinition, RouteBenchmark, RouteResult } from "../types";
import RouteScorePanel from "../components/RouteScorePanel";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const STATUS_COLORS: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  mock: "#f59e0b",
  reserved: "#94a3b8",
  pending: "#94a3b8",
  running: "#3b82f6",
  completed: "#10b981",
  partial: "#f59e0b",
};

export default function RouteBenchmarkPage() {
  const [routes, setRoutes] = useState<RouteDefinition[]>([]);
  const [selectedTestCase, setSelectedTestCase] = useState("");
  const [title, setTitle] = useState("");
  const [inputPayload, setInputPayload] = useState('{"content": ""}');
  const [selectedRoutes, setSelectedRoutes] = useState<string[]>([]);
  const [commonParams, setCommonParams] = useState({
    targetDuration: 45,
    keyPointCount: 6,
    highlightMode: "auto",
    transitionEnabled: true,
    transitionFrames: 4,
    stylePreset: "ai_frontier_dark",
  });
  const [isRunning, setIsRunning] = useState(false);
  const [benchmark, setBenchmark] = useState<RouteBenchmark | null>(null);
  const [error, setError] = useState("");

  // Load available routes on mount
  useEffect(() => {
    fetch(`${API_BASE}/routes`)
      .then((r) => r.json())
      .then((data: RouteDefinition[]) => setRoutes(data))
      .catch(() => setError("Failed to load routes"));
  }, []);

  const handleTestCaseChange = (caseId: string) => {
    setSelectedTestCase(caseId);
    const tc = SEED_TEST_CASES.find((t) => t.id === caseId);
    if (tc?.defaultInput) {
      setInputPayload(tc.defaultInput);
    }
  };

  const toggleRoute = (routeId: string) => {
    setSelectedRoutes((prev) =>
      prev.includes(routeId)
        ? prev.filter((r) => r !== routeId)
        : [...prev, routeId]
    );
  };

  const handleRun = async () => {
    if (!selectedTestCase || !title.trim() || selectedRoutes.length === 0) {
      setError("请填写完整信息并选择至少一条路线");
      return;
    }

    setIsRunning(true);
    setError("");
    setBenchmark(null);

    try {
      const payload = JSON.parse(inputPayload);
      const resp = await fetch(`${API_BASE}/route-benchmarks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          testCaseId: selectedTestCase,
          title: title.trim(),
          inputPayload: payload,
          commonParams,
          routeIds: selectedRoutes,
        }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail ?? `${resp.status}`);
      }

      const data: RouteBenchmark = await resp.json();
      setBenchmark(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.5rem" }}>
          <Link
            to="/video-lab"
            style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}
          >
            ← 返回首页
          </Link>
        </div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          多路线横向验证
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.9rem" }}>
          同一份 AI 资讯内容，多条技术路线横向对比，统一评分
        </p>
      </div>

      {/* Route Selection */}
      <div
        style={{
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "1rem" }}>
          选择技术路线
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
          {routes.map((route) => {
            const isSelected = selectedRoutes.includes(route.routeId);
            const statusColor = STATUS_COLORS[route.status] ?? "#94a3b8";
            return (
              <button
                key={route.routeId}
                onClick={() => toggleRoute(route.routeId)}
                style={{
                  padding: "0.5rem 1rem",
                  borderRadius: "8px",
                  border: isSelected ? `2px solid ${statusColor}` : "1px solid #e2e8f0",
                  background: isSelected ? `${statusColor}10` : "white",
                  color: isSelected ? statusColor : "#475569",
                  fontSize: "0.85rem",
                  cursor: "pointer",
                  fontWeight: isSelected ? 600 : 400,
                }}
              >
                {route.name}
                <span
                  style={{
                    marginLeft: "0.4rem",
                    fontSize: "0.7rem",
                    opacity: 0.7,
                    textTransform: "uppercase",
                  }}
                >
                  {route.status}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Benchmark Config */}
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
            placeholder="例如: AI资讯-多路线横向对比"
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
              <option key={tc.id} value={tc.id}>{tc.name}</option>
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
            rows={5}
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
          {isRunning ? "验证中..." : "运行横向验证"}
        </button>

        {error && (
          <div style={{ marginTop: "1rem", color: "#ef4444", fontSize: "0.85rem" }}>
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {benchmark && (
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>验证结果</h2>
            <span
              style={{
                background: `${STATUS_COLORS[benchmark.status] ?? "#94a3b8"}15`,
                color: STATUS_COLORS[benchmark.status] ?? "#94a3b8",
                borderRadius: "999px",
                padding: "0.15rem 0.6rem",
                fontSize: "0.75rem",
                fontWeight: 600,
              }}
            >
              {benchmark.status}
            </span>
            {benchmark.elapsedMs && (
              <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                {benchmark.elapsedMs}ms
              </span>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem" }}>
            {benchmark.results.map((result: RouteResult) => (
              <RouteResultCard key={result.routeId} result={result} />
            ))}
          </div>

          {/* Score Panel */}
          <RouteScorePanel results={benchmark.results} />
        </div>
      )}
    </div>
  );
}

function RouteResultCard({ result }: { result: RouteResult }) {
  const statusColor = STATUS_COLORS[result.status] ?? "#94a3b8";

  return (
    <div
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "1rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <span
          style={{
            background: `${statusColor}15`,
            color: statusColor,
            borderRadius: "4px",
            padding: "0.1rem 0.4rem",
            fontSize: "0.7rem",
            fontWeight: 600,
            textTransform: "uppercase",
          }}
        >
          {result.status}
        </span>
        <strong style={{ fontSize: "0.9rem" }}>{result.routeId}</strong>
      </div>

      <div style={{ fontSize: "0.8rem", color: "#475569", marginBottom: "0.5rem" }}>
        {result.summary}
      </div>

      {result.status === "succeeded" && result.videoUrl && (
        <div style={{ marginTop: "0.75rem" }}>
          <video
            controls
            src={result.videoUrl}
            style={{
              width: "100%",
              maxHeight: "200px",
              borderRadius: "6px",
              objectFit: "contain",
              background: "#0f172a",
            }}
          />
        </div>
      )}

      {result.warnings && result.warnings.length > 0 && (
        <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "#f59e0b" }}>
          {result.warnings[0]}
        </div>
      )}

      {result.metrics && (
        <div
          style={{
            marginTop: "0.75rem",
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
          }}
        >
          {Object.entries(result.metrics).map(([k, v]) => (
            <span
              key={k}
              style={{
                background: "#f8fafc",
                borderRadius: "4px",
                padding: "0.15rem 0.4rem",
                fontSize: "0.7rem",
                color: "#64748b",
              }}
            >
              {k}: {String(v)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
