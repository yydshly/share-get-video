// AiNewsVideo.tsx - V0.3.1 minimum verification Remotion template
// Portrait 9:16, 1080x1920
// Pages: Cover, KeyPoint cards, Summary

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Sequence,
} from "remotion";
import type { AiNewsVideoProps, KeyPoint } from "./data";

// ─── Colors (ai_frontier_dark preset) ───────────────────────────────────────
const C = {
  bg: "#0a0e1a",
  surface: "#111827",
  card: "#1a2236",
  accent: "#3b82f6",
  accent2: "#8b5cf6",
  highlight: "#f59e0b",
  textPrimary: "#f8fafc",
  textSecondary: "#94a3b8",
  textMuted: "#64748b",
  border: "#1e293b",
  glow: "rgba(59, 130, 246, 0.15)",
};

// ─── Cover Page ───────────────────────────────────────────────────────────────
const CoverPage: React.FC<{ title: string; subtitle?: string; duration: number }> = ({
  title,
  subtitle,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [0, 15], [30, 0], { extrapolateRight: "clamp" });
  const subtitleOpacity = interpolate(frame, [10, 25], [0, 1], { extrapolateRight: "clamp" });
  const lineOpacity = interpolate(frame, [15, 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        justifyContent: "center",
        alignItems: "center",
        padding: "80px 60px",
      }}
    >
      {/* Glow accent */}
      <div
        style={{
          position: "absolute",
          top: "15%",
          left: "50%",
          transform: "translateX(-50%)",
          width: 400,
          height: 400,
          borderRadius: "50%",
          background: C.glow,
          filter: "blur(80px)",
        }}
      />

      {/* Top label */}
      <div
        style={{
          position: "absolute",
          top: 60,
          fontSize: 22,
          color: C.accent,
          fontWeight: 700,
          letterSpacing: 4,
          textTransform: "uppercase",
          opacity: subtitleOpacity,
        }}
      >
        AI 前沿
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: 96,
          fontWeight: 800,
          color: C.textPrimary,
          textAlign: "center",
          margin: 0,
          lineHeight: 1.1,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          textShadow: "0 0 60px rgba(59, 130, 246, 0.3)",
        }}
      >
        {title}
      </h1>

      {/* Subtitle */}
      {subtitle && (
        <p
          style={{
            fontSize: 36,
            color: C.textSecondary,
            textAlign: "center",
            marginTop: 24,
            opacity: subtitleOpacity,
          }}
        >
          {subtitle}
        </p>
      )}

      {/* Decorative line */}
      <div
        style={{
          width: 120,
          height: 4,
          background: `linear-gradient(90deg, ${C.accent}, ${C.accent2})`,
          borderRadius: 2,
          marginTop: 48,
          opacity: lineOpacity,
        }}
      />

      {/* Bottom info */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          fontSize: 24,
          color: C.textMuted,
          opacity: interpolate(frame, [20, 35], [0, 1], { extrapolateRight: "clamp" }),
        }}
      >
        AI 资讯共享视频 · V0.3.1
      </div>
    </AbsoluteFill>
  );
};

// ─── Key Point Card ──────────────────────────────────────────────────────────
const KeyPointCard: React.FC<{
  kp: KeyPoint;
  index: number;
  startFrame: number;
  totalDuration: number;
  fps: number;
}> = ({ kp, index, startFrame, totalDuration, fps }) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);

  const cardOpacity = interpolate(localFrame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const cardY = interpolate(localFrame, [0, 12], [40, 0], { extrapolateRight: "clamp" });
  const indexOpacity = interpolate(localFrame, [5, 15], [0, 1], { extrapolateRight: "clamp" });
  const titleOpacity = interpolate(localFrame, [8, 20], [0, 1], { extrapolateRight: "clamp" });
  const bodyOpacity = interpolate(localFrame, [15, 27], [0, 1], { extrapolateRight: "clamp" });
  const sourceOpacity = interpolate(localFrame, [20, 32], [0, 1], { extrapolateRight: "clamp" });

  // Subtle pulse on the card border
  const borderPulse = interpolate(
    localFrame,
    [0, 30, 60],
    [0, 1, 0],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        justifyContent: "center",
        alignItems: "center",
        padding: "80px 60px",
      }}
    >
      {/* Card container */}
      <div
        style={{
          width: "100%",
          maxWidth: 900,
          background: C.card,
          borderRadius: 24,
          border: `1px solid ${C.border}`,
          padding: "64px 56px",
          position: "relative",
          opacity: cardOpacity,
          transform: `translateY(${cardY}px)`,
          boxShadow: `0 0 80px ${C.glow}, 0 20px 60px rgba(0,0,0,0.5)`,
        }}
      >
        {/* Accent glow */}
        <div
          style={{
            position: "absolute",
            top: -1,
            left: "10%",
            right: "10%",
            height: 2,
            background: `linear-gradient(90deg, transparent, ${C.accent}, transparent)`,
            opacity: 0.3 + borderPulse * 0.4,
          }}
        />

        {/* Index badge */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 64,
            height: 64,
            borderRadius: 16,
            background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
            fontSize: 28,
            fontWeight: 800,
            color: C.textPrimary,
            marginBottom: 32,
            opacity: indexOpacity,
          }}
        >
          {String(index + 1).padStart(2, "0")}
        </div>

        {/* Title */}
        <h2
          style={{
            fontSize: 72,
            fontWeight: 800,
            color: C.textPrimary,
            margin: 0,
            marginBottom: 28,
            lineHeight: 1.15,
            opacity: titleOpacity,
            textShadow: "0 0 40px rgba(59, 130, 246, 0.2)",
          }}
        >
          {kp.title}
        </h2>

        {/* Body */}
        <p
          style={{
            fontSize: 38,
            color: C.textSecondary,
            margin: 0,
            marginBottom: 24,
            lineHeight: 1.5,
            opacity: bodyOpacity,
          }}
        >
          {kp.body}
        </p>

        {/* Source */}
        {kp.source && (
          <div
            style={{
              fontSize: 24,
              color: C.textMuted,
              opacity: sourceOpacity,
            }}
          >
            来源：{kp.source}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ─── Summary Page ─────────────────────────────────────────────────────────────
const SummaryPage: React.FC<{ title: string; keyPoints: KeyPoint[] }> = ({
  title,
  keyPoints,
}) => {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [0, 15], [30, 0], { extrapolateRight: "clamp" });
  const listOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        justifyContent: "center",
        alignItems: "center",
        padding: "80px 60px",
      }}
    >
      {/* Glow */}
      <div
        style={{
          position: "absolute",
          bottom: "20%",
          right: "10%",
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "rgba(139, 92, 246, 0.1)",
          filter: "blur(100px)",
        }}
      />

      <div style={{ maxWidth: 900, width: "100%" }}>
        <h2
          style={{
            fontSize: 80,
            fontWeight: 800,
            color: C.textPrimary,
            margin: 0,
            marginBottom: 48,
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
          }}
        >
          {title}
        </h2>

        <div style={{ opacity: listOpacity }}>
          {keyPoints.map((kp, i) => {
            const itemOpacity = interpolate(frame, [15 + i * 8, 25 + i * 8], [0, 1], {
              extrapolateRight: "clamp",
            });
            const itemY = interpolate(frame, [15 + i * 8, 25 + i * 8], [20, 0], {
              extrapolateRight: "clamp",
            });
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 20,
                  marginBottom: 24,
                  opacity: itemOpacity,
                  transform: `translateY(${itemY}px)`,
                }}
              >
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: "50%",
                    background: C.accent,
                    marginTop: 14,
                    flexShrink: 0,
                    boxShadow: `0 0 12px ${C.accent}`,
                  }}
                />
                <div>
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: C.textPrimary,
                    }}
                  >
                    {kp.title}
                  </span>
                  <span style={{ fontSize: 28, color: C.textMuted }}>
                    {" "}
                    — {kp.body}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─── Main Video Component ────────────────────────────────────────────────────
export const AiNewsVideo: React.FC<AiNewsVideoProps> = ({
  title,
  subtitle,
  keyPoints,
  durationSec,
}) => {
  const { fps } = useVideoConfig();

  // Layout timing (in frames)
  // Cover: 0 → 90 frames (~3s)
  // Each KeyPoint card: 90 → 90 + 150 = 240 frames (~5s each)
  // Summary: last 150 frames (~5s)
  const COVER_DURATION = 90; // 3s
  const CARD_DURATION = 150; // 5s
  const SUMMARY_DURATION = 150; // 5s

  const cardStart = COVER_DURATION;
  const summaryStart = COVER_DURATION + keyPoints.length * CARD_DURATION;

  const totalFrames = Math.max(
    summaryStart + SUMMARY_DURATION,
    fps * durationSec
  );

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* Cover */}
      <Sequence from={0} durationInFrames={COVER_DURATION}>
        <CoverPage title={title} subtitle={subtitle} duration={COVER_DURATION} />
      </Sequence>

      {/* Key Point Cards */}
      {keyPoints.map((kp, i) => (
        <Sequence
          key={i}
          from={cardStart + i * CARD_DURATION}
          durationInFrames={CARD_DURATION}
        >
          <KeyPointCard
            kp={kp}
            index={i}
            startFrame={0}
            totalDuration={CARD_DURATION}
            fps={fps}
          />
        </Sequence>
      ))}

      {/* Summary */}
      <Sequence from={summaryStart} durationInFrames={SUMMARY_DURATION}>
        <SummaryPage title={title} keyPoints={keyPoints} />
      </Sequence>
    </AbsoluteFill>
  );
};

export default AiNewsVideo;
