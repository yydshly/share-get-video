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
import type { AiNewsVideoProps, KeyPoint, Metric, RemotionStyle, MotionIntensity, CoverStyle, OverviewStyle, MetricAnimation, TransitionStyle } from "./data";

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

// V0.3.9: Motion intensity scale mapping
const MOTION_SCALE: Record<MotionIntensity, number> = {
  low: 0.75,
  medium: 1.0,
  high: 1.25,
};

// V0.3.9: Get effective motion scale from style props
function getMotionScale(vstyle?: RemotionStyle): number {
  const intensity = vstyle?.motionIntensity ?? "medium";
  return MOTION_SCALE[intensity] ?? 1.0;
}

// ─── Data motion helpers (count-up number + growing bar) ─────────────────────
// Remotion 特有：把百分比做成"数字滚动 + 数据条生长"，这是静态卡(Pillow)做不到的动画。
// V0.3.6-quality-p0: priority — kp.metrics > auto-extract from text
// V0.3.6-quality-p0-fix: non-% metrics show MetricValueCard only (no DataBar)
function findPrimaryStat(kp: KeyPoint): { value: number; suffix: string; label?: string } | null {
  // Priority 1: explicit kp.metrics
  if (kp.metrics && kp.metrics.length > 0) {
    const m = kp.metrics[0];
    const unit = m.unit ?? "";
    return { value: m.value, suffix: unit, label: m.label };
  }
  // Priority 2: auto-extract from text (legacy fallback)
  const sources = [...(kp.emphasisTerms ?? []), kp.body ?? "", kp.title ?? ""];
  for (const s of sources) {
    const match = String(s).match(/(\d+(?:\.\d+)?)\s*%/);
    if (match) return { value: parseFloat(match[1]), suffix: "%" };
  }
  return null;
}

// V0.3.6-quality-p0-fix: Static big-number card for non-% metrics (F1=0.84, 5620亿, etc.)
const MetricValueCard: React.FC<{
  label: string; value: number; unit: string;
  startFrame?: number; durationFrames?: number;
  style?: React.CSSProperties;
}> = ({ label, value, unit, startFrame = 18, durationFrames = 26, style }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const eased = 1 - Math.pow(1 - p, 3);
  const current = value * eased;
  const decimals = value % 1 === 0 ? 0 : 2;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ fontSize: 22, color: C.textMuted, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 80, fontWeight: 900, color: style?.color ?? C.highlight, textShadow: `0 0 36px ${style?.color ?? C.highlight}55`, lineHeight: 1 }}>
        {current.toFixed(decimals)}{unit}
      </div>
    </div>
  );
};

// V0.3.6-quality-p0: Range bar for percentage interval metrics (e.g. 57-77%)
// V0.3.6-quality-p0-fix: use appropriate decimals for non-0-100 ranges
const RangeBar: React.FC<{
  min: number; max: number; unit: string; startFrame?: number; durationFrames?: number;
  fromColor?: string; toColor?: string;
}> = ({ min, max, unit, startFrame = 18, durationFrames = 30, fromColor = C.accent, toColor = C.highlight }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const eased = 1 - Math.pow(1 - progress, 3);
  const filled = min + (max - min) * eased;
  // Decimals: percentages use 0; decimal ranges like 0.84-0.91 use 2
  const isPctRange = unit === "%" && max <= 100;
  const decimals = isPctRange ? 0 : 2;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ fontSize: 72, fontWeight: 900, color: toColor, textShadow: `0 0 36px ${toColor}55`, lineHeight: 1 }}>
        {filled.toFixed(decimals)}{unit}
      </div>
      {isPctRange ? (
        // Only show progress bar for percentage ranges (0-100 scale)
        <div style={{ width: "100%", height: 16, background: C.surface, borderRadius: 999, overflow: "hidden", border: `1px solid ${C.border}` }}>
          <div style={{ width: `${Math.min(100, Math.max(0, filled))}%`, height: "100%", background: `linear-gradient(90deg, ${fromColor}, ${toColor})`, borderRadius: 999 }} />
        </div>
      ) : null}
      <div style={{ fontSize: 20, color: C.textMuted }}>
        {min.toFixed(decimals)}{unit} – {max.toFixed(decimals)}{unit}
      </div>
    </div>
  );
};

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

// V0.3.9: Cover Page with style variants
const CoverPage: React.FC<{
  title: string;
  subtitle?: string;
  keyPoints: KeyPoint[];
  duration: number;
  coverStyle?: CoverStyle;
  vstyle?: RemotionStyle;
}> = ({ title, subtitle, keyPoints, duration, coverStyle = "editorial", vstyle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const motionScale = getMotionScale(vstyle);

  // Scale animation frames by motion intensity
  const scaleFrames = (frames: number[]) => frames.map(f => f / motionScale);

  const [titleFadeStart, titleFadeEnd] = scaleFrames([0, 15]);
  const [subtitleFadeStart, subtitleFadeEnd] = scaleFrames([10, 25]);
  const [listFadeStart, listFadeEnd] = scaleFrames([20, 40]);

  const titleOpacity = interpolate(frame, [titleFadeStart, titleFadeEnd], [0, 1], { extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [titleFadeStart, titleFadeEnd], [30, 0], { extrapolateRight: "clamp" });
  const subtitleOpacity = interpolate(frame, [subtitleFadeStart, subtitleFadeEnd], [0, 1], { extrapolateRight: "clamp" });
  const listOpacity = interpolate(frame, [listFadeStart, listFadeEnd], [0, 1], { extrapolateRight: "clamp" });

  const accent = vstyle?.accentColor || C.accent;
  const hl = vstyle?.highlightColor || C.highlight;

  // V0.3.9: Different cover styles
  if (coverStyle === "cinematic") {
    // Cinematic: stronger background, larger title, more dramatic lighting
    return (
      <AbsoluteFill
        style={{
          background: C.bg,
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 50px",
        }}
      >
        {/* Stronger glow layers */}
        <div style={{ position: "absolute", top: "5%", left: "20%", width: 700, height: 700, borderRadius: "50%", background: `radial-gradient(circle, ${accent}22 0%, transparent 70%)`, filter: "blur(120px)" }} />
        <div style={{ position: "absolute", bottom: "10%", right: "10%", width: 600, height: 600, borderRadius: "50%", background: `radial-gradient(circle, ${C.accent2}18 0%, transparent 70%)`, filter: "blur(100px)" }} />
        {/* Overlay gradient */}
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(10,14,26,0.3) 0%, rgba(10,14,26,0.8) 100%)" }} />

        <div style={{ position: "relative", zIndex: 1, textAlign: "center", maxWidth: 950 }}>
          {/* Top label */}
          <div style={{ fontSize: 22, color: accent, fontWeight: 700, letterSpacing: 6, textTransform: "uppercase", opacity: subtitleOpacity, marginBottom: 20 }}>
            AI 前沿 · 速览
          </div>

          {/* Large cinematic title */}
          <h1 style={{ fontSize: 80, fontWeight: 900, color: C.textPrimary, margin: 0, lineHeight: 1.1, opacity: titleOpacity, transform: `translateY(${titleY}px)`, textShadow: `0 0 120px ${accent}66` }}>
            {title}
          </h1>

          {/* Subtitle */}
          {subtitle && (
            <p style={{ fontSize: 32, color: C.textSecondary, marginTop: 24, opacity: subtitleOpacity, lineHeight: 1.5 }}>
              {subtitle}
            </p>
          )}

          {/* Keypoint preview - minimal */}
          <div style={{ marginTop: 50, opacity: listOpacity, display: "flex", justifyContent: "center", gap: 20 }}>
            {keyPoints.slice(0, 3).map((kp, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 36, height: 36, borderRadius: 10, background: `linear-gradient(135deg, ${accent}, ${C.accent2})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 800, color: C.textPrimary }}>
                  {String(i + 1).padStart(2, "0")}
                </div>
                <span style={{ fontSize: 22, fontWeight: 600, color: C.textPrimary }}>{kp.title}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom info */}
        <div style={{ position: "absolute", bottom: 40, left: 50, right: 50, fontSize: 20, color: C.textMuted, opacity: interpolate(frame, [30 / motionScale, 50 / motionScale], [0, 1], { extrapolateRight: "clamp" }), display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: accent, boxShadow: `0 0 8px ${accent}` }} />
          <span>{keyPoints.length} 条要点 · 今日速览</span>
        </div>
      </AbsoluteFill>
    );
  }

  if (coverStyle === "minimal") {
    // Minimal: less decoration, only essential title and minimal info
    return (
      <AbsoluteFill
        style={{
          background: C.bg,
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 80px",
        }}
      >
        <div style={{ maxWidth: 800, textAlign: "center" }}>
          {/* Title - clean and large */}
          <h1 style={{ fontSize: 72, fontWeight: 800, color: C.textPrimary, margin: 0, lineHeight: 1.15, opacity: titleOpacity, transform: `translateY(${titleY}px)` }}>
            {title}
          </h1>

          {/* Subtitle */}
          {subtitle && (
            <p style={{ fontSize: 28, color: C.textSecondary, marginTop: 20, opacity: subtitleOpacity, lineHeight: 1.4 }}>
              {subtitle}
            </p>
          )}
        </div>

        {/* Bottom - minimal indicator */}
        <div style={{ position: "absolute", bottom: 40, fontSize: 18, color: C.textMuted, opacity: interpolate(frame, [30 / motionScale, 50 / motionScale], [0, 1], { extrapolateRight: "clamp" }) }}>
          {keyPoints.length} 条要点
        </div>
      </AbsoluteFill>
    );
  }

  // Default: editorial style (original behavior)
  // editorial: current default news cover style with clear title, subtitle, and preview list
  // V0.5.6: 竖屏垂直居中内容块（原 flex-start 把标题/列表钉在顶部，下方大片空白）
  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        justifyContent: "center",
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
          color: accent,
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
          textShadow: `0 0 80px ${accent}66`,
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
          const [itemFadeStart, itemFadeEnd] = scaleFrames([25 + i * 5, 35 + i * 5]);
          const itemOpacity = interpolate(frame, [itemFadeStart, itemFadeEnd], [0, 1], {
            extrapolateRight: "clamp",
          });
          const itemX = interpolate(frame, [itemFadeStart, itemFadeEnd], [-20, 0], {
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
                  background: `linear-gradient(135deg, ${accent}, ${C.accent2})`,
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
          opacity: interpolate(frame, [30 / motionScale, 50 / motionScale], [0, 1], { extrapolateRight: "clamp" }),
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
            background: accent,
            boxShadow: `0 0 8px ${accent}`,
          }}
        />
        <span>{keyPoints.length} 条要点 · 今日速览</span>
      </div>
    </AbsoluteFill>
  );
};

// V0.3.9: Key Point Card with motionIntensity and metricAnimation support
const KeyPointCard: React.FC<{
  kp: KeyPoint;
  index: number;
  startFrame: number;
  totalDuration: number;
  fps: number;
  vstyle?: RemotionStyle;
  showDataViz?: boolean;
}> = ({ kp, index, startFrame, totalDuration, fps, vstyle, showDataViz = true }) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);

  // V0.3.9: Motion scaling
  const motionScale = getMotionScale(vstyle);
  const scaleFrames = (frames: number[]) => frames.map(f => f / motionScale);

  // 主题自适应 + 可调样式（显式 vstyle 优先，否则按该条 tone 配色/图标）
  const tonePreset = TONE_STYLES[(kp.tone || "neutral")] || TONE_STYLES.neutral;
  const accent = vstyle?.accentColor || tonePreset.accent;
  const hl = vstyle?.highlightColor || tonePreset.highlight;
  const fs = vstyle?.fontScale || 1;
  const showIcon = vstyle?.showIcon ?? true;
  const iconGlyph = tonePreset.glyph;
  const metricAnimation = vstyle?.metricAnimation ?? "countup_bar";

  // V0.3.9: Scale animation frames by motion intensity
  const [cardFadeStart, cardFadeEnd] = scaleFrames([0, 12]);
  const [indexFadeStart, indexFadeEnd] = scaleFrames([5, 15]);
  const [titleFadeStart, titleFadeEnd] = scaleFrames([8, 20]);
  const [bodyFadeStart, bodyFadeEnd] = scaleFrames([15, 27]);
  const [sourceFadeStart, sourceFadeEnd] = scaleFrames([20, 32]);

  const cardOpacity = interpolate(localFrame, [cardFadeStart, cardFadeEnd], [0, 1], { extrapolateRight: "clamp" });
  const cardY = interpolate(localFrame, [cardFadeStart, cardFadeEnd], [40, 0], { extrapolateRight: "clamp" });
  const indexOpacity = interpolate(localFrame, [indexFadeStart, indexFadeEnd], [0, 1], { extrapolateRight: "clamp" });
  const titleOpacity = interpolate(localFrame, [titleFadeStart, titleFadeEnd], [0, 1], { extrapolateRight: "clamp" });
  const bodyOpacity = interpolate(localFrame, [bodyFadeStart, bodyFadeEnd], [0, 1], { extrapolateRight: "clamp" });
  const sourceOpacity = interpolate(localFrame, [sourceFadeStart, sourceFadeEnd], [0, 1], { extrapolateRight: "clamp" });

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
          padding: "56px 44px",
          position: "relative",
          opacity: cardOpacity,
          transform: `translateY(${cardY}px)`,
          boxShadow: `0 0 80px ${C.glow}, 0 24px 60px rgba(0,0,0,0.6)`,
          // V0.5.5: 内容垂直居中 + 贴合内容的高度下限，消除卡片下半固定留白
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          minHeight: 760,
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
        {/* V0.3.6-quality-p0: kp.metrics takes priority */}
        {/* V0.3.6-quality-p0-fix: only % metrics show DataBar; non-% show MetricValueCard */}
        {/* V0.3.6-quality-p0-fix: showDataViz=false suppresses all metrics visualization */}
        {/* V0.3.9: metricAnimation controls animation style: countup_bar / countup_number / none */}
        {(() => {
          if (!showDataViz) return null;
          // Priority 1: kp.metrics with range (57-77%)
          if (kp.metrics && kp.metrics.length > 0) {
            const m = kp.metrics[0];
            const unit = m.unit ?? "";
            if (m.min !== undefined && m.max !== undefined) {
              // Range metric: RangeBar handles % vs non-% appropriately
              return (
                <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
                  <RangeBar
                    min={m.min}
                    max={m.max}
                    unit={unit}
                    fromColor={accent}
                    toColor={hl}
                  />
                </div>
              );
            }
            // Simple metric: % → count-up + bar or countup_number or none
            if (unit === "%") {
              if (metricAnimation === "none") {
                // Show final value directly without animation
                return (
                  <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
                    <div style={{ fontSize: 80, fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}>
                      {m.value}{unit}
                    </div>
                    {motionScale > 0.9 && motionScale < 1.1 && <DataBar pct={Math.min(100, Math.max(0, m.value))} fromColor={accent} toColor={hl} />}
                  </div>
                );
              }
              return (
                <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
                  <CountUpNumber
                    value={m.value}
                    suffix={unit}
                    decimals={m.value % 1 === 0 ? 0 : 1}
                    style={{ fontSize: 80, fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}
                  />
                  {metricAnimation === "countup_bar" && (
                    <DataBar pct={Math.min(100, Math.max(0, m.value))} fromColor={accent} toColor={hl} />
                  )}
                </div>
              );
            }
            // Non-% metric: just big number + unit + label (no bar)
            if (metricAnimation === "none") {
              return (
                <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
                  <MetricValueCard
                    label={m.label ?? unit}
                    value={m.value}
                    unit={unit}
                    style={{ color: hl }}
                  />
                </div>
              );
            }
            return (
              <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
                <MetricValueCard
                  label={m.label ?? unit}
                  value={m.value}
                  unit={unit}
                  style={{ color: hl }}
                />
              </div>
            );
          }
          // Priority 2: auto-extract fallback (always %, so show bar or number only)
          const stat = findPrimaryStat(kp);
          if (!stat) return null;
          if (metricAnimation === "none") {
            return (
              <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
                <div style={{ fontSize: 80, fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}>
                  {stat.value}{stat.suffix}
                </div>
              </div>
            );
          }
          return (
            <div style={{ marginTop: 6, marginBottom: 8, opacity: bodyOpacity }}>
              <CountUpNumber
                value={stat.value}
                suffix={stat.suffix}
                decimals={stat.value % 1 === 0 ? 0 : 1}
                style={{ fontSize: 80, fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}
              />
              {metricAnimation === "countup_bar" && (
                <DataBar pct={stat.value} fromColor={accent} toColor={hl} />
              )}
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

// V0.3.9: Summary Page with overviewStyle variants (timeline, grid, clean)
const SummaryPage: React.FC<{
  title: string;
  keyPoints: KeyPoint[];
  overviewStyle?: OverviewStyle;
  vstyle?: RemotionStyle;
}> = ({ title, keyPoints, overviewStyle = "timeline", vstyle }) => {
  const frame = useCurrentFrame();
  const motionScale = getMotionScale(vstyle);
  const scaleFrames = (frames: number[]) => frames.map(f => f / motionScale);

  const [titleFadeStart, titleFadeEnd] = scaleFrames([0, 15]);
  const titleOpacity = interpolate(frame, [titleFadeStart, titleFadeEnd], [0, 1], { extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [titleFadeStart, titleFadeEnd], [30, 0], { extrapolateRight: "clamp" });

  const accent = vstyle?.accentColor || C.accent;
  const hl = vstyle?.highlightColor || C.highlight;

  // V0.3.9: grid style - 2-column card layout
  if (overviewStyle === "grid") {
    const [listFadeStart, listFadeEnd] = scaleFrames([10, 30]);
    const listOpacity = interpolate(frame, [listFadeStart, listFadeEnd], [0, 1], { extrapolateRight: "clamp" });

    return (
      <AbsoluteFill
        style={{
          background: C.bg,
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 50px",
        }}
      >
        <div style={{ maxWidth: 950, width: "100%" }}>
          <h2 style={{ fontSize: 48, fontWeight: 800, color: C.textPrimary, margin: 0, marginBottom: 32, opacity: titleOpacity, transform: `translateY(${titleY}px)` }}>
            今日回顾
          </h2>

          <div style={{ opacity: listOpacity, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            {keyPoints.map((kp, i) => {
              const itemOpacity = interpolate(frame, [10 + i * 5, 20 + i * 5], [0, 1], { extrapolateRight: "clamp" });
              const itemY = interpolate(frame, [10 + i * 5, 20 + i * 5], [20, 0], { extrapolateRight: "clamp" });
              return (
                <div key={i} style={{ background: C.card, borderRadius: 16, border: `1px solid ${C.border}`, padding: "24px 28px", opacity: itemOpacity, transform: `translateY(${itemY}px)` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: `linear-gradient(135deg, ${accent}, ${C.accent2})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 800, color: C.textPrimary }}>
                      {String(i + 1).padStart(2, "0")}
                    </div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: C.textPrimary }}>{kp.title}</div>
                  </div>
                  <div style={{ fontSize: 18, color: C.textSecondary, lineHeight: 1.5 }}>{kp.body}</div>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // V0.3.9: clean style - minimal list with title only
  if (overviewStyle === "clean") {
    const [listFadeStart, listFadeEnd] = scaleFrames([10, 30]);
    const listOpacity = interpolate(frame, [listFadeStart, listFadeEnd], [0, 1], { extrapolateRight: "clamp" });

    return (
      <AbsoluteFill
        style={{
          background: C.bg,
          justifyContent: "center",
          alignItems: "center",
          padding: "80px 100px",
        }}
      >
        <div style={{ maxWidth: 800, width: "100%" }}>
          <h2 style={{ fontSize: 48, fontWeight: 800, color: C.textPrimary, margin: 0, marginBottom: 40, opacity: titleOpacity, transform: `translateY(${titleY}px)` }}>
            今日回顾
          </h2>

          <div style={{ opacity: listOpacity }}>
            {keyPoints.map((kp, i) => {
              const itemOpacity = interpolate(frame, [12 + i * 6, 22 + i * 6], [0, 1], { extrapolateRight: "clamp" });
              return (
                <div key={i} style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 24, opacity: itemOpacity }}>
                  <span style={{ fontSize: 28, fontWeight: 800, color: accent }}>{String(i + 1).padStart(2, "0")}</span>
                  <span style={{ fontSize: 26, fontWeight: 600, color: C.textPrimary }}>{kp.title}</span>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // Default: timeline style (original behavior)
  const [listFadeStart, listFadeEnd] = scaleFrames([10, 30]);
  const listOpacity = interpolate(frame, [listFadeStart, listFadeEnd], [0, 1], { extrapolateRight: "clamp" });

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
            const [itemFadeStart, itemFadeEnd] = scaleFrames([15 + i * 8, 25 + i * 8]);
            const itemOpacity = interpolate(frame, [itemFadeStart, itemFadeEnd], [0, 1], {
              extrapolateRight: "clamp",
            });
            const itemX = interpolate(frame, [itemFadeStart, itemFadeEnd], [-20, 0], {
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
                    background: `linear-gradient(135deg, ${accent}, ${C.accent2})`,
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

// V0.3.9: Main Video Component with transitionStyle and style variant support
export const AiNewsVideo: React.FC<AiNewsVideoProps> = ({
  title,
  subtitle,
  keyPoints,
  durationSec,
  segmentDurations,
  style,
  showDataViz = true,
}) => {
  const { fps } = useVideoConfig();

  // V0.3.9: Extract style variants
  const motionScale = getMotionScale(style);
  const transitionStyle = style?.transitionStyle ?? "slide_fade";
  const coverStyle = style?.coverStyle ?? "editorial";
  const overviewStyle = style?.overviewStyle ?? "timeline";

  // Calculate transition overlap based on transitionStyle
  // V0.3.9: Different transition modes - fade has more overlap, slide has less
  const getTransitionOverlap = () => {
    switch (transitionStyle) {
      case "fade":
        return 20; // More overlap for pure fade
      case "slide":
        return 8;  // Less overlap for pure slide
      case "slide_fade":
      default:
        return 12; // Balanced slide+fade
    }
  };
  const transitionOverlap = getTransitionOverlap();

  // 每段时长：优先使用与旁白对齐的 segmentDurations，否则回退固定时长
  const FIXED_COVER = 75;   // 2.5s
  const FIXED_CARD = 135;   // 4.5s
  const FIXED_SUMMARY = 60; // 2s

  const useAligned =
    !!segmentDurations &&
    Array.isArray(segmentDurations.cardSecs) &&
    segmentDurations.cardSecs.length === keyPoints.length;

  // Scale durations by motion intensity
  const scaleDuration = (frames: number) => Math.round(frames / motionScale);

  const coverFrames = scaleDuration(useAligned
    ? Math.max(30, Math.round(segmentDurations!.coverSec * fps))
    : FIXED_COVER);
  const cardFramesArr = (useAligned
    ? segmentDurations!.cardSecs.map((s) => Math.max(45, Math.round(s * fps)))
    : keyPoints.map(() => FIXED_CARD)).map(scaleDuration);
  const summaryFrames = scaleDuration(useAligned
    ? Math.max(30, Math.round(segmentDurations!.summarySec * fps))
    : FIXED_SUMMARY);

  // 累计起点 (with transition overlap for seamless cuts)
  const cardStarts: number[] = [];
  let acc = coverFrames;
  for (const f of cardFramesArr) {
    cardStarts.push(acc);
    acc += f - transitionOverlap;
  }
  const summaryStart = acc - transitionOverlap;

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* Cover */}
      <Sequence from={0} durationInFrames={coverFrames + transitionOverlap}>
        <CoverPage
          title={title}
          subtitle={subtitle}
          keyPoints={keyPoints}
          duration={coverFrames}
          coverStyle={coverStyle}
          vstyle={style}
        />
      </Sequence>

      {/* Key Point Cards with transition-aware timing */}
      {keyPoints.map((kp, i) => (
        <Sequence
          key={i}
          from={cardStarts[i]}
          durationInFrames={cardFramesArr[i] + transitionOverlap}
        >
          <KeyPointCard
            kp={kp}
            index={i}
            startFrame={0}
            totalDuration={cardFramesArr[i]}
            fps={fps}
            vstyle={style}
            showDataViz={showDataViz}
          />
        </Sequence>
      ))}

      {/* Summary with transition-aware timing */}
      <Sequence from={summaryStart} durationInFrames={summaryFrames + transitionOverlap}>
        <SummaryPage
          title={title}
          keyPoints={keyPoints}
          overviewStyle={overviewStyle}
          vstyle={style}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

export default AiNewsVideo;
