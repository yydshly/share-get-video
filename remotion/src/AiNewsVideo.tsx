// AiNewsVideo.tsx - V0.3.8.1 timeline-style Remotion template
// Portrait 9:16, 1080x1920
// Pages: Compact cover with keypoint list, keypoint cards, summary
// V0.3.6-a2: Added keyword/number highlighting in keypoint cards

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Sequence,
} from "remotion";
import type { AiNewsVideoProps, KeyPoint, RemotionStyle } from "./data";

// ─── Highlight Helper (V0.3.6-b1) ────────────────────────────────────────────
/** Auto-extract numbers, percentages, and key terms from text (fallback). */
function autoExtractHighlights(text: string): string[] {
  const highlights: string[] = [];
  // Match percentages: 88.9%, 72%, 39% etc.
  const pctRegex = /\d+\.?\d*%/g;
  // Match numbers with units: 10倍, 5x, 100万, 5620亿 etc.
  const numUnitRegex = /\d+\.?\d*(?:倍|x|万|亿|千|[kmgKMG])/g;
  // Match standalone numbers: 39, 88.9, etc. (but not years like 2024)
  const numRegex = /(?<!\d)\d{1,3}\.\d+|(?<!\d)\d{2,3}(?!\d)/g;

  const matches = text.matchAll(new RegExp(`(?:${pctRegex.source})|(?:${numUnitRegex.source})|(?:${numRegex.source})`, 'g'));
  for (const m of matches) {
    if (m[0] && !highlights.includes(m[0])) {
      highlights.push(m[0]);
    }
  }
  return highlights;
}

/**
 * Split text into segments with highlight markers.
 * V0.3.6-b1: priority — explicit emphasisTerms > auto-extract > none.
 */
function getHighlightedSegments(
  text: string,
  emphasisTerms?: string[],
): { text: string; highlight: boolean }[] {
  // Priority: explicit emphasisTerms > auto-extract
  const highlights = (emphasisTerms && emphasisTerms.length > 0)
    ? emphasisTerms
    : autoExtractHighlights(text);

  if (highlights.length === 0) return [{ text, highlight: false }];

  const pattern = new RegExp(`(${highlights.map(h => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'g');
  const parts = text.split(pattern);
  return parts
    .filter(p => p)
    .map(p => ({ text: p, highlight: highlights.includes(p) }));
}

/** Text segment with inline highlights.
 * V0.3.6-b1: emphasisTerms from KeyPoint take priority over auto-extract.
 */
const HighlightedText: React.FC<{
  text: string;
  style: React.CSSProperties;
  highlightColor?: string;
  emphasisTerms?: string[];
}> = ({ text, style, highlightColor = C.highlight, emphasisTerms }) => {
  const segments = getHighlightedSegments(text, emphasisTerms);
  return (
    <span style={style}>
      {segments.map((seg, i) =>
        seg.highlight ? (
          <span key={i} style={{ color: highlightColor, fontWeight: 700 }}>{seg.text}</span>
        ) : (
          <span key={i}>{seg.text}</span>
        )
      )}
    </span>
  );
};

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

// ─── Tone presets (主题自适应：按语义配色/图标) ──────────────────────────────
const TONE_STYLES: Record<string, { accent: string; highlight: string; glyph: string }> = {
  positive: { accent: "#22c55e", highlight: "#86efac", glyph: "↑" },
  negative: { accent: "#f59e0b", highlight: "#fcd34d", glyph: "!" },
  neutral: { accent: "#3b82f6", highlight: "#60a5fa", glyph: "✦" },
};

// ─── Data motion helpers (count-up number + growing bar) ─────────────────────
// Remotion 特有：把百分比做成"数字滚动 + 数据条生长"，这是静态卡(Pillow)做不到的动画。
function findPrimaryStat(kp: KeyPoint): { value: number; suffix: string } | null {
  const sources = [...(kp.emphasisTerms ?? []), kp.body ?? "", kp.title ?? ""];
  for (const s of sources) {
    const m = String(s).match(/(\d+(?:\.\d+)?)\s*%/);
    if (m) return { value: parseFloat(m[1]), suffix: "%" };
  }
  return null;
}

const CountUpNumber: React.FC<{
  value: number; suffix?: string; startFrame?: number; durationFrames?: number; decimals?: number; style?: React.CSSProperties;
}> = ({ value, suffix = "", startFrame = 18, durationFrames = 26, decimals = 0, style }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
  return <span style={style}>{(value * eased).toFixed(decimals)}{suffix}</span>;
};

const DataBar: React.FC<{ pct: number; startFrame?: number; durationFrames?: number; fromColor?: string; toColor?: string }> = ({ pct, startFrame = 18, durationFrames = 30, fromColor = C.accent, toColor = C.highlight }) => {
  const frame = useCurrentFrame();
  const w = interpolate(frame, [startFrame, startFrame + durationFrames], [0, Math.min(100, Math.max(0, pct))], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ width: "100%", height: 16, background: C.surface, borderRadius: 999, overflow: "hidden", marginTop: 10, border: `1px solid ${C.border}` }}>
      <div style={{ width: `${w}%`, height: "100%", background: `linear-gradient(90deg, ${fromColor}, ${toColor})`, borderRadius: 999 }} />
    </div>
  );
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
          fontSize: 64,
          fontWeight: 800,
          color: C.textPrimary,
          textAlign: "left",
          margin: 0,
          marginTop: 24,
          lineHeight: 1.15,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          textShadow: "0 0 80px rgba(59, 130, 246, 0.4)",
        }}
      >
        {title}
      </h1>

      {/* Subtitle */}
      {subtitle && (
        <p
          style={{
            fontSize: 30,
            color: C.textSecondary,
            textAlign: "left",
            marginTop: 16,
            marginBottom: 0,
            opacity: subtitleOpacity,
            lineHeight: 1.4,
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
                marginBottom: 20,
                opacity: itemOpacity,
                transform: `translateX(${itemX}px)`,
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 12,
                  background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 18,
                  fontWeight: 800,
                  color: C.textPrimary,
                  flexShrink: 0,
                }}
              >
                {String(i + 1).padStart(2, "0")}
              </div>
              <div
                style={{
                  fontSize: 26,
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
          fontSize: 20,
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
  vstyle?: RemotionStyle;
}> = ({ kp, index, startFrame, totalDuration, fps, vstyle }) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);

  // 主题自适应 + 可调样式（显式 vstyle 优先，否则按该条 tone 配色/图标）
  const tonePreset = TONE_STYLES[(kp.tone || "neutral")] || TONE_STYLES.neutral;
  const accent = vstyle?.accentColor || tonePreset.accent;
  const hl = vstyle?.highlightColor || tonePreset.highlight;
  const fs = vstyle?.fontScale || 1;
  const showIcon = vstyle?.showIcon ?? true;
  const iconGlyph = tonePreset.glyph;

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
            background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
            opacity: 0.3 + borderPulse * 0.4,
          }}
        />

        {/* Header row: big index + category tag + optional icon */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 36 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 72,
              height: 72,
              borderRadius: 18,
              background: `linear-gradient(135deg, ${accent}, ${C.accent2})`,
              fontSize: 32,
              fontWeight: 800,
              color: C.textPrimary,
              opacity: indexOpacity,
              boxShadow: `0 0 30px ${accent}60`,
            }}
          >
            {String(index + 1).padStart(2, "0")}
          </div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: accent,
              background: `${accent}26`,
              border: `1px solid ${accent}66`,
              borderRadius: 999,
              padding: "6px 16px",
              letterSpacing: 1.5,
              textTransform: "uppercase",
              opacity: indexOpacity,
            }}
          >
            KEY POINT
          </div>
          {showIcon && (
            <div
              style={{
                marginLeft: "auto",
                width: 48,
                height: 48,
                borderRadius: 12,
                background: `${accent}22`,
                border: `2px solid ${accent}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: accent,
                fontSize: 24,
                fontWeight: 900,
                opacity: indexOpacity,
              }}
            >
              {iconGlyph}
            </div>
          )}
        </div>

        {/* Title */}
        <h2
          style={{
            fontSize: Math.round(44 * fs),
            fontWeight: 800,
            color: C.textPrimary,
            margin: 0,
            marginBottom: 28,
            lineHeight: 1.3,
            opacity: titleOpacity,
            textShadow: "0 0 40px rgba(59, 130, 246, 0.25)",
          }}
        >
          <HighlightedText text={kp.title} style={{}} highlightColor={hl} emphasisTerms={kp.emphasisTerms} />
        </h2>

        {/* Decorative separator */}
        <div
          style={{
            width: 80,
            height: 3,
            background: `linear-gradient(90deg, ${accent}, ${C.accent2})`,
            borderRadius: 2,
            marginBottom: 28,
            opacity: titleOpacity,
          }}
        />

        {/* Body */}
        <p
          style={{
            fontSize: Math.round(32 * fs),
            color: C.textSecondary,
            margin: 0,
            marginBottom: 28,
            lineHeight: 1.7,
            opacity: bodyOpacity,
          }}
        >
          <HighlightedText text={kp.body} style={{}} highlightColor={hl} emphasisTerms={kp.emphasisTerms} />
        </p>

        {/* Data animation: count-up + growing bar for the primary percentage */}
        {(() => {
          const stat = findPrimaryStat(kp);
          if (!stat) return null;
          return (
            <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
              <CountUpNumber
                value={stat.value}
                suffix={stat.suffix}
                decimals={stat.value % 1 === 0 ? 0 : 1}
                style={{ fontSize: 80, fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}
              />
              <DataBar pct={stat.value} fromColor={accent} toColor={hl} />
            </div>
          );
        })()}

        {/* Source footer */}
        {kp.source && (
          <div
            style={{
              marginTop: 32,
              paddingTop: 20,
              borderTop: `1px solid ${C.border}`,
              fontSize: 20,
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
            fontSize: 48,
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
                  marginBottom: 20,
                  opacity: itemOpacity,
                  transform: `translateX(${itemX}px)`,
                }}
              >
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
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
                <div>
                  <div
                    style={{
                      fontSize: 26,
                      fontWeight: 700,
                      color: C.textPrimary,
                      marginBottom: 6,
                    }}
                  >
                    {kp.title}
                  </div>
                  <div style={{ fontSize: 22, color: C.textMuted, lineHeight: 1.5 }}>
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
  style,
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
            vstyle={style}
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
