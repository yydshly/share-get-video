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
import type { AiNewsVideoProps, KeyPoint, Metric, RemotionStyle, MotionIntensity, CoverStyle, OverviewStyle, MetricAnimation, TransitionStyle, RemotionFamily, ReportOverview, BackgroundPreset } from "./data";

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

// V1.2.2: Aspect-ratio-aware layout configuration
// Drives density, font sizes, spacing, and content quantity per output ratio.
const LAYOUT_CONFIGS: Record<string, {
  /** Max keypoint previews shown on the cover/report-opening page */
  coverMaxPreviewItems: number;
  /** Font size for the main title on the cover page */
  coverTitleFontSize: number;
  /** Font size for the subtitle/summary on the cover page */
  coverSubtitleFontSize: number;
  /** Font size for each keypoint title in cover previews */
  coverPreviewTitleFontSize: number;
  /** Font size for each keypoint description in cover previews */
  coverPreviewDescFontSize: number;
  /** Gap between keypoint preview items on the cover page */
  coverPreviewGap: number;
  /** Font size for card title in keypoint pages */
  cardTitleFontSize: number;
  /** Font size for card body/description in keypoint pages */
  cardDescFontSize: number;
  /** Min height of the keypoint card container */
  cardMinHeight: number;
  /** Bottom padding of the keypoint card container */
  cardPadding: number;
  /** Margin bottom between keypoint card elements */
  cardElementGap: number;
  /** Max characters shown for body/description text */
  descMaxChars: number;
}> = {
  vertical_compact: {
    coverMaxPreviewItems: 6,
    coverTitleFontSize: 54,
    coverSubtitleFontSize: 22,
    coverPreviewTitleFontSize: 22,
    coverPreviewDescFontSize: 17,
    coverPreviewGap: 14,
    cardTitleFontSize: 38,
    cardDescFontSize: 26,
    cardMinHeight: 620,
    cardPadding: 40,
    cardElementGap: 20,
    descMaxChars: 56,
  },
  horizontal_balanced: {
    coverMaxPreviewItems: 6,
    coverTitleFontSize: 46,
    coverSubtitleFontSize: 20,
    coverPreviewTitleFontSize: 20,
    coverPreviewDescFontSize: 16,
    coverPreviewGap: 12,
    cardTitleFontSize: 32,
    cardDescFontSize: 22,
    cardMinHeight: 480,
    cardPadding: 36,
    cardElementGap: 16,
    descMaxChars: 72,
  },
  square_compact: {
    coverMaxPreviewItems: 5,
    coverTitleFontSize: 44,
    coverSubtitleFontSize: 19,
    coverPreviewTitleFontSize: 20,
    coverPreviewDescFontSize: 15,
    coverPreviewGap: 12,
    cardTitleFontSize: 30,
    cardDescFontSize: 21,
    cardMinHeight: 520,
    cardPadding: 36,
    cardElementGap: 16,
    descMaxChars: 52,
  },
};

/** Get effective layout config, falling back to vertical_compact. */
function getLayoutConfig(layoutMode?: string) {
  return LAYOUT_CONFIGS[layoutMode || "vertical_compact"] || LAYOUT_CONFIGS.vertical_compact;
}

/** V1.2.x: Metric number font size adapts to layout mode and font scale. */
function getMetricFontSize(layoutMode?: string, fontScale = 1): number {
  const mode = layoutMode || "vertical_compact";
  const base = mode === "square_compact" ? 64 : 72;
  return Math.round(base * fontScale);
}

/** Truncate text to maxChars, adding ellipsis if truncated. */
function truncateText(text: string, maxChars: number): string {
  if (!text) return "";
  const clean = text.trim();
  if (clean.length <= maxChars) return clean;
  return clean.slice(0, maxChars - 1) + "…";
}

// V1.2.4: FloatingParticles — frame-driven drifting dots (Remotion-only effect).
// Deterministic positions (index-seeded) so renders are stable; dots rise & fade-breathe.
const FloatingParticles: React.FC<{ count: number; color: string; maxSize?: number }> = ({ count, color, maxSize = 5 }) => {
  const frame = useCurrentFrame();
  const dots = [];
  for (let i = 0; i < count; i++) {
    const baseX = (i * 73) % 100;
    const size = 2 + ((i * 37) % maxSize);
    const speed = 0.12 + ((i % 5) * 0.06);
    const phase = (i * 53) % 120;
    const y = (((phase - frame * speed) % 120) + 120) % 120; // 0..120, rising
    const x = baseX + Math.sin((frame + i * 30) / 45) * 2.5;
    const op = 0.12 + 0.28 * (0.5 + 0.5 * Math.sin((frame + i * 20) / 28));
    dots.push(
      <div key={i} style={{
        position: "absolute", left: `${x}%`, top: `${y - 10}%`,
        width: size, height: size, borderRadius: "50%",
        background: color, opacity: op, boxShadow: `0 0 ${size * 2.5}px ${color}`,
      }} />
    );
  }
  return <>{dots}</>;
};

// V1.2.4: BackgroundLayer — frame-animated programmatic backgrounds (no image assets).
// Each preset has a distinct MOTION signature (Remotion-specific — a static renderer
// like Pillow can't do flowing grids / scan sweeps / drifting particles):
//   tech_grid_dark   → 流动网格 + 扫描光带 + 上升数据粒子 + 呼吸辉光
//   aurora_blue      → 缓慢漂移的蓝紫极光（呼吸）
//   glass_dashboard  → 玻璃面板（frosted glass + 蓝紫高光层）
//   warm_cinematic   → 暖色电影感（琥珀/金色光晕 + 暗角）
const BackgroundLayer: React.FC<{
  preset?: BackgroundPreset;
  accent?: string;
  highlight?: string;
}> = ({ preset = "tech_grid_dark", accent = C.accent, highlight = C.highlight }) => {
  const frame = useCurrentFrame();
  if (preset === "glass_dashboard") {
    // ── glass_dashboard: frosted glass panels + layered blue-purple glows ──
    // Key differentiator: backdrop-blur glass panels, NOT just glows
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 0,
          background: "#080c18",
          overflow: "hidden",
        }}
      >
        {/* Base ambient blue glow — wide and soft */}
        <div style={{
          position: "absolute", top: "-40%", left: "-20%", width: "140%", height: "120%",
          background: `radial-gradient(ellipse at 40% 30%, ${accent}18 0%, ${C.accent2}10 40%, transparent 70%)`,
          filter: "blur(60px)",
        }} />
        {/* Glass panel — top left, frosted feel */}
        <div style={{
          position: "absolute",
          top: "8%",
          left: "5%",
          width: "45%",
          height: "38%",
          background: `linear-gradient(135deg, ${accent}0e 0%, ${C.accent2}0a 100%)`,
          border: `1px solid ${accent}30`,
          borderRadius: 16,
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
        }} />
        {/* Glass panel — bottom right, offset */}
        <div style={{
          position: "absolute",
          bottom: "12%",
          right: "6%",
          width: "38%",
          height: "32%",
          background: `linear-gradient(225deg, ${C.accent2}0c 0%, ${accent}08 100%)`,
          border: `1px solid ${C.accent2}28`,
          borderRadius: 14,
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
        }} />
        {/* Bright glass highlight streak — top panel top edge */}
        <div style={{
          position: "absolute",
          top: "8%",
          left: "5%",
          width: "45%",
          height: 2,
          background: `linear-gradient(90deg, transparent, ${accent}60, transparent)`,
          borderRadius: 1,
          filter: "blur(1px)",
        }} />
        {/* Secondary glass panel — center right, small */}
        <div style={{
          position: "absolute",
          top: "22%",
          right: "8%",
          width: "28%",
          height: "22%",
          background: `${accent}0a`,
          border: `1px solid ${accent}22`,
          borderRadius: 10,
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
        }} />
        {/* Purple accent glow — bottom left */}
        <div style={{
          position: "absolute", bottom: "-15%", left: "-10%", width: "60%", height: "60%",
          background: `radial-gradient(circle, ${C.accent2}1a 0%, transparent 65%)`,
          filter: "blur(70px)",
        }} />
        {/* Top gradient mask */}
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: "18%",
          background: `linear-gradient(180deg, #080c18 dd 0%, transparent 100%)`,
        }} />
        {/* Bottom gradient mask */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0, height: "20%",
          background: "linear-gradient(0deg, #080c18 aa 0%, transparent 100%)",
        }} />
      </div>
    );
  }

  if (preset === "aurora_blue") {
    // 蓝紫极光渐变：Card Stack 默认背景，空间感更强
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 0,
          background: C.bg,
          overflow: "hidden",
        }}
      >
        {/* 中央大 radial glow — 蓝紫极光 */}
        <div style={{
          position: "absolute", top: "-30%", left: "-20%", width: "140%", height: "100%",
          background: `radial-gradient(ellipse at 30% 40%, ${accent}28 0%, ${C.accent2}14 35%, transparent 65%)`,
          filter: "blur(40px)",
        }} />
        {/* 底部右上方暖色 glow */}
        <div style={{
          position: "absolute", bottom: "-20%", right: "-10%", width: "80%", height: "80%",
          background: `radial-gradient(circle, ${C.accent2}1a 0%, transparent 60%)`,
          filter: "blur(60px)",
        }} />
        {/* 左上角点缀 */}
        <div style={{
          position: "absolute", top: "5%", right: "15%", width: "40%", height: "40%",
          background: `radial-gradient(circle, ${highlight}12 0%, transparent 60%)`,
          filter: "blur(50px)",
        }} />
        {/* 底部渐变 */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0, height: "30%",
          background: `linear-gradient(0deg, ${C.bg}ee 0%, transparent 100%)`,
        }} />
      </div>
    );
  }

  if (preset === "warm_cinematic") {
    // ── warm_cinematic: amber/golden cinematic light + vignette ──
    // Key differentiator: warm amber tones, cinematic light streak, strong vignette
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 0,
          background: "#0c0a14",
          overflow: "hidden",
        }}
      >
        {/* Wide amber light streak from top */}
        <div style={{
          position: "absolute", top: "-20%", left: "10%", width: "80%", height: "55%",
          background: `radial-gradient(ellipse at 50% 20%, rgba(251,191,36,0.18) 0%, rgba(249,115,22,0.10) 40%, transparent 70%)`,
          filter: "blur(50px)",
        }} />
        {/* Golden secondary glow — left side */}
        <div style={{
          position: "absolute", top: "10%", left: "-15%", width: "55%", height: "70%",
          background: `radial-gradient(circle, rgba(251,146,60,0.12) 0%, transparent 60%)`,
          filter: "blur(60px)",
        }} />
        {/* Bottom warm bloom */}
        <div style={{
          position: "absolute", bottom: "-20%", right: "10%", width: "65%", height: "55%",
          background: `radial-gradient(circle, rgba(249,115,22,0.14) 0%, transparent 60%)`,
          filter: "blur(70px)",
        }} />
        {/* Top vignette — cinematic darkening */}
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: "30%",
          background: "linear-gradient(180deg, #0c0a14 ee 0%, transparent 100%)",
        }} />
        {/* Bottom vignette — strong cinematic darkening */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0, height: "35%",
          background: "linear-gradient(0deg, #0c0a14 ff 0%, transparent 100%)",
        }} />
        {/* Left/right subtle vignette */}
        <div style={{
          position: "absolute", top: 0, bottom: 0, left: 0, width: "15%",
          background: "linear-gradient(90deg, #0c0a14 0%, transparent 100%)",
        }} />
        <div style={{
          position: "absolute", top: 0, bottom: 0, right: 0, width: "15%",
          background: "linear-gradient(270deg, #0c0a14 0%, transparent 100%)",
        }} />
      </div>
    );
  }

  // Default: tech_grid_dark — 深蓝黑底 + 流动网格 + 扫描光带 + 上升粒子 + 呼吸辉光
  const gridPan = -((frame * 0.4) % 60);
  const scanY = ((frame * 0.55) % 130) - 15;
  const glow1 = 0.55 + 0.45 * Math.sin(frame / 45);
  const glow2 = 0.45 + 0.35 * Math.sin(frame / 32 + 1.5);
  return (
    <div style={{ position: "absolute", inset: 0, zIndex: 0, background: C.bg, overflow: "hidden" }}>
      {/* Flowing grid — 60px lines panning upward (stronger, bluish) */}
      <div style={{
        position: "absolute", left: 0, right: 0, top: "-10%", height: "120%",
        transform: `translateY(${gridPan}px)`,
        backgroundImage: `
          repeating-linear-gradient(0deg, transparent, transparent 59px, ${accent}33 59px, ${accent}33 60px),
          repeating-linear-gradient(90deg, transparent, transparent 59px, ${accent}26 59px, ${accent}26 60px)
        `,
        opacity: 0.7,
      }} />
      {/* Primary blue tech glow — top center, breathing */}
      <div style={{
        position: "absolute", top: "0%", left: "15%", width: "70%", height: "55%",
        background: `radial-gradient(ellipse, ${accent}3a 0%, transparent 70%)`,
        filter: "blur(70px)", opacity: glow1,
      }} />
      {/* Secondary glow — bottom right, breathing */}
      <div style={{
        position: "absolute", bottom: "0%", right: "0%", width: "55%", height: "50%",
        background: `radial-gradient(circle, ${highlight}22 0%, transparent 65%)`,
        filter: "blur(60px)", opacity: glow2,
      }} />
      {/* Horizontal scan light band — sweeps top→bottom */}
      <div style={{
        position: "absolute", left: 0, right: 0, top: `${scanY}%`, height: "12%",
        background: `linear-gradient(180deg, transparent, ${accent}1f 45%, ${accent}40 50%, ${accent}1f 55%, transparent)`,
        filter: "blur(6px)",
      }} />
      {/* Rising data particles */}
      <FloatingParticles count={18} color={accent} maxSize={4} />
      {/* Top + bottom gradient masks */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: "14%",
        background: `linear-gradient(180deg, ${C.bg}dd 0%, transparent 100%)`,
      }} />
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0, height: "16%",
        background: `linear-gradient(0deg, ${C.bg}cc 0%, transparent 100%)`,
      }} />
    </div>
  );
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
  // V1.2.x: Font size for the big metric number — adapts to layout mode
  metricFontSize?: number;
}> = ({ label, value, unit, startFrame = 18, durationFrames = 26, style, metricFontSize = 72 }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const eased = 1 - Math.pow(1 - p, 3);
  const current = value * eased;
  const decimals = value % 1 === 0 ? 0 : 2;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ fontSize: 22, color: C.textMuted, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: metricFontSize, fontWeight: 900, color: style?.color ?? C.highlight, textShadow: `0 0 36px ${style?.color ?? C.highlight}55`, lineHeight: 1 }}>
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
          background: "transparent",
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 50px",
        }}
      >
        {/* V1.2.1.4: Background layer + existing glow layers for cinematic depth */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        {/* Supplementary cinematic glow layers */}
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
          background: "transparent",
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 80px",
        }}
      >
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1, maxWidth: 800, textAlign: "center" }}>
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
  // V1.2.2: Now shows up to 6 keypoint previews with descriptions, using layout config for density
  const layout = getLayoutConfig(vstyle?.aspectRatioLayoutMode);
  const maxItems = Math.min(layout.coverMaxPreviewItems, keyPoints.length);
  return (
    <AbsoluteFill
      style={{
        background: "transparent",
        justifyContent: "center",
        alignItems: "stretch",
        padding: "48px 50px",
      }}
    >
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
      {/* Glow accent */}
      <div
        style={{
          position: "absolute",
          top: "8%",
          left: "30%",
          width: 500,
          height: 400,
          borderRadius: "50%",
          background: C.glow,
          filter: "blur(100px)",
        }}
      />

      {/* Top label */}
      <div
        style={{
          fontSize: 18,
          color: accent,
          fontWeight: 700,
          letterSpacing: 4,
          textTransform: "uppercase",
          opacity: subtitleOpacity,
          marginBottom: 16,
        }}
      >
        AI 前沿 · 速览
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: layout.coverTitleFontSize,
          fontWeight: 800,
          color: C.textPrimary,
          textAlign: "left",
          margin: 0,
          marginBottom: 14,
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
            fontSize: layout.coverSubtitleFontSize,
            color: C.textSecondary,
            textAlign: "left",
            marginTop: 0,
            marginBottom: 0,
            opacity: subtitleOpacity,
            lineHeight: 1.4,
          }}
        >
          {subtitle}
        </p>
      )}

      {/* V1.2.2: Keypoint preview list — now with descriptions, up to coverMaxPreviewItems */}
      <div style={{ marginTop: 36, opacity: listOpacity }}>
        <div style={{ fontSize: 13, color: accent, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", marginBottom: 14, opacity: subtitleOpacity }}>
          本期重点
        </div>
        {keyPoints.slice(0, maxItems).map((kp, i) => {
          const [itemFadeStart, itemFadeEnd] = scaleFrames([20 + i * 4, 30 + i * 4]);
          const itemOpacity = interpolate(frame, [itemFadeStart, itemFadeEnd], [0, 1], {
            extrapolateRight: "clamp",
          });
          const itemY = interpolate(frame, [itemFadeStart, itemFadeEnd], [12, 0], {
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 14,
                marginBottom: layout.coverPreviewGap,
                opacity: itemOpacity,
                transform: `translateY(${itemY}px)`,
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
                  fontSize: 15,
                  fontWeight: 800,
                  color: C.textPrimary,
                  flexShrink: 0,
                  marginTop: 1,
                }}
              >
                {String(i + 1).padStart(2, "0")}
              </div>
              <div style={{ flex: 1, overflow: "hidden" }}>
                <div
                  style={{
                    fontSize: layout.coverPreviewTitleFontSize,
                    fontWeight: 700,
                    color: C.textPrimary,
                    lineHeight: 1.25,
                    marginBottom: 4,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {kp.title}
                </div>
                {kp.body && (
                  <div
                    style={{
                      fontSize: layout.coverPreviewDescFontSize,
                      color: C.textMuted,
                      lineHeight: 1.4,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {truncateText(kp.body, layout.descMaxChars)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom info */}
      <div
        style={{
          position: "absolute",
          bottom: 36,
          left: 50,
          right: 50,
          fontSize: 18,
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
// V1.2.2: Uses layout config for compact sizing; always shows description.
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

  // V1.2.2: Layout config for aspect-ratio-aware compactness
  const layout = getLayoutConfig(vstyle?.aspectRatioLayoutMode);

  // 主题自适应 + 可调样式（显式 vstyle 优先，否则按该条 tone 配色/图标）
  const tonePreset = TONE_STYLES[(kp.tone || "neutral")] || TONE_STYLES.neutral;
  const accent = vstyle?.accentColor || tonePreset.accent;
  const hl = vstyle?.highlightColor || tonePreset.highlight;
  const fs = vstyle?.fontScale || 1;
  const showIcon = vstyle?.showIcon ?? true;
  const variant = vstyle?.familyVariant;
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
        background: "transparent",
        justifyContent: "center",
        alignItems: "center",
        padding: "60px 40px",
      }}
    >
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
      {/* Card container - 82% width, compact height driven by layout config */}
      <div
        style={{
          width: "82%",
          maxWidth: 880,
          background: C.card,
          borderRadius: 24,
          border: `2px solid ${C.border}`,
          padding: layout.cardPadding,
          position: "relative",
          opacity: cardOpacity,
          transform: `translateY(${cardY}px)`,
          boxShadow: `0 0 80px ${C.glow}, 0 24px 60px rgba(0,0,0,0.6)`,
          // V0.5.5: 内容垂直居中 + 贴合内容的高度下限，消除卡片下半固定留白
          // V1.2.2: Uses layout config for compact minHeight
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          minHeight: layout.cardMinHeight,
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
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 56,
              height: 56,
              borderRadius: 14,
              background: `linear-gradient(135deg, ${accent}, ${C.accent2})`,
              fontSize: 24,
              fontWeight: 800,
              color: C.textPrimary,
              opacity: indexOpacity,
              boxShadow: `0 0 24px ${accent}60`,
              flexShrink: 0,
            }}
          >
            {String(index + 1).padStart(2, "0")}
          </div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: accent,
              background: `${accent}26`,
              border: `1px solid ${accent}66`,
              borderRadius: 999,
              padding: "5px 14px",
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
                width: 40,
                height: 40,
                borderRadius: 10,
                background: `${accent}22`,
                border: `2px solid ${accent}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: accent,
                fontSize: 20,
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
            fontSize: Math.round(layout.cardTitleFontSize * fs),
            fontWeight: 800,
            color: C.textPrimary,
            margin: 0,
            marginBottom: layout.cardElementGap,
            lineHeight: 1.25,
            opacity: titleOpacity,
            textShadow: "0 0 40px rgba(59, 130, 246, 0.25)",
          }}
        >
          <HighlightedText text={kp.title} style={{}} highlightColor={hl} emphasisTerms={kp.emphasisTerms} />
        </h2>

        {/* Decorative separator */}
        <div
          style={{
            width: 64,
            height: 3,
            background: `linear-gradient(90deg, ${accent}, ${C.accent2})`,
            borderRadius: 2,
            marginBottom: layout.cardElementGap,
            opacity: titleOpacity,
          }}
        />

        {/* Body — always visible, truncated to descMaxChars */}
        <p
          style={{
            fontSize: Math.round(layout.cardDescFontSize * fs),
            color: C.textSecondary,
            margin: 0,
            marginBottom: layout.cardElementGap,
            lineHeight: 1.65,
            opacity: bodyOpacity,
          }}
        >
          <HighlightedText text={truncateText(kp.body, layout.descMaxChars)} style={{}} highlightColor={hl} emphasisTerms={kp.emphasisTerms} />
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
                    <div style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}>
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
                    style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}
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
                    metricFontSize={getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs)}
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
                  metricFontSize={getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs)}
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
                <div style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}>
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
                style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}
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

// V0.6.2: Card Stack — renders a single card layer within the card-stack layout
// V1.2.2: Uses layout config for compact sizing
const CardStackLayer: React.FC<{
  kp: KeyPoint;
  index: number;
  // Stack position: -1 = previous (behind/right), 0 = current (main), 1 = next (preview/left)
  stackPosition: -1 | 0 | 1;
  startFrame: number;    // When this layer becomes visible
  exitFrame: number;     // When this layer starts exiting
  totalFrames: number;   // Total duration of the stack segment
  fps: number;
  vstyle?: RemotionStyle;
  showDataViz?: boolean;
}> = ({ kp, index, stackPosition, startFrame, exitFrame, totalFrames, fps, vstyle, showDataViz = true }) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);

  // V1.2.2: Layout config for aspect-ratio-aware compactness
  const layout = getLayoutConfig(vstyle?.aspectRatioLayoutMode);

  const tonePreset = TONE_STYLES[(kp.tone || "neutral")] || TONE_STYLES.neutral;
  const accent = vstyle?.accentColor || tonePreset.accent;
  const hl = vstyle?.highlightColor || tonePreset.highlight;
  const fs = vstyle?.fontScale || 1;
  const showIcon = vstyle?.showIcon ?? true;
  const iconGlyph = tonePreset.glyph;
  const metricAnimation = vstyle?.metricAnimation ?? "countup_bar";

  // Card Stack specific positioning
  const isPrev = stackPosition === -1;
  const isNext = stackPosition === 1;
  // V1.2.x: Debug switch — hide PREV/NEXT stack labels by default
  const showStackDebugLabels = vstyle?.debugStackLabels === true;

  // Previous card: slides out to top-right, shrinks, fades
  // Current card: slides in from bottom-right, grows, becomes prominent
  // Next card: peek from left/bottom-left, small preview

  // Animation progress for this layer
  const entryDuration = 16; // frames to fully enter
  const exitDuration = 16;  // frames to fully exit

  let scale: number, opacity: number, offsetX: number, offsetY: number;

  if (isPrev) {
    // V0.6.5.2: Further strengthened — prev card visible at top-right corner
    const progress = Math.min(1, localFrame / entryDuration);
    const eased = 1 - Math.pow(1 - progress, 2);
    scale = 1.0 - 0.22 * eased;    // 1.0 → 0.78 (smaller = further away)
    opacity = 1.0 - 0.25 * eased;   // 1.0 → 0.75 (more opaque)
    offsetX = 220 * eased;           // slides right much more (was 140)
    offsetY = -130 * eased;          // slides up much more (was -80)
  } else if (isNext) {
    // V0.6.5.2: Further strengthened — next card visible at bottom-left corner
    const progress = Math.min(1, localFrame / entryDuration);
    const eased = 1 - Math.pow(1 - progress, 2);
    scale = 0.72 + 0.04 * eased;    // 0.72 → 0.76 (slightly larger)
    opacity = 0.40 + 0.20 * eased;  // 0.40 → 0.60 (more opaque than V0.6.5's 0.40)
    offsetX = -220 * eased;          // from left much more (was -120)
    offsetY = 110 * eased;           // from bottom much more (was 70)
  } else {
    // Current card: V0.6.5 — slides up from bottom, scales in to full size
    const progress = Math.min(1, localFrame / entryDuration);
    const eased = 1 - Math.pow(1 - progress, 3);
    scale = 0.90 + 0.10 * eased;   // 0.90 → 1.0 (was 0.92 → 1.0)
    opacity = 0.0 + 1.0 * eased;    // 0 → 1
    offsetX = 0;                    // V0.6.5: centered (was 20 → 0)
    offsetY = 0;                   // V0.6.5: centered (was 30 → 0)
  }

  // V0.6.5.2: Visible border color for prev/next layer identification
  const layerBorderColor = isPrev
    ? "rgba(96,165,250,0.85)"
    : isNext
    ? "rgba(34,211,238,0.85)"
    : C.border;

  // V0.6.5.2: Stronger glow for prev/next layers
  const layerGlow = isPrev
    ? "rgba(59,130,246,0.45)"
    : isNext
    ? "rgba(6,182,212,0.45)"
    : C.glow;

  // Build the card JSX (same content as KeyPointCard but positioned differently)
  // V0.6.5.2: prev/next have distinct border colors and small corner labels for visibility verification
  const cardContent = (
    <div
      style={{
        width: "82%",
        maxWidth: 880,
        background: C.card,
        borderRadius: 24,
        border: `2px solid ${layerBorderColor}`,
        padding: layout.cardPadding,
        position: "relative",
        boxShadow: `0 0 80px ${layerGlow}, 0 24px 60px rgba(0,0,0,0.6)`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        minHeight: layout.cardMinHeight,
      }}
    >
      {/* V0.6.5.2: Small verification label for prev layer — top-right corner */}
      {showStackDebugLabels && isPrev && (
        <div style={{
          position: "absolute",
          top: 12,
          right: 16,
          background: "rgba(59,130,246,0.25)",
          border: "1px solid rgba(96,165,250,0.7)",
          borderRadius: 6,
          padding: "3px 10px",
          fontSize: 13,
          fontWeight: 700,
          color: "rgba(147,197,253,0.95)",
          letterSpacing: 1,
          zIndex: 10,
        }}>
          PREV
        </div>
      )}
      {/* V0.6.5.2: Small verification label for next layer — bottom-left corner */}
      {showStackDebugLabels && isNext && (
        <div style={{
          position: "absolute",
          bottom: 12,
          left: 16,
          background: "rgba(6,182,212,0.25)",
          border: "1px solid rgba(34,211,238,0.7)",
          borderRadius: 6,
          padding: "3px 10px",
          fontSize: 13,
          fontWeight: 700,
          color: "rgba(128,240,255,0.95)",
          letterSpacing: 1,
          zIndex: 10,
        }}>
          NEXT
        </div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
        <div style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: 56, height: 56, borderRadius: 14,
          background: `linear-gradient(135deg, ${accent}, ${C.accent2})`,
          fontSize: 24, fontWeight: 800, color: C.textPrimary,
          boxShadow: `0 0 24px ${accent}60`,
          flexShrink: 0,
        }}>
          {String(index + 1).padStart(2, "0")}
        </div>
        <div style={{
          fontSize: 14, fontWeight: 700, color: accent,
          background: `${accent}26`, border: `1px solid ${accent}66`,
          borderRadius: 999, padding: "5px 14px", letterSpacing: 1.5, textTransform: "uppercase" as const,
        }}>
          KEY POINT
        </div>
        {showIcon && (
          <div style={{
            marginLeft: "auto", width: 40, height: 40, borderRadius: 10,
            background: `${accent}22`, border: `2px solid ${accent}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: accent, fontSize: 20, fontWeight: 900,
          }}>
            {iconGlyph}
          </div>
        )}
      </div>

      <h2 style={{
        fontSize: Math.round(layout.cardTitleFontSize * fs), fontWeight: 800, color: C.textPrimary,
        margin: 0, marginBottom: layout.cardElementGap, lineHeight: 1.25,
        textShadow: "0 0 40px rgba(59, 130, 246, 0.25)",
      }}>
        <HighlightedText text={kp.title} style={{}} highlightColor={hl} emphasisTerms={kp.emphasisTerms} />
      </h2>

      <div style={{
        width: 64, height: 3, background: `linear-gradient(90deg, ${accent}, ${C.accent2})`,
        borderRadius: 2, marginBottom: layout.cardElementGap,
      }} />

      <p style={{
        fontSize: Math.round(layout.cardDescFontSize * fs), color: C.textSecondary,
        margin: 0, marginBottom: layout.cardElementGap, lineHeight: 1.65,
      }}>
        <HighlightedText text={truncateText(kp.body, layout.descMaxChars)} style={{}} highlightColor={hl} emphasisTerms={kp.emphasisTerms} />
      </p>

      {showDataViz && (() => {
        if (kp.metrics && kp.metrics.length > 0) {
          const m = kp.metrics[0];
          const unit = m.unit ?? "";
          if (m.min !== undefined && m.max !== undefined) {
            return (
              <div style={{ marginTop: 6, marginBottom: 8 }}>
                <RangeBar min={m.min} max={m.max} unit={unit} fromColor={accent} toColor={hl} />
              </div>
            );
          }
          if (unit === "%") {
            if (metricAnimation === "none") {
              return (
                <div style={{ marginTop: 6, marginBottom: 8 }}>
                  <div style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}>
                    {m.value}{unit}
                  </div>
                </div>
              );
            }
            return (
              <div style={{ marginTop: 6, marginBottom: 8 }}>
                <CountUpNumber value={m.value} suffix={unit} decimals={m.value % 1 === 0 ? 0 : 1}
                  style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }} />
                {metricAnimation === "countup_bar" && <DataBar pct={Math.min(100, Math.max(0, m.value))} fromColor={accent} toColor={hl} />}
              </div>
            );
          }
          return (
            <div style={{ marginTop: 6, marginBottom: 8 }}>
              <MetricValueCard label={m.label ?? unit} value={m.value} unit={unit} style={{ color: hl }} metricFontSize={getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs)} />
            </div>
          );
        }
        const stat = findPrimaryStat(kp);
        if (!stat) return null;
        if (metricAnimation === "none") {
          return (
            <div style={{ marginTop: 6, marginBottom: 8 }}>
              <div style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }}>
                {stat.value}{stat.suffix}
              </div>
            </div>
          );
        }
        return (
          <div style={{ marginTop: 6, marginBottom: 8 }}>
            <CountUpNumber value={stat.value} suffix={stat.suffix} decimals={stat.value % 1 === 0 ? 0 : 1}
              style={{ fontSize: getMetricFontSize(vstyle?.aspectRatioLayoutMode, fs), fontWeight: 900, color: hl, textShadow: `0 0 36px ${hl}55`, lineHeight: 1 }} />
            {metricAnimation === "countup_bar" && <DataBar pct={stat.value} fromColor={accent} toColor={hl} />}
          </div>
        );
      })()}

      {kp.source && (
        <div style={{
          marginTop: 32, paddingTop: 20, borderTop: `1px solid ${C.border}`,
          fontSize: 20, color: C.textMuted,
        }}>
          来源：{kp.source}
        </div>
      )}
    </div>
  );

  // V0.6.5: z-index — ensure correct stacking (prev=1, next=0, current=2)
  const zIndex = isPrev ? 1 : isNext ? 0 : 2;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
        opacity,
        transformOrigin: "center center",
        zIndex,
      }}
    >
      {cardContent}
    </div>
  );
};

// V0.6.2: Card Stack layout — renders prev/current/next cards stacked
// Used when remotionFamily === "card_stack"
const CardStackLayout: React.FC<{
  keyPoints: KeyPoint[];
  cardStarts: number[];
  cardFramesArr: number[];
  transitionOverlap: number;
  fps: number;
  vstyle?: RemotionStyle;
  showDataViz?: boolean;
}> = ({ keyPoints, cardStarts, cardFramesArr, transitionOverlap, fps, vstyle, showDataViz }) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ background: "transparent", justifyContent: "center", alignItems: "center", padding: "60px 40px" }}>
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={vstyle?.accentColor} highlight={vstyle?.highlightColor} />
      {keyPoints.map((kp, i) => {
        const totalFrames = cardFramesArr[i] + transitionOverlap;
        // V1.2.1.4: visualPeekFrames is independent of transitionOverlap / safeOverlap.
        // This allows prev/next cards to be visually visible even when safeOverlap=0 (source-bound mode).
        const visualPeekFramesRaw = vstyle?.cardStackPeekFrames ?? 18;
        const visualPeekFrames = Math.max(0, Math.min(45, visualPeekFramesRaw));
        const entryWindow = Math.min(visualPeekFrames, Math.max(0, totalFrames - 1));
        const prevVisible = entryWindow > 0 && i > 0;
        const nextVisible = entryWindow > 0 && i < keyPoints.length - 1;

        // Previous card layer: appears at start of current card
        // Current card layer: main
        // Next card layer: appears at end of current card

        return (
          <Sequence
            key={i}
            from={cardStarts[i]}
            durationInFrames={totalFrames}
          >
            <AbsoluteFill style={{ background: "transparent", justifyContent: "center", alignItems: "center" }}>
              {/* Previous card (behind, offset top-right) */}
              {prevVisible && (
                <CardStackLayer
                  kp={keyPoints[i - 1]}
                  index={i - 1}
                  stackPosition={-1}
                  startFrame={0}
                  exitFrame={totalFrames - entryWindow}
                  totalFrames={totalFrames}
                  fps={fps}
                  vstyle={vstyle}
                  showDataViz={showDataViz}
                />
              )}

              {/* Current card (main) */}
              <CardStackLayer
                kp={kp}
                index={i}
                stackPosition={0}
                startFrame={0}
                exitFrame={totalFrames}
                totalFrames={totalFrames}
                fps={fps}
                vstyle={vstyle}
                showDataViz={showDataViz}
              />

              {/* Next card preview (peek from left) */}
              {nextVisible && (
                <CardStackLayer
                  kp={keyPoints[i + 1]}
                  index={i + 1}
                  stackPosition={1}
                  startFrame={totalFrames - entryWindow}
                  exitFrame={totalFrames}
                  totalFrames={totalFrames}
                  fps={fps}
                  vstyle={vstyle}
                  showDataViz={showDataViz}
                />
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
// V0.8.9: Timeline News layout — renders all keyPoints as a vertical event-evolution
// timeline. The currently-playing node is highlighted; past nodes are dimmed; upcoming
// nodes are even dimmer. Used when remotionFamily === "timeline_news".
const TimelineNewsLayout: React.FC<{
  keyPoints: KeyPoint[];
  cardStarts: number[];
  cardFramesArr: number[];
  transitionOverlap: number;
  fps: number;
  vstyle?: RemotionStyle;
  showDataViz?: boolean;
}> = ({ keyPoints, cardStarts, cardFramesArr, fps, vstyle, showDataViz = true }) => {
  const localFrame = useCurrentFrame();

  // V0.8.9: This layout is wrapped in a Sequence starting at coverFrames.
  // useCurrentFrame() returns the local frame inside that Sequence (0-based).
  // By construction, cardStarts[0] === coverFrames, so the first keypoint's local
  // start is 0; subsequent keypoints' local starts are cumulative sums of cardFramesArr.
  const relativeStarts: number[] = [];
  {
    let acc = 0;
    for (const f of cardFramesArr) {
      relativeStarts.push(acc);
      acc += f;
    }
  }

  // Determine each node's state: upcoming | active | past
  const states: ("upcoming" | "active" | "past")[] = cardFramesArr.map((dur, i) => {
    const start = relativeStarts[i];
    const end = start + dur;
    if (localFrame < start) return "upcoming";
    if (localFrame < end) return "active";
    return "past";
  });

  // V0.8.9: progress line — 0 to 1 based on time within the card section
  const totalCardFrames = cardFramesArr.reduce((a, b) => a + b, 0);
  const progress = totalCardFrames > 0 ? Math.min(1, Math.max(0, localFrame / totalCardFrames)) : 0;

  const accent = vstyle?.accentColor || C.accent;
  const hl = vstyle?.highlightColor || C.highlight;
  const fs = vstyle?.fontScale || 1;
  const showIcon = vstyle?.showIcon ?? true;
  const variant = vstyle?.familyVariant;

  // Container wraps from coverFrames to summaryStart; we center content vertically.
  // node center X is at left padding + 27 (half of 54)
  const NODE_SIZE = 54;
  const NODE_LEFT = 60; // padding-left
  const NODE_CENTER_X = NODE_LEFT + NODE_SIZE / 2;

  if (variant === "route_map") {
    return (
      <AbsoluteFill style={{ background: "transparent", padding: "72px 58px", justifyContent: "center" }}>
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ color: accent, fontSize: 18, fontWeight: 800, letterSpacing: 5, textTransform: "uppercase", marginBottom: 42 }}>Route Map</div>
          <div style={{ position: "relative", height: 720 }}>
            <div style={{ position: "absolute", left: 70, right: 70, top: 330, height: 6, borderRadius: 999, background: C.surface }} />
            <div style={{ position: "absolute", left: 70, top: 330, width: `calc((100% - 140px) * ${progress})`, height: 6, borderRadius: 999, background: `linear-gradient(90deg, ${accent}, ${hl})`, boxShadow: `0 0 22px ${accent}66` }} />
            {keyPoints.slice(0, 5).map((kp, i) => {
              const state = states[i];
              const isActive = state === "active";
              const isPast = state === "past";
              const left = `${8 + i * (84 / Math.max(1, Math.min(5, keyPoints.length) - 1))}%`;
              const top = i % 2 === 0 ? 210 : 420;
              return (
                <div key={i} style={{ position: "absolute", left, top, width: 220, transform: "translateX(-50%)", opacity: isActive ? 1 : isPast ? 0.7 : 0.38 }}>
                  <div style={{ width: 58, height: 58, borderRadius: "50%", margin: "0 auto 14px", background: isActive ? `linear-gradient(135deg, ${accent}, ${hl})` : C.card, border: `2px solid ${isActive ? hl : C.border}`, color: isActive ? C.bg : C.textMuted, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, fontWeight: 900, boxShadow: isActive ? `0 0 36px ${accent}66` : "none" }}>{i + 1}</div>
                  <div style={{ background: isActive ? C.card : C.surface, border: `1px solid ${isActive ? accent : C.border}`, borderRadius: 16, padding: "14px 16px", textAlign: "center" }}>
                    <div style={{ color: isActive ? C.textPrimary : C.textSecondary, fontSize: Math.round((isActive ? 22 : 18) * fs), fontWeight: 800, lineHeight: 1.28 }}>{kp.title}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        background: "transparent",
        padding: "60px 50px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
      }}
    >
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
      {/* V0.8.9: 顶部小标题 — 标识 Timeline News 范式 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 28,
        }}
      >
        <div
          style={{
            fontSize: 18,
            color: accent,
            fontWeight: 700,
            letterSpacing: 4,
            textTransform: "uppercase",
            opacity: 0.85,
          }}
        >
          事件演进 · {keyPoints.length} 个节点
        </div>
      </div>

      {/* V0.8.9: 竖向时间线主轴（包含进度线 + 节点列） */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 22,
          position: "relative",
        }}
      >
        {/* 背景进度线（暗色槽） */}
        <div
          style={{
            position: "absolute",
            left: NODE_CENTER_X - 1.5,
            top: NODE_SIZE / 2,
            bottom: NODE_SIZE / 2,
            width: 3,
            background: C.surface,
            borderRadius: 999,
          }}
        />
        {/* 已播放进度（彩色渐变 + glow） */}
        <div
          style={{
            position: "absolute",
            left: NODE_CENTER_X - 1.5,
            top: NODE_SIZE / 2,
            width: 3,
            height: `calc((100% - ${NODE_SIZE}px) * ${progress})`,
            background: `linear-gradient(180deg, ${accent}, ${hl})`,
            borderRadius: 999,
            boxShadow: `0 0 12px ${accent}88`,
          }}
        />

        {keyPoints.map((kp, i) => {
          const state = states[i];
          const isActive = state === "active";
          const isPast = state === "past";
          const isUpcoming = state === "upcoming";

          const nodeOpacity = isActive ? 1 : isPast ? 0.55 : 0.25;
          const nodeScale = isActive ? 1.0 : 0.85;
          const nodeBg = isActive
            ? `linear-gradient(135deg, ${accent}, ${C.accent2})`
            : C.card;
          const nodeBorderColor = isActive ? accent : C.border;
          const nodeTextColor = isActive ? C.textPrimary : C.textMuted;
          const nodeShadow = isActive ? `0 0 30px ${accent}88` : "none";

          // 节点进场：active 节点第一帧略淡入
          const entryStart = relativeStarts[i];
          const entryFrames = 12;
          const nodeEntryOpacity = isActive
            ? Math.min(1, Math.max(0, (localFrame - entryStart) / entryFrames))
            : 1;
          const combinedOpacity = nodeOpacity * nodeEntryOpacity;

          // 轻量 metric：使用 findPrimaryStat（与 CardStackLayer 同样的优先级）
          const stat = findPrimaryStat(kp);

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 20,
                opacity: combinedOpacity,
                position: "relative",
              }}
            >
              {/* 节点圆 (左侧时间线主轴) */}
              <div
                style={{
                  width: NODE_SIZE,
                  height: NODE_SIZE,
                  borderRadius: "50%",
                  background: nodeBg,
                  border: `2px solid ${nodeBorderColor}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 18,
                  fontWeight: 800,
                  color: nodeTextColor,
                  flexShrink: 0,
                  zIndex: 1,
                  transform: `scale(${nodeScale})`,
                  boxShadow: nodeShadow,
                }}
              >
                {String(i + 1).padStart(2, "0")}
              </div>

              {/* 事件卡片 (右侧) */}
              <div
                style={{
                  flex: 1,
                  background: isActive ? C.card : C.surface,
                  borderRadius: 16,
                  border: `1px solid ${isActive ? accent + "66" : C.border}`,
                  padding: isActive ? "22px 26px" : "14px 18px",
                  boxShadow: isActive ? `0 0 40px ${accent}33` : "none",
                }}
              >
                {/* 标题 */}
                <h3
                  style={{
                    fontSize: Math.round((isActive ? 34 : 26) * fs),
                    fontWeight: 800,
                    color: isActive ? C.textPrimary : C.textSecondary,
                    margin: 0,
                    marginBottom: isActive ? 10 : 0,
                    lineHeight: 1.3,
                  }}
                >
                  <HighlightedText
                    text={kp.title}
                    style={{}}
                    highlightColor={hl}
                    emphasisTerms={kp.emphasisTerms}
                  />
                </h3>

                {/* 摘要 (active 节点才显示完整 body) */}
                {isActive && (
                  <p
                    style={{
                      fontSize: Math.round(22 * fs),
                      color: C.textSecondary,
                      margin: 0,
                      marginBottom: stat ? 12 : (kp.source ? 12 : 0),
                      lineHeight: 1.6,
                    }}
                  >
                    <HighlightedText
                      text={kp.body}
                      style={{}}
                      highlightColor={hl}
                      emphasisTerms={kp.emphasisTerms}
                    />
                  </p>
                )}

                {/* 轻量 metric (仅 active，且 showDataViz 开) */}
                {isActive && showDataViz && stat && (
                  <div
                    style={{
                      fontSize: 30,
                      fontWeight: 900,
                      color: hl,
                      marginBottom: kp.source ? 10 : 0,
                      textShadow: `0 0 24px ${hl}55`,
                      lineHeight: 1,
                    }}
                  >
                    <CountUpNumber
                      value={stat.value}
                      suffix={stat.suffix}
                      decimals={stat.value % 1 === 0 ? 0 : 1}
                      style={{ fontSize: 30, fontWeight: 900, color: hl }}
                    />
                    {stat.label && (
                      <span
                        style={{
                          fontSize: 16,
                          color: C.textMuted,
                          marginLeft: 8,
                          fontWeight: 500,
                        }}
                      >
                        {stat.label}
                      </span>
                    )}
                  </div>
                )}

                {/* 来源 (active 节点) */}
                {isActive && kp.source && (
                  <div
                    style={{
                      fontSize: 15,
                      color: C.textMuted,
                      paddingTop: 10,
                      borderTop: `1px solid ${C.border}`,
                    }}
                  >
                    来源：{kp.source}
                  </div>
                )}

                {/* 非 active 节点也允许 small icon 提示分类 (与 showIcon 联动) */}
                {!isActive && showIcon && (
                  <div
                    style={{
                      fontSize: 13,
                      color: C.textMuted,
                      marginTop: 4,
                      opacity: 0.7,
                    }}
                  >
                    ◆ 节点 {String(i + 1).padStart(2, "0")}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const DashboardBriefLayout: React.FC<{
  keyPoints: KeyPoint[];
  cardStarts: number[];
  cardFramesArr: number[];
  transitionOverlap: number;
  fps: number;
  vstyle?: RemotionStyle;
  showDataViz?: boolean;
}> = ({ keyPoints, cardFramesArr, vstyle, showDataViz = true }) => {
  const localFrame = useCurrentFrame();
  const accent = vstyle?.accentColor || "#f59e0b";
  const hl = vstyle?.highlightColor || "#fde047";
  const fs = vstyle?.fontScale || 1;
  const variant = vstyle?.familyVariant;
  const relativeStarts: number[] = [];
  {
    let acc = 0;
    for (const f of cardFramesArr) {
      relativeStarts.push(acc);
      acc += f;
    }
  }
  const activeIndex = Math.max(
    0,
    Math.min(
      keyPoints.length - 1,
      relativeStarts.findIndex((start, i) => {
        const next = relativeStarts[i + 1] ?? Number.POSITIVE_INFINITY;
        return localFrame >= start && localFrame < next;
      }),
    ),
  );
  const totalCardFrames = cardFramesArr.reduce((a, b) => a + b, 0);
  const progress = totalCardFrames > 0 ? Math.min(1, Math.max(0, localFrame / totalCardFrames)) : 0;
  const active = keyPoints[activeIndex] ?? keyPoints[0];
  const stats = keyPoints
    .map((kp, i) => ({ kp, stat: findPrimaryStat(kp), index: i }))
    .filter((item) => item.stat)
    .slice(0, 3);

  if (variant === "ranking_strip") {
    return (
      <AbsoluteFill style={{ background: "transparent", padding: "70px 58px", justifyContent: "center" }}>
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ color: accent, fontSize: 18, fontWeight: 800, letterSpacing: 5, textTransform: "uppercase", marginBottom: 22 }}>Ranking Strip</div>
          <h2 style={{ color: C.textPrimary, fontSize: 52, fontWeight: 900, lineHeight: 1.15, margin: 0, marginBottom: 34 }}>Top signals by impact</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {keyPoints.slice(0, 5).map((kp, i) => {
              const activeRow = i === activeIndex;
              const width = `${Math.max(34, 100 - i * 12)}%`;
              return (
                <div key={i} style={{ background: activeRow ? C.card : C.surface, border: `1px solid ${activeRow ? accent : C.border}`, borderRadius: 18, padding: "20px 22px", opacity: activeRow ? 1 : 0.72, boxShadow: activeRow ? `0 0 34px ${accent}28` : "none" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "64px 1fr", gap: 18, alignItems: "center" }}>
                    <div style={{ color: activeRow ? hl : C.textMuted, fontSize: 44, fontWeight: 900 }}>{String(i + 1).padStart(2, "0")}</div>
                    <div>
                      <div style={{ color: activeRow ? C.textPrimary : C.textSecondary, fontSize: Math.round(28 * fs), fontWeight: 800, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{kp.title}</div>
                      <div style={{ height: 10, background: "#0b1220", borderRadius: 999, overflow: "hidden", marginTop: 12 }}>
                        <div style={{ width, height: "100%", background: `linear-gradient(90deg, ${accent}, ${hl})`, borderRadius: 999 }} />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "chart_story") {
    const points = keyPoints.slice(0, 5).map((kp, i) => {
      const stat = findPrimaryStat(kp);
      return Math.min(100, Math.max(12, stat?.value ?? 30 + i * 13));
    });
    return (
      <AbsoluteFill style={{ background: "transparent", padding: "66px 56px" }}>
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1, height: "100%", display: "flex", flexDirection: "column" }}>
          <div style={{ color: accent, fontSize: 18, fontWeight: 800, letterSpacing: 5, textTransform: "uppercase" }}>Chart Story</div>
          <h2 style={{ color: C.textPrimary, fontSize: 48, fontWeight: 900, margin: "14px 0 26px", lineHeight: 1.15 }}>{active?.title}</h2>
          <div style={{ flex: 1, background: C.card, border: `1px solid ${accent}55`, borderRadius: 24, padding: "36px 34px", display: "flex", alignItems: "end", gap: 18 }}>
            {points.map((value, i) => {
              const activeBar = i === activeIndex;
              const h = `${value}%`;
              return (
                <div key={i} style={{ flex: 1, height: "100%", display: "flex", flexDirection: "column", justifyContent: "end", gap: 12 }}>
                  <div style={{ height: h, minHeight: 60, borderRadius: "18px 18px 8px 8px", background: `linear-gradient(180deg, ${activeBar ? hl : accent}, ${accent})`, opacity: activeBar ? 1 : 0.45, boxShadow: activeBar ? `0 0 34px ${hl}44` : "none" }} />
                  <div style={{ color: activeBar ? C.textPrimary : C.textMuted, fontSize: 18, fontWeight: 800, textAlign: "center" }}>0{i + 1}</div>
                </div>
              );
            })}
          </div>
          <p style={{ color: C.textSecondary, fontSize: 27, lineHeight: 1.5, margin: "24px 0 0" }}>{active?.body}</p>
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ background: "transparent", padding: "58px 50px" }}>
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
      <div style={{ position: "relative", zIndex: 1, height: "100%", display: "flex", flexDirection: "column", gap: 22 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ color: accent, fontSize: 18, fontWeight: 800, letterSpacing: 4, textTransform: "uppercase" }}>
              Dashboard Brief
            </div>
            <div style={{ color: C.textPrimary, fontSize: 42, fontWeight: 900, marginTop: 8 }}>
              AI News Signal Board
            </div>
          </div>
          <div style={{ width: 126, height: 126, borderRadius: 28, background: `${accent}18`, border: `1px solid ${accent}55`, display: "flex", alignItems: "center", justifyContent: "center", color: hl, fontSize: 42, fontWeight: 900, boxShadow: `0 0 40px ${accent}30` }}>
            {Math.round(progress * 100)}%
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
          {stats.length > 0 ? stats.map(({ kp, stat, index }) => (
            <div key={index} style={{ background: C.card, border: `1px solid ${index === activeIndex ? accent : C.border}`, borderRadius: 18, padding: "22px 20px", minHeight: 178, boxShadow: index === activeIndex ? `0 0 34px ${accent}28` : "none" }}>
              <div style={{ color: C.textMuted, fontSize: 17, fontWeight: 700, marginBottom: 12 }}>
                {stat!.label || `Metric ${index + 1}`}
              </div>
              <div style={{ color: hl, fontSize: 56, fontWeight: 900, lineHeight: 1, textShadow: `0 0 24px ${hl}44` }}>
                {showDataViz ? (
                  <CountUpNumber value={stat!.value} suffix={stat!.suffix} decimals={stat!.value % 1 === 0 ? 0 : 1} />
                ) : (
                  <>{stat!.value}{stat!.suffix}</>
                )}
              </div>
              <div style={{ color: C.textSecondary, fontSize: 19, lineHeight: 1.35, marginTop: 12 }}>
                {kp.title}
              </div>
            </div>
          )) : keyPoints.slice(0, 3).map((kp, i) => (
            <div key={i} style={{ background: C.card, border: `1px solid ${i === activeIndex ? accent : C.border}`, borderRadius: 18, padding: "22px 20px", minHeight: 178 }}>
              <div style={{ color: hl, fontSize: 48, fontWeight: 900 }}>0{i + 1}</div>
              <div style={{ color: C.textSecondary, fontSize: 20, lineHeight: 1.4, marginTop: 10 }}>{kp.title}</div>
            </div>
          ))}
        </div>

        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 18, minHeight: 0 }}>
          <div style={{ background: C.card, border: `1px solid ${accent}55`, borderRadius: 22, padding: "30px 32px", boxShadow: `0 0 50px ${accent}20` }}>
            <div style={{ color: accent, fontSize: 18, fontWeight: 800, marginBottom: 18 }}>ACTIVE SIGNAL</div>
            <h2 style={{ color: C.textPrimary, fontSize: Math.round(44 * fs), lineHeight: 1.2, margin: 0, marginBottom: 18 }}>
              <HighlightedText text={active?.title ?? ""} style={{}} highlightColor={hl} emphasisTerms={active?.emphasisTerms} />
            </h2>
            <p style={{ color: C.textSecondary, fontSize: Math.round(27 * fs), lineHeight: 1.55, margin: 0 }}>
              <HighlightedText text={active?.body ?? ""} style={{}} highlightColor={hl} emphasisTerms={active?.emphasisTerms} />
            </p>
          </div>

          <div style={{ background: "#0f172a", border: `1px solid ${C.border}`, borderRadius: 22, padding: "26px 24px", display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ color: C.textMuted, fontSize: 18, fontWeight: 800 }}>RANKING</div>
            {keyPoints.slice(0, 5).map((kp, i) => {
              const activeRow = i === activeIndex;
              const width = `${Math.max(26, 100 - i * 14)}%`;
              return (
                <div key={i} style={{ opacity: activeRow ? 1 : 0.58 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <span style={{ color: activeRow ? hl : C.textMuted, fontSize: 20, fontWeight: 900 }}>{i + 1}</span>
                    <span style={{ color: activeRow ? C.textPrimary : C.textSecondary, fontSize: 18, fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{kp.title}</span>
                  </div>
                  <div style={{ height: 9, background: C.surface, borderRadius: 999, overflow: "hidden" }}>
                    <div style={{ width, height: "100%", background: `linear-gradient(90deg, ${accent}, ${hl})`, borderRadius: 999 }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const CaptionStoryLayout: React.FC<{
  keyPoints: KeyPoint[];
  cardStarts: number[];
  cardFramesArr: number[];
  transitionOverlap: number;
  fps: number;
  vstyle?: RemotionStyle;
  showDataViz?: boolean;
}> = ({ keyPoints, cardFramesArr, vstyle }) => {
  const localFrame = useCurrentFrame();
  const accent = vstyle?.accentColor || "#ec4899";
  const hl = vstyle?.highlightColor || "#f9a8d4";
  const fs = vstyle?.fontScale || 1;
  const variant = vstyle?.familyVariant;
  const relativeStarts: number[] = [];
  {
    let acc = 0;
    for (const f of cardFramesArr) {
      relativeStarts.push(acc);
      acc += f;
    }
  }
  const activeIndex = Math.max(
    0,
    Math.min(
      keyPoints.length - 1,
      relativeStarts.findIndex((start, i) => {
        const next = relativeStarts[i + 1] ?? Number.POSITIVE_INFINITY;
        return localFrame >= start && localFrame < next;
      }),
    ),
  );
  const active = keyPoints[activeIndex] ?? keyPoints[0];
  const segmentStart = relativeStarts[activeIndex] ?? 0;
  const segmentFrame = Math.max(0, localFrame - segmentStart);
  const titleOpacity = interpolate(segmentFrame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const titleY = interpolate(segmentFrame, [0, 18], [40, 0], { extrapolateRight: "clamp" });
  const bodyOpacity = interpolate(segmentFrame, [10, 30], [0, 1], { extrapolateRight: "clamp" });

  if (variant === "caption_intro") {
    return (
      <AbsoluteFill style={{ background: "transparent", padding: "88px 66px", justifyContent: "center", alignItems: "center" }}>
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1, textAlign: "center", maxWidth: 930 }}>
          <div style={{ display: "inline-flex", border: `1px solid ${accent}66`, color: accent, borderRadius: 999, padding: "8px 18px", fontSize: 18, fontWeight: 800, letterSpacing: 4, textTransform: "uppercase", marginBottom: 34 }}>Cinematic Intro</div>
          <h2 style={{ color: C.textPrimary, fontSize: Math.round(82 * fs), lineHeight: 1.05, margin: 0, opacity: titleOpacity, transform: `translateY(${titleY}px)`, textShadow: `0 0 86px ${accent}55` }}>
            <HighlightedText text={active?.title ?? ""} style={{}} highlightColor={hl} emphasisTerms={active?.emphasisTerms} />
          </h2>
          <p style={{ color: C.textSecondary, fontSize: Math.round(31 * fs), lineHeight: 1.5, margin: "34px auto 0", opacity: bodyOpacity, maxWidth: 820 }}>{active?.body}</p>
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "cta_overlay") {
    return (
      <AbsoluteFill style={{ background: "transparent", padding: "72px 58px", justifyContent: "center" }}>
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1, maxWidth: 900 }}>
          <div style={{ color: accent, fontSize: 18, fontWeight: 800, letterSpacing: 5, textTransform: "uppercase", marginBottom: 32 }}>CTA Overlay</div>
          <h2 style={{ color: C.textPrimary, fontSize: Math.round(68 * fs), lineHeight: 1.08, margin: 0, opacity: titleOpacity, transform: `translateY(${titleY}px)` }}>
            <HighlightedText text={active?.title ?? ""} style={{}} highlightColor={hl} emphasisTerms={active?.emphasisTerms} />
          </h2>
          <p style={{ color: C.textSecondary, fontSize: Math.round(31 * fs), lineHeight: 1.5, margin: "30px 0 0", opacity: bodyOpacity }}>{active?.body}</p>
        </div>
        <div style={{ position: "absolute", left: 58, right: 58, bottom: 72, background: "rgba(15,23,42,0.88)", border: `1px solid ${accent}77`, borderRadius: 22, padding: "24px 28px", display: "flex", alignItems: "center", justifyContent: "space-between", boxShadow: `0 0 42px ${accent}33` }}>
          <div style={{ color: C.textPrimary, fontSize: 30, fontWeight: 900 }}>继续关注这条 AI 变化</div>
          <div style={{ background: `linear-gradient(135deg, ${accent}, ${hl})`, color: C.bg, borderRadius: 999, padding: "12px 22px", fontSize: 22, fontWeight: 900 }}>NEXT</div>
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ background: "transparent", padding: "72px 58px", justifyContent: "center" }}>
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
      <div style={{ position: "relative", zIndex: 1 }}>
        <div style={{ color: accent, fontSize: 18, fontWeight: 800, letterSpacing: 5, textTransform: "uppercase", marginBottom: 38 }}>
          Caption Story · {String(activeIndex + 1).padStart(2, "0")} / {keyPoints.length}
        </div>
        <h2 style={{ color: C.textPrimary, fontSize: Math.round(74 * fs), lineHeight: 1.08, letterSpacing: 0, margin: 0, opacity: titleOpacity, transform: `translateY(${titleY}px)`, textShadow: `0 0 70px ${accent}44` }}>
          <HighlightedText text={active?.title ?? ""} style={{}} highlightColor={hl} emphasisTerms={active?.emphasisTerms} />
        </h2>
        <div style={{ width: 150, height: 6, borderRadius: 999, background: `linear-gradient(90deg, ${accent}, ${hl})`, marginTop: 34, marginBottom: 34, opacity: titleOpacity }} />
        <p style={{ color: C.textSecondary, fontSize: Math.round(34 * fs), lineHeight: 1.5, margin: 0, opacity: bodyOpacity, maxWidth: 900 }}>
          <HighlightedText text={active?.body ?? ""} style={{}} highlightColor={hl} emphasisTerms={active?.emphasisTerms} />
        </p>
      </div>
      <div style={{ position: "absolute", left: 58, right: 58, bottom: 58, display: "flex", gap: 10 }}>
        {keyPoints.map((_, i) => (
          <div key={i} style={{ flex: 1, height: 7, borderRadius: 999, background: i <= activeIndex ? `linear-gradient(90deg, ${accent}, ${hl})` : C.surface, opacity: i === activeIndex ? 1 : 0.55 }} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

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
          background: "transparent",
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 50px",
        }}
      >
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1, maxWidth: 950, width: "100%" }}>
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
          background: "transparent",
          justifyContent: "center",
          alignItems: "center",
          padding: "80px 100px",
        }}
      >
        {/* V1.2.1.4: Background layer */}
        <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
        <div style={{ position: "relative", zIndex: 1, maxWidth: 800, width: "100%" }}>
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
        background: "transparent",
        justifyContent: "center",
        alignItems: "center",
        padding: "60px 50px",
      }}
    >
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
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

      <div style={{ position: "relative", zIndex: 1, maxWidth: 900, width: "100%" }}>
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

const ReportOpeningPage: React.FC<{
  title: string;
  overview?: ReportOverview;
  keyPoints: KeyPoint[];
  duration: number;
  vstyle?: RemotionStyle;
}> = ({ title, overview, keyPoints, duration, vstyle }) => {
  const frame = useCurrentFrame();
  const fs = vstyle?.fontScale || 1;
  const accent = vstyle?.accentColor ?? C.accent;
  const hl = vstyle?.highlightColor ?? C.highlight;
  const opacity = interpolate(frame, [0, Math.min(12, duration * 0.18)], [0.92, 1], { extrapolateRight: "clamp" });
  const y = interpolate(frame, [0, Math.min(14, duration * 0.2)], [10, 0], { extrapolateRight: "clamp" });
  const summary = overview?.summary || "";
  const openingTitle = overview?.title || title || "内容概览";

  // V1.2.2: Use layout config for aspect-ratio-aware density
  const layout = getLayoutConfig(vstyle?.aspectRatioLayoutMode);
  const maxItems = Math.min(layout.coverMaxPreviewItems, keyPoints.length);

  return (
    <AbsoluteFill style={{ background: "transparent", padding: 72, color: C.textPrimary, fontFamily: "sans-serif" }}>
      {/* V1.2.1.4: Background layer */}
      <BackgroundLayer preset={vstyle?.backgroundPreset} accent={accent} highlight={hl} />
      <div style={{
        position: "relative",
        height: "100%",
        border: `2px solid ${accent}66`,
        borderRadius: 28,
        padding: 48,
        background: "rgba(15, 23, 42, 0.72)",
        boxShadow: `0 0 120px ${accent}22`,
        opacity,
        transform: `translateY(${y}px)`,
        overflow: "hidden",
        zIndex: 1,
        display: "flex",
        flexDirection: "column",
        gap: 0,
      }}>
        <div style={{ color: accent, fontSize: Math.round(22 * fs), fontWeight: 800, marginBottom: 14 }}>
          首页总览
        </div>
        <h1 style={{ fontSize: Math.round(layout.coverTitleFontSize * fs), lineHeight: 1.12, margin: 0, marginBottom: 10, fontWeight: 900 }}>
          {openingTitle}
        </h1>
        {summary && (
          <>
            <div style={{ width: 120, height: 4, borderRadius: 999, background: `linear-gradient(90deg, ${accent}, ${hl})`, margin: "12px 0" }} />
            <p style={{ fontSize: Math.round(layout.coverSubtitleFontSize * fs), lineHeight: 1.55, color: C.textSecondary, margin: 0, marginBottom: 18 }}>
              {truncateText(summary, 80)}
            </p>
          </>
        )}
        <div style={{ color: hl, fontSize: Math.round(20 * fs), fontWeight: 800, marginBottom: 12 }}>
          本期信息点
        </div>
        {/* V1.2.2: Show previews with descriptions using layout config */}
        <div style={{ display: "grid", gap: layout.coverPreviewGap, flex: 1, alignContent: "flex-start" }}>
          {keyPoints.slice(0, maxItems).map((kp, i) => (
            <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", color: C.textPrimary }}>
              <span style={{ color: accent, fontSize: Math.round(layout.coverPreviewTitleFontSize * fs), fontWeight: 900, flexShrink: 0, marginTop: 1 }}>
                {String(i + 1).padStart(2, "0")}
              </span>
              <div style={{ flex: 1, overflow: "hidden" }}>
                <div style={{ fontSize: Math.round(layout.coverPreviewTitleFontSize * fs), lineHeight: 1.25, fontWeight: 700, marginBottom: 3, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {kp.title}
                </div>
                {kp.body && (
                  <div style={{ fontSize: Math.round(layout.coverPreviewDescFontSize * fs), color: C.textMuted, lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {truncateText(kp.body, 56)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// V0.3.9: Main Video Component with transitionStyle and style variant support
// V0.6.2: Card Stack support via remotionFamily prop
export const AiNewsVideo: React.FC<AiNewsVideoProps> = ({
  title,
  subtitle,
  keyPoints,
  durationSec,
  segmentDurations,
  style,
  showDataViz = true,
  remotionFamily = "data_news",
  structureType,
  reportOverview,
}) => {
  const { fps } = useVideoConfig();

  // V0.3.9: Extract style variants
  const motionScale = getMotionScale(style);
  const transitionStyle = style?.transitionStyle ?? "slide_fade";
  const coverStyle = style?.coverStyle ?? "editorial";
  const overviewStyle = style?.overviewStyle ?? "timeline";
  const isReportSourceBound = structureType === "report_source_bound";

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

  // Scale durations by motion intensity (only for non-aligned fallback mode).
  // V0.8.1: useAligned mode forbids motionIntensity from scaling scene duration,
  // because those durations are already aligned with real TTS audio. motionIntensity
  // may still affect animation speeds inside each scene, but not scene length.
  const scaleDuration = (frames: number) => Math.round(frames / motionScale);

  const coverFrames = useAligned
    ? Math.max(30, Math.round(segmentDurations!.coverSec * fps))
    : scaleDuration(FIXED_COVER);
  const cardFramesArr = useAligned
    ? segmentDurations!.cardSecs.map((s) => Math.max(45, Math.round(s * fps)))
    : keyPoints.map(() => scaleDuration(FIXED_CARD));
  const summaryFrames = useAligned
    ? (segmentDurations!.summarySec > 0 ? Math.max(30, Math.round(segmentDurations!.summarySec * fps)) : 0)
    : scaleDuration(FIXED_SUMMARY);

  // Safe overlap: in useAligned mode, clamp to <= 6 to avoid creating timeline
  // gaps that no longer match audio. Last Summary never relies on overlap to fill tail.
  const safeOverlap = useAligned
    ? (isReportSourceBound ? 0 : Math.min(transitionOverlap, 6))
    : transitionOverlap;

  // V0.8.1: scene semantic start must strictly follow segmentDurations order.
  // transitionOverlap may visually overlap a scene onto the next, but cannot move
  // the start of the next scene earlier (which used to cause audio/video desync
  // and missing summary / premature black screen).
  const cardStarts: number[] = [];
  let acc = coverFrames;
  for (const f of cardFramesArr) {
    cardStarts.push(acc);
    acc += f;
  }
  const summaryStart = acc;
  const totalVisualFrames =
    coverFrames + cardFramesArr.reduce((a, b) => a + b, 0) + summaryFrames;

  // V0.8.1 self-check fields (kept as comments / unused-var OK for debugging exports later):
  // useAligned, coverFrames, cardFramesArr, summaryFrames, summaryStart, totalVisualFrames
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _timelineDebug = {
    useAligned,
    coverFrames,
    cardFramesArr,
    summaryFrames,
    cardStarts,
    summaryStart,
    totalVisualFrames,
    safeOverlap,
  };

  return (
    <AbsoluteFill style={{ background: "transparent" }}>
      {/* V1.2.1.4: Programmatic background layer at root — individual pages can override */}
      <BackgroundLayer preset={style?.backgroundPreset} accent={style?.accentColor} highlight={style?.highlightColor} />
      {/* Cover / report opening */}
      <Sequence from={0} durationInFrames={coverFrames + safeOverlap}>
        {isReportSourceBound ? (
          <ReportOpeningPage
            title={title}
            overview={reportOverview || { title, summary: subtitle }}
            keyPoints={keyPoints}
            duration={coverFrames}
            vstyle={style}
          />
        ) : (
          <CoverPage
            title={title}
            subtitle={subtitle}
            keyPoints={keyPoints}
            duration={coverFrames}
            coverStyle={coverStyle}
            vstyle={style}
          />
        )}
      </Sequence>

      {/* Key Point Cards with transition-aware timing */}
      {/* V0.6.2: Card Stack vs default data_news layout */}
      {/* V0.8.9: Add timeline_news — vertical event-evolution timeline, all nodes
          visible simultaneously with current node highlighted. */}
      {remotionFamily === "card_stack" ? (
        <CardStackLayout
          keyPoints={keyPoints}
          cardStarts={cardStarts}
          cardFramesArr={cardFramesArr}
          transitionOverlap={safeOverlap}
          fps={fps}
          vstyle={style}
          showDataViz={showDataViz}
        />
      ) : remotionFamily === "timeline_news" ? (
        // V0.8.9: Wrap the entire card section in one Sequence so TimelineNewsLayout
        // can see the local frame and decide which node is active. cardStarts[0] ===
        // coverFrames by construction, so the local frame == (absoluteFrame - coverFrames).
        <Sequence
          from={coverFrames}
          durationInFrames={Math.max(1, summaryStart - coverFrames + safeOverlap)}
        >
          <TimelineNewsLayout
            keyPoints={keyPoints}
            cardStarts={cardStarts}
            cardFramesArr={cardFramesArr}
            transitionOverlap={safeOverlap}
            fps={fps}
            vstyle={style}
            showDataViz={showDataViz}
          />
        </Sequence>
      ) : remotionFamily === "dashboard_brief" ? (
        <Sequence
          from={coverFrames}
          durationInFrames={Math.max(1, summaryStart - coverFrames + safeOverlap)}
        >
          <DashboardBriefLayout
            keyPoints={keyPoints}
            cardStarts={cardStarts}
            cardFramesArr={cardFramesArr}
            transitionOverlap={safeOverlap}
            fps={fps}
            vstyle={style}
            showDataViz={showDataViz}
          />
        </Sequence>
      ) : remotionFamily === "caption_story" ? (
        <Sequence
          from={coverFrames}
          durationInFrames={Math.max(1, summaryStart - coverFrames + safeOverlap)}
        >
          <CaptionStoryLayout
            keyPoints={keyPoints}
            cardStarts={cardStarts}
            cardFramesArr={cardFramesArr}
            transitionOverlap={safeOverlap}
            fps={fps}
            vstyle={style}
            showDataViz={showDataViz}
          />
        </Sequence>
      ) : (
        keyPoints.map((kp, i) => (
          <Sequence
            key={i}
            from={cardStarts[i]}
            durationInFrames={cardFramesArr[i] + safeOverlap}
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
        ))
      )}

      {/* Summary with transition-aware timing.
          V0.8.1: no transitionOverlap on Summary — Summary is the last scene and
          must exactly match the audio tail; padding it would push it past total duration. */}
      {summaryFrames > 0 && (
        <Sequence from={summaryStart} durationInFrames={summaryFrames}>
          <SummaryPage
            title={title}
            keyPoints={keyPoints}
            overviewStyle={overviewStyle}
            vstyle={style}
          />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};

export default AiNewsVideo;
