// data.ts - Shared types for Remotion template
// V0.3.6-b1: Added emphasisTerms to KeyPoint
// V0.3.6-quality-p0: Added metrics to KeyPoint

export type Metric = {
  label: string;
  value: number;
  unit: string;
  min?: number;
  max?: number;
};

export type KeyPoint = {
  title: string;
  body: string;
  source?: string;
  // V0.3.6-b1: explicit emphasis terms for highlight; falls back to auto-extract
  emphasisTerms?: string[];
  // V0.3.6-quality-p0: data visualization metrics
  metrics?: Metric[];
  // 主题自适应：positive | negative | neutral（驱动配色/图标）
  tone?: string;
};

export type SegmentDurations = {
  coverSec: number;
  cardSecs: number[];
  summarySec: number;
};

// V0.3.9: Extended style types for motion/visual customization
export type MotionIntensity = "low" | "medium" | "high";
export type CoverStyle = "editorial" | "cinematic" | "minimal";
export type OverviewStyle = "timeline" | "grid" | "clean";
export type MetricAnimation = "countup_bar" | "countup_number" | "none";
export type TransitionStyle = "slide_fade" | "fade" | "slide";

export type RemotionStyle = {
  accentColor?: string;     // 主题强调色（标号/分隔线/数据条/图标）
  highlightColor?: string;  // 关键词/数字高亮色
  fontScale?: number;       // 字号缩放（排版清晰度），如 1.1
  showIcon?: boolean;       // 是否在卡片显示视觉图标元素
  // V0.3.9: Motion & style enhancements
  motionIntensity?: MotionIntensity;   // 动画强弱: low(0.75x) / medium(1x) / high(1.25x)
  coverStyle?: CoverStyle;              // 封面风格: editorial / cinematic / minimal
  overviewStyle?: OverviewStyle;         // 概览风格: timeline / grid / clean
  metricAnimation?: MetricAnimation;    // 指标动画: countup_bar / countup_number / none
  transitionStyle?: TransitionStyle;   // 转场风格: slide_fade / fade / slide
};

// V0.6.2: Remotion family — selects visual presentation paradigm
// V0.8.9: Added "timeline_news" for AI news event evolution timelines.
export type RemotionFamily = "data_news" | "card_stack" | "timeline_news";

export type AiNewsVideoProps = {
  title: string;
  subtitle?: string;
  keyPoints: KeyPoint[];
  durationSec: number;
  stylePreset: "ai_frontier_dark";
  // 每段时长（与旁白对齐）；缺省时模板用固定时长
  segmentDurations?: SegmentDurations;
  // 可调样式（对应调试台旋钮：配色/字号/图标）
  style?: RemotionStyle;
  // V0.3.6-quality-p0-fix: showDataViz=false suppresses metrics animation
  showDataViz?: boolean;
  // V0.6.2: Remotion family — data_news (default) | card_stack
  // V0.8.9: Added timeline_news — vertical event-evolution timeline layout.
  remotionFamily?: RemotionFamily;
};

export const defaultProps: AiNewsVideoProps = {
  title: "AI 前沿动态",
  subtitle: "今日 AI 资讯速览",
  keyPoints: [
    {
      title: "GPT-5 发布",
      body: "OpenAI 发布 GPT-5，性能显著提升",
      source: "OpenAI",
      emphasisTerms: ["GPT-5", "OpenAI"],
    },
    {
      title: "Claude 4 发布",
      body: "Anthropic 发布 Claude 4，强化推理能力",
      source: "Anthropic",
      emphasisTerms: ["Claude 4", "Anthropic"],
    },
  ],
  durationSec: 45,
  stylePreset: "ai_frontier_dark",
};
