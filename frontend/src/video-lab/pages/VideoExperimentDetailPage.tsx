// VideoExperimentDetailPage - Experiment detail view page

import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import type {
  VideoExperiment,
  VideoExperimentResult,
  VideoExperimentEvaluation,
  ExperimentWithResult,
} from "../types";
import ProductionStepsTimeline from "../components/ProductionStepsTimeline";
import EvaluationPanel from "../components/EvaluationPanel";
import ExperimentSummaryPanel from "../components/ExperimentSummaryPanel";
import ArtifactViewer from "../components/ArtifactViewer";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";

const STATUS_COLORS: Record<string, string> = {
  succeeded: "#10b981",
  failed: "#ef4444",
  running: "#3b82f6",
  pending: "#94a3b8",
};

interface ExperimentResponse {
  experiment: VideoExperiment;
  result?: VideoExperimentResult;
}

export default function VideoExperimentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ExperimentResponse | null>(null);
  const [evaluation, setEvaluation] = useState<VideoExperimentEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await fetch(`${API_BASE}/experiments/${id}`);
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(`${resp.status}: ${err.detail ?? resp.statusText}`);
        }
        const expData: ExperimentResponse = await resp.json();
        setData(expData);

        // Fetch evaluation if it exists
        const evalResp = await fetch(`${API_BASE}/experiments/${id}/evaluation`);
        if (evalResp.ok) {
          const evalData = await evalResp.json();
          setEvaluation(evalData as VideoExperimentEvaluation);
        }
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
        加载中...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: "2rem" }}>
        <div style={{ color: "#ef4444", marginBottom: "1rem" }}>
          加载失败: {error || "未找到实验"}
        </div>
        <Link to="/video-lab/compare" style={{ color: "#3b82f6" }}>返回对比页</Link>
      </div>
    );
  }

  const { experiment, result } = data;
  const rawOutput = result?.rawOutput as Record<string, unknown> | undefined;
  const assets = result?.assets as Record<string, unknown> | undefined;

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
          <Link
            to="/video-lab/compare"
            style={{ color: "#64748b", fontSize: "0.85rem", textDecoration: "none" }}
          >
            ← 返回对比页
          </Link>
        </div>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          {experiment.title}
        </h1>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
          <span
            style={{
              background: `${STATUS_COLORS[experiment.status] ?? "#94a3b8"}15`,
              color: STATUS_COLORS[experiment.status] ?? "#94a3b8",
              borderRadius: "999px",
              padding: "0.15rem 0.6rem",
              fontSize: "0.8rem",
              fontWeight: 500,
            }}
          >
            {experiment.status}
          </span>
          <span style={{ fontSize: "0.82rem", color: "#64748b" }}>
            {experiment.testCaseId} · {experiment.methodId}
          </span>
          {experiment.elapsedMs && (
            <span style={{ fontSize: "0.82rem", color: "#64748b" }}>
              {experiment.elapsedMs}ms
            </span>
          )}
        </div>
        {experiment.errorMessage && (
          <div style={{ marginTop: "0.5rem", fontSize: "0.82rem", color: "#ef4444" }}>
            错误: {experiment.errorMessage}
          </div>
        )}
      </div>

      {/* Memory warning */}
      <div
        style={{
          background: "#fffbeb",
          border: "1px solid #f59e0b30",
          borderRadius: "8px",
          padding: "0.6rem 0.75rem",
          fontSize: "0.8rem",
          color: "#92400e",
          marginBottom: "1rem",
        }}
      >
        ⚠️ 当前实验结果保存在后端内存中，服务重启后会丢失。
      </div>

      {/* Video + Cover Preview */}
      {result && (
        <>
          {/* Video Preview */}
          {result.videoUrl && (
            <div style={{ marginBottom: "1.5rem" }}>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem", color: "#1e293b" }}>
                视频预览
              </div>
              <div
                style={{
                  background: "#1e293b",
                  borderRadius: "10px",
                  maxHeight: "450px",
                  overflow: "hidden",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <video
                  controls
                  src={result.videoUrl}
                  style={{ maxWidth: "100%", maxHeight: "450px", objectFit: "contain" }}
                />
              </div>
              <div style={{ marginTop: "0.6rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                <a
                  href={result.videoUrl}
                  download
                  style={{
                    background: "#3b82f6",
                    color: "white",
                    textDecoration: "none",
                    borderRadius: "6px",
                    padding: "0.35rem 0.9rem",
                    fontSize: "0.82rem",
                  }}
                >
                  下载视频
                </a>
                {result.coverUrl && (
                  <a
                    href={result.coverUrl}
                    download
                    style={{
                      background: "#8b5cf6",
                      color: "white",
                      textDecoration: "none",
                      borderRadius: "6px",
                      padding: "0.35rem 0.9rem",
                      fontSize: "0.82rem",
                    }}
                  >
                    下载封面
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Cover only */}
          {result.coverUrl && !result.videoUrl && (
            <div style={{ marginBottom: "1.5rem" }}>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem", color: "#1e293b" }}>
                封面预览
              </div>
              <img
                src={result.coverUrl}
                alt="cover"
                style={{ maxWidth: "180px", maxHeight: "300px", borderRadius: "8px", objectFit: "contain" }}
              />
            </div>
          )}

          {/* Assets info */}
          {assets && (
            <div
              style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "0.75rem 1rem",
                marginBottom: "1.5rem",
                display: "flex",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              {assets.frameCount !== undefined && (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>帧数：</span>
                  <strong style={{ color: "#1e293b" }}>{String(assets.frameCount)}</strong>
                </div>
              )}
              {assets.fps !== undefined && (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>帧率：</span>
                  <strong style={{ color: "#1e293b" }}>{String(assets.fps)} fps</strong>
                </div>
              )}
              {assets.resolution !== undefined && (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>分辨率：</span>
                  <strong style={{ color: "#1e293b" }}>{String(assets.resolution)}</strong>
                </div>
              )}
              {assets.format !== undefined && (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>格式：</span>
                  <strong style={{ color: "#1e293b" }}>{String(assets.format)}</strong>
                </div>
              )}
              {assets.codec !== undefined && (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>编码：</span>
                  <strong style={{ color: "#1e293b" }}>{String(assets.codec)}</strong>
                </div>
              )}
              <div style={{ fontSize: "0.82rem" }}>
                <span style={{ color: "#94a3b8" }}>FFmpeg：</span>
                <strong style={{ color: assets.ffmpegSuccess ? "#10b981" : "#ef4444" }}>
                  {assets.ffmpegSuccess ? "成功" : "失败"}
                </strong>
              </div>
              <div style={{ fontSize: "0.82rem" }}>
                <span style={{ color: "#94a3b8" }}>Provider：</span>
                <strong style={{ color: "#1e293b" }}>{result.provider}</strong>
              </div>
              {assets.visualPreset ? (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>视觉模板：</span>
                  <strong style={{ color: "#8b5cf6" }}>{`${assets.visualPreset}`}</strong>
                </div>
              ) : null}
              {assets.templateVersion ? (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>模板版本：</span>
                  <strong style={{ color: "#1e293b" }}>{`${assets.templateVersion}`}</strong>
                </div>
              ) : null}
              {assets.transitionEnabled !== undefined ? (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>转场：</span>
                  <strong style={{ color: (assets.transitionEnabled as boolean) ? "#10b981" : "#94a3b8" }}>
                    {(assets.transitionEnabled as boolean) ? `${assets.transitionType || "Fade"}` : "无"}
                  </strong>
                </div>
              ) : null}
              {assets.highlightTerms && Array.isArray(assets.highlightTerms) && (assets.highlightTerms as unknown[]).length > 0 ? (
                <div style={{ fontSize: "0.82rem" }}>
                  <span style={{ color: "#94a3b8" }}>高亮词：</span>
                  <strong style={{ color: "#f59e0b" }}>
                    {(assets.highlightTerms as string[]).slice(0, 3).join(" / ")}
                    {(assets.highlightTerms as string[]).length > 3 ? " ..." : ""}
                  </strong>
                </div>
              ) : null}
            </div>
          )}

          {/* All Artifacts */}
          {result.productionSteps.length > 0 && (() => {
            const allArtifacts = result.productionSteps.flatMap((s) => s.artifacts);
            const uniqueById = allArtifacts.filter(
              (a, i, arr) => arr.findIndex((b) => b.id === a.id) === i,
            );
            if (uniqueById.length === 0) return null;
            return (
              <div style={{ marginBottom: "1.5rem" }}>
                <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem", color: "#1e293b" }}>
                  产物清单（{uniqueById.length}）
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                  {uniqueById.map((art) => (
                    <ArtifactViewer key={art.id} artifact={art} />
                  ))}
                </div>
              </div>
            );
          })()}

          {/* Experiment Summary */}
          {result && (
            <ExperimentSummaryPanel result={result} evaluation={evaluation} />
          )}

          {/* Production Steps */}
          {result.productionSteps.length > 0 && (
            <ProductionStepsTimeline steps={result.productionSteps} />
          )}

          {/* Evaluation Panel */}
          {experiment.status === "succeeded" && (
            <EvaluationPanel
              experimentId={experiment.id}
              existingEvaluation={evaluation}
              apiBase={API_BASE}
              onEvaluationSaved={(eval_) => setEvaluation(eval_)}
            />
          )}
        </>
      )}
    </div>
  );
}
