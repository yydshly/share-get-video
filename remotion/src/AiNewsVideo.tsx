// AiNewsVideo.tsx - V0.3.8 timeline-style Remotion template
// Portrait 9:16, 1080x1920
// Pages: Compact cover with keypoint list, keypoint cards, summary

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

// ─── Cover Page (V0.3.8: compact, includes 3-point preview list) ─────────────
const CoverPage: React.FC<{
  title: string;
  subtitle?: string;
  keyPoints: KeyPoint[];
  duration: number;
}> = ({ title, subtitle, keyPoints, duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [0, 15], [30, 0], { extrapolateRight: "clamp" });
  const subtitleOpacity = interpolate(frame, [10, 25], [0, 1], { extrapolateRight: "clamp" });
  const listOpacity = interpolate(frame, [20, 40], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        justifyContent: "flex-start",
        alignItems: "stretch",
        padding: "60px 50px",
      }}
    >
      {/* Glow accent */}
      <div
        style={{
          position: "absolute",
          top: "10%",
          left: "30%",
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: C.glow,
          filter: "blur(100px)",
        }}
      />

      {/* Top label */}
      <div
        style={{
          fontSize: 20,
          color: C.accent,
          fontWeight: 700,
          letterSpacing: 4,
          textTransform: "uppercase",
          opacity: subtitleOpacity,
        }}
      >
        AI 前沿 · 速览
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: 56,
          fontWeight: 800,
          color: C.textPrimary,
          textAlign: "left",
          margin: 0,
          marginTop: 24,
          lineHeight: 1.15,
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
            fontSize: 26,
            color: C.textSecondary,
            textAlign: "left",
            marginTop: 12,
            marginBottom: 0,
            opacity: subtitleOpacity,
          }}
        >
          {subtitle}
        </p>
      )}

      {/* Timeline preview of 3 keypoints */}
      <div style={{ marginTop: 60, opacity: listOpacity }}>
        {keyPoints.slice(0, 3).map((kp, i) => {
          const itemOpacity = interpolate(frame, [25 + i * 5, 35 + i * 5], [0, 1], {
            extrapolateRight: "clamp",
          });
          const itemX = interpolate(frame, [25 + i * 5, 35 + i * 5], [-20, 0], {
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                marginBottom: 18,
                opacity: itemOpacity,
                transform: `translateX(${itemX}px)`,
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 16,
                  fontWeight: 800,
                  color: C.textPrimary,
                  flexShrink: 0,
                }}
              >
                {String(i + 1).padStart(2, "0")}
              </div>
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 600,
                  color: C.textPrimary,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {kp.title}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom info */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: 50,
          right: 50,
          fontSize: 18,
          color: C.textMuted,
          opacity: interpolate(frame, [30, 50], [0, 1], { extrapolateRight: "clamp" }),
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: C.accent,
            boxShadow: `0 0 8px ${C.accent}`,
          }}
        />
        <span>{keyPoints.length} 条要点 · 今日速览</span>
      </div>
    </AbsoluteFill>
  );
};

// ─── Key Point Card (V0.3.8: smaller title, source line, tag pill) ───────────
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
        padding: "70px 50px",
      }}
    >
      {/* Card container */}
      <div
        style={{
          width: "100%",
          maxWidth: 900,
          background: C.card,
          borderRadius: 20,
          border: `1px solid ${C.border}`,
          padding: "40px 36px",
          position: "relative",
          opacity: cardOpacity,
          transform: `translateY(${cardY}px)`,
          boxShadow: `0 0 60px ${C.glow}, 0 16px 50px rgba(0,0,0,0.5)`,
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

        {/* Header row: index badge + tag pill */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 48,
              height: 48,
              borderRadius: 12,
              background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
              fontSize: 20,
              fontWeight: 800,
              color: C.textPrimary,
              opacity: indexOpacity,
            }}
          >
            {String(index + 1).padStart(2, "0")}
          </div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: C.accent,
              background: "rgba(59, 130, 246, 0.15)",
              border: `1px solid rgba(59, 130, 246, 0.3)`,
              borderRadius: 999,
              padding: "4px 12px",
              letterSpacing: 1,
              textTransform: "uppercase",
              opacity: indexOpacity,
            }}
          >
            KEY POINT
          </div>
        </div>

        {/* Title - reduced from 72 to 40 */}
        <h2
          style={{
            fontSize: 40,
            fontWeight: 800,
            color: C.textPrimary,
            margin: 0,
            marginBottom: 20,
            lineHeight: 1.2,
            opacity: titleOpacity,
            textShadow: "0 0 30px rgba(59, 130, 246, 0.2)",
          }}
        >
          {kp.title}
        </h2>

        {/* Body - reduced from 38 to 24 */}
        <p
          style={{
            fontSize: 24,
            color: C.textSecondary,
            margin: 0,
            marginBottom: 16,
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
              fontSize: 16,
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

// ─── Summary Page (V0.3.8: timeline recap) ───────────────────────────────────
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
        padding: "60px 50px",
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
            fontSize: 40,
            fontWeight: 800,
            color: C.textPrimary,
            margin: 0,
            marginBottom: 32,
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
          }}
        >
          今日回顾
        </h2>

        <div style={{ opacity: listOpacity }}>
          {keyPoints.map((kp, i) => {
            const itemOpacity = interpolate(frame, [15 + i * 8, 25 + i * 8], [0, 1], {
              extrapolateRight: "clamp",
            });
            const itemX = interpolate(frame, [15 + i * 8, 25 + i * 8], [-20, 0], {
              extrapolateRight: "clamp",
            });
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 16,
                  marginBottom: 18,
                  opacity: itemOpacity,
                  transform: `translateX(${itemX}px)`,
                }}
              >
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 8,
                    background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 14,
                    fontWeight: 800,
                    color: C.textPrimary,
                    flexShrink: 0,
                  }}
                >
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 22,
                      fontWeight: 700,
                      color: C.textPrimary,
                      marginBottom: 4,
                    }}
                  >
                    {kp.title}
                  </div>
                  <div style={{ fontSize: 18, color: C.textMuted, lineHeight: 1.4 }}>
                    {kp.body}
                  </div>
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
  // Cover: 0 → 120 frames (~4s) — extended to show 3-point preview
  // Each KeyPoint card: 120 → 120 + 5*150 = 870 frames (~5s each, 3 cards = 15s)
  // Summary: last 150 frames (~5s)
  const COVER_DURATION = 120; // 4s
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
      {/* Cover - now shows 3-point timeline */}
      <Sequence from={0} durationInFrames={COVER_DURATION}>
        <CoverPage
          title={title}
          subtitle={subtitle}
          keyPoints={keyPoints}
          duration={COVER_DURATION}
        />
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
