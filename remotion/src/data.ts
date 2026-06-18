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

export type ReportOverview = {
  title?: string;
  summary?: string;
};

// V0.3.9: Extended style types for motion/visual customization
export type MotionIntensity = "low" | "medium" | "high";
export type CoverStyle = "editorial" | "cinematic" | "minimal";
export type OverviewStyle = "timeline" | "grid" | "clean";
export type MetricAnimation = "countup_bar" | "countup_number" | "none";
export type TransitionStyle = "slide_fade" | "fade" | "slide" | "push" | "wipe" | "zoom_blur" | "flip" | "glitch";
export type FamilyVariant =
  | "chart_story"
  | "ranking_strip"
  | "route_map"
  | "caption_intro"
  | "cta_overlay";

// V1.2.2: Aspect-ratio-aware layout mode — drives density and sizing per canvas ratio
export type AspectRatioLayoutMode = "vertical_compact" | "horizontal_balanced" | "square_compact";

// V1.2.1.4: Background preset for programmatic CSS backgrounds
export type BackgroundPreset =
  | "tech_grid_dark"   // 深蓝黑底 + 细网格 + 蓝色柔光（通用科技新闻）
  | "aurora_blue"       // 蓝紫极光渐变 + 大面积 radial glow（Card Stack 默认）
  | "glass_dashboard"   // 深色 dashboard 感 + 半透明几何块（Data News 默认）
  | "warm_cinematic"    // 暖色暗背景 + 柔光 + 电影感
  | "neon_circuit"      // neon circuit grid + pulse nodes + scan sweep
  | "deep_space";       // deep starfield + orbital arcs + drifting nebula

// V1.2.4: Visual style preset — overall visual tone overrides
export type VisualStylePreset = "light_editorial" | "warm_paper" | "bold_magazine";

// V1.2.4: Visual technique —特色表现技法
// V1.2.5: + blueprint（深蓝晒图纸 + 白色工程线，与 academic_sketch 暖纸冷暖对照）
// V1.2.5+: + data_viz_dashboard, agent_sandbox_25d, kinetic_code_typography
// V1.2.3: + 12 new prototype techniques for Remotion Lab effect prototype library
export type VisualTechnique =
  | "academic_sketch"
  | "blueprint"
  | "data_viz_dashboard"
  | "agent_sandbox_25d"
  | "kinetic_code_typography"
  | "whiteboard_explainer"
  | "benchmark_ranking"
  | "architecture_diagram"
  | "product_demo_flow"
  | "launch_countdown"
  | "map_timeline"
  | "audio_visualizer"
  | "tiktok_caption_story"
  | "magazine_headline"
  | "capability_radar"
  | "timeline_recap"
  | "lottie_icon_story";

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
  familyVariant?: FamilyVariant;
  // V1.2.1.4: Background preset — controls CSS background of each page
  backgroundPreset?: BackgroundPreset;
  // V1.2.1.4: Card Stack visual peek frames (independent of audio/segment timing)
  cardStackPeekFrames?: number;
  // V1.2.2: Aspect-ratio-aware layout mode — drives density and sizing per output ratio
  aspectRatioLayoutMode?: AspectRatioLayoutMode;
  // V1.2.x: Debug switch — show PREV/NEXT stack labels on card layers
  debugStackLabels?: boolean;
  // V1.2.4: Visual style preset — overall visual tone (light/warm/bold)
  visualStylePreset?: VisualStylePreset;
  // V1.2.4: Visual technique — academic_sketch (paper-like, grid, hand-drawn)
  visualTechnique?: VisualTechnique;
  // V1.2.3: Lab-only content probe — forces a visible content layer in Visual Technique Matrix
  visualTechniqueContentProbe?: boolean;
  visualTechniqueFixtureId?: string;
  visualTechniqueMatrixMode?: "technique_compare" | "family_adaptation";
  // V1.2.3: Lab-only debug label — shows STYLE + FAMILY tag in the rendered output
  showVisualStyleDebugLabel?: boolean;
};

// V0.6.2: Remotion family — selects visual presentation paradigm
// V0.8.9: Added "timeline_news" for AI news event evolution timelines.
export type RemotionFamily =
  | "data_news"
  | "card_stack"
  | "timeline_news"
  | "dashboard_brief"
  | "caption_story";

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
  structureType?: "report_source_bound" | string;
  reportOverview?: ReportOverview;
  sourceRefs?: Array<{ itemIndex: number; itemTitle: string; evidence: string[] }>;
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
