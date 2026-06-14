// ArtifactViewer - Reusable artifact display component

import type { VideoProductionArtifact } from "../types";

const ARTIFACT_TYPE_LABELS: Record<string, string> = {
  video_output: "视频输出",
  cover_image: "封面图",
  frame_image: "帧图片",
  manifest: "实验清单",
  normalized_content: "结构化内容",
  key_points: "关键点",
  video_strategy: "视频策略",
  script: "脚本",
  storyboard: "分镜",
  subtitle_plan: "字幕方案",
  voiceover_plan: "配音方案",
  asset_plan: "资产方案",
  render_plan: "渲染方案",
  mock_video: "模拟视频",
  evaluation: "评估结果",
};

interface Props {
  artifact: VideoProductionArtifact;
}

export default function ArtifactViewer({ artifact }: Props) {
  const url = (artifact.payload?.url as string) || "";
  const path = (artifact.payload?.path as string) || "";
  const isVideo = artifact.type === "video_output";
  const isImage = artifact.type === "cover_image" || artifact.type === "frame_image";
  const isManifest = artifact.type === "manifest";
  const hasMediaPreview = Boolean(url && (isVideo || isImage));
  const hasOnlyPath = Boolean(path && !url);

  return (
    <div
      style={{
        background: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "6px",
        padding: "0.6rem",
        marginBottom: "0.4rem",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem" }}>
        <span
          style={{
            fontSize: "0.7rem",
            fontWeight: 600,
            background: "#3b82f6",
            color: "white",
            borderRadius: "4px",
            padding: "0.1rem 0.4rem",
          }}
        >
          {ARTIFACT_TYPE_LABELS[artifact.type] || artifact.type}
        </span>
        <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1e40af" }}>
          {artifact.title}
        </span>
      </div>

      {/* Summary */}
      <div style={{ fontSize: "0.78rem", color: "#475569", marginBottom: hasMediaPreview ? "0.3rem" : 0 }}>
        {artifact.summary}
      </div>

      {/* Video preview — only from url */}
      {url && isVideo && (
        <div style={{ marginTop: "0.4rem" }}>
          <video
            src={url}
            controls
            style={{ maxWidth: "100%", maxHeight: "200px", borderRadius: "6px" }}
          />
          <div style={{ marginTop: "0.3rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <a href={url} download style={{ fontSize: "0.78rem", color: "#3b82f6" }}>
              下载视频
            </a>
          </div>
        </div>
      )}

      {/* Image preview — only from url */}
      {url && isImage && (
        <div style={{ marginTop: "0.4rem" }}>
          <img
            src={url}
            alt={artifact.title}
            style={{ maxWidth: "120px", maxHeight: "160px", borderRadius: "6px", objectFit: "contain" }}
          />
          <div style={{ marginTop: "0.3rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <a href={url} download style={{ fontSize: "0.78rem", color: "#3b82f6" }}>
              下载图片
            </a>
          </div>
        </div>
      )}

      {/* Manifest download */}
      {url && isManifest && (
        <div style={{ marginTop: "0.4rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <a
            href={url}
            download
            style={{
              fontSize: "0.78rem",
              background: "#8b5cf6",
              color: "white",
              textDecoration: "none",
              borderRadius: "6px",
              padding: "0.2rem 0.6rem",
            }}
          >
            下载 manifest.json
          </a>
        </div>
      )}

      {/* Has url but not media — show it as info */}
      {url && !isVideo && !isImage && !isManifest && (
        <div style={{ marginTop: "0.3rem", fontSize: "0.72rem", color: "#93c5fd", fontFamily: "monospace" }}>
          {url}
        </div>
      )}

      {/* Has only path (no url) — show warning */}
      {hasOnlyPath && (
        <div style={{ marginTop: "0.3rem", fontSize: "0.72rem", color: "#f59e0b" }}>
          仅有本地路径，无法浏览器预览：<span style={{ fontFamily: "monospace" }}>{path}</span>
        </div>
      )}
    </div>
  );
}
