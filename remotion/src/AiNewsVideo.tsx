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

// ─── Key Point Card (V0.3.8.2: bigger card, denser, full-screen info) ───────
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
        padding: "60px 40px",
      }}
    >
      {/* Card container - 80% width of 1080 = 864px */}
      <div
        style={{
          width: "82%",
          maxWidth: 880,
          background: C.card,
          borderRadius: 24,
          border: `2px solid ${C.border}`,
          padding: "50px 44px",
          position: "relative",
          opacity: cardOpacity,
          transform: `translateY(${cardY}px)`,
          boxShadow: `0 0 80px ${C.glow}, 0 24px 60px rgba(0,0,0,0.6)`,
          minHeight: 1100,
        }}
      >
        {/* Accent glow */}
        <div
          style={{
            position: "absolute",
            top: -2,
            left: "10%",
            right: "10%",
            height: 3,
            background: `linear-gradient(90deg, transparent, ${C.accent}, transparent)`,
            opacity: 0.3 + borderPulse * 0.4,
          }}
        />

        {/* Header row: big index + category tag */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 36 }}>
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
              opacity: indexOpacity,
              boxShadow: `0 0 20px ${C.accent}40`,
            }}
          >
            {String(index + 1).padStart(2, "0")}
          </div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: C.accent,
              background: "rgba(59, 130, 246, 0.15)",
              border: `1px solid rgba(59, 130, 246, 0.4)`,
              borderRadius: 999,
              padding: "6px 16px",
              letterSpacing: 1.5,
              textTransform: "uppercase",
              opacity: indexOpacity,
            }}
          >
            KEY POINT
          </div>
        </div>

        {/* Title - balanced 32px, can span 3-4 lines */}
        <h2
          style={{
            fontSize: 32,
            fontWeight: 800,
            color: C.textPrimary,
            margin: 0,
            marginBottom: 28,
            lineHeight: 1.3,
            opacity: titleOpacity,
            textShadow: "0 0 30px rgba(59, 130, 246, 0.2)",
          }}
        >
          {kp.title}
        </h2>

        {/* Decorative separator */}
        <div
          style={{
            width: 80,
            height: 3,
            background: `linear-gradient(90deg, ${C.accent}, ${C.accent2})`,
            borderRadius: 2,
            marginBottom: 28,
            opacity: titleOpacity,
          }}
        />

        {/* Body - 24px, multi-line, fills the card */}
        <p
          style={{
            fontSize: 24,
            color: C.textSecondary,
            margin: 0,
            marginBottom: 24,
            lineHeight: 1.6,
            opacity: bodyOpacity,
          }}
        >
          {kp.body}
        </p>

        {/* Source footer */}
        {kp.source && (
          <div
            style={{
              marginTop: 32,
              paddingTop: 20,
              borderTop: `1px solid ${C.border}`,
              fontSize: 18,
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
  segmentDurations,
}) => {
  const { fps } = useVideoConfig();

  // 每段时长：优先使用与旁白对齐的 segmentDurations，否则回退固定时长
  const FIXED_COVER = 75;   // 2.5s
  const FIXED_CARD = 135;   // 4.5s
  const FIXED_SUMMARY = 60; // 2s

  const useAligned =
    !!segmentDurations &&
    Array.isArray(segmentDurations.cardSecs) &&
    segmentDurations.cardSecs.length === keyPoints.length;

  const coverFrames = useAligned
    ? Math.max(30, Math.round(segmentDurations!.coverSec * fps))
    : FIXED_COVER;
  const cardFramesArr = useAligned
    ? segmentDurations!.cardSecs.map((s) => Math.max(45, Math.round(s * fps)))
    : keyPoints.map(() => FIXED_CARD);
  const summaryFrames = useAligned
    ? Math.max(30, Math.round(segmentDurations!.summarySec * fps))
    : FIXED_SUMMARY;

  // 累计起点
  const cardStarts: number[] = [];
  let acc = coverFrames;
  for (const f of cardFramesArr) {
    cardStarts.push(acc);
    acc += f;
  }
  const summaryStart = acc;

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* Cover - now shows 3-point timeline */}
      <Sequence from={0} durationInFrames={coverFrames}>
        <CoverPage
          title={title}
          subtitle={subtitle}
          keyPoints={keyPoints}
          duration={coverFrames}
        />
      </Sequence>

      {/* Key Point Cards */}
      {keyPoints.map((kp, i) => (
        <Sequence
          key={i}
          from={cardStarts[i]}
          durationInFrames={cardFramesArr[i]}
        >
          <KeyPointCard
            kp={kp}
            index={i}
            startFrame={0}
            totalDuration={cardFramesArr[i]}
            fps={fps}
          />
        </Sequence>
      ))}

      {/* Summary */}
      <Sequence from={summaryStart} durationInFrames={summaryFrames}>
        <SummaryPage title={title} keyPoints={keyPoints} />
      </Sequence>
    </AbsoluteFill>
  );
};

export default AiNewsVideo;
