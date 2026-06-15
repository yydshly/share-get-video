/**
 * videoRoutePresets.ts - 三条技术路线的候选 preset 配置
 *
 * V0.3.7: Route-specific configuration — 每条路线独立配置、独立风格、独立 preset
 *
 * 路线定位：
 * - pillow:  稳定信息卡 / 批量生成 / 兜底路线
 * - remotion: React 时间轴动画 / 动态栏目模板 / 产品化视频模板
 * - ai_asset: AI 背景图 / 氛围视觉 / 展示型短视频
 */

// ─── 类型定义 ────────────────────────────────────────────────────────────────

export type VideoRouteId = "local_frame_compose" | "template_programmatic_render" | "ai_asset_then_compose";

export interface PillowParams {
  /** 显示数据可视化（metrics 卡） */
  showDataViz: boolean;
  /** 高亮模式：auto / numbers / none */
  highlightMode: "auto" | "numbers" | "none";
  /** 内容对齐：top / center */
  contentAlign: "top" | "center";
  /** 主题自适应（自动配色/图标） */
  themeAdaptive: boolean;
  /** 转场开关 */
  transitionEnabled: boolean;
  /** 转场帧数 */
  transitionFrames: number;
  /** 标题颜色 */
  titleColor: string;
  /** 正文颜色 */
  bodyColor: string;
  /** 高亮颜色 */
  highlightColor: string;
}

export interface RemotionParams {
  /** 显示数据可视化 */
  showDataViz: boolean;
  /** 主题色 */
  accentColor: string;
  /** 高亮颜色 */
  highlightColor: string;
  /** 字号缩放 */
  fontScale: number;
  /** 显示图标 */
  showIcon: boolean;
  /** 动效强度：low / medium / high */
  motionIntensity: "low" | "medium" | "high";
  /** 封面风格：editorial / cinematic / minimal */
  coverStyle: "editorial" | "cinematic" | "minimal";
  /** 概览页风格：timeline / grid / clean */
  overviewStyle: "timeline" | "grid" | "clean";
  /** 指标动画：countup_bar / countup_number / none */
  metricAnimation: "countup_bar" | "countup_number" | "none";
  /** 转场风格：slide_fade / fade / slide */
  transitionStyle: "slide_fade" | "fade" | "slide";
}

export interface AiAssetParams {
  /** 显示数据可视化 */
  showDataViz: boolean;
  /** AI 背景图风格提示词 */
  imageStyle: string;
  /** 背景暗化程度 0-1 */
  backgroundDarken: number;
  /** 信息卡透明度 0-1 */
  cardOpacity: number;
  /** 卡片背景模糊 */
  cardBlur: boolean;
  /** 高亮颜色 */
  highlightColor: string;
  /** 内容对齐：top / center */
  contentAlign: "top" | "center";
  /** Ken Burns 动效 */
  kenBurns: boolean;
}

export interface VideoRoutePreset {
  id: string;
  /** 对应 VisualRoute routeId */
  route: VideoRouteId;
  name: string;
  label: string;
  description: string;
  /** 简介，一句话说明定位 */
  tagline: string;
  /** 核心展示能力列表 */
  capabilities: string[];
  /** 完整参数 */
  params: PillowParams | RemotionParams | AiAssetParams;
}

// ─── 候选 Preset ──────────────────────────────────────────────────────────────

const PILLOW_DATA_CARD_V1: VideoRoutePreset = {
  id: "pillow_data_card_v1_candidate",
  route: "local_frame_compose",
  name: "pillow_data_card_v1_candidate",
  label: "数据信息卡",
  tagline: "稳定排版 · 长文本可读 · 数据卡清晰 · 成本低 · 依赖少",
  description:
    "Pillow 信息卡路线：适合稳定批量生成。长文本可读性强，数据卡清晰，依赖少，成本低。",
  capabilities: [
    "稳定排版",
    "长文本可读",
    "数据卡清晰",
    "成本低",
    "依赖少",
  ],
  params: {
    showDataViz: true,
    highlightMode: "auto",
    contentAlign: "top",
    themeAdaptive: true,
    transitionEnabled: true,
    transitionFrames: 4,
    titleColor: "#f8fafc",
    bodyColor: "#94a3b8",
    highlightColor: "#f59e0b",
  } as PillowParams,
};

const REMOTION_METRIC_MOTION_V1: VideoRoutePreset = {
  id: "remotion_metric_motion_v1_candidate",
  route: "template_programmatic_render",
  name: "remotion_metric_motion_v1_candidate",
  label: "动态指标模板",
  tagline: "数字滚动 · 进度条生长 · 卡片入场 · 页面转场",
  description:
    "Remotion 动态模板路线：React 时间轴动画，数字滚动、进度条生长、卡片入场、页面转场，完整模板系统。",
  capabilities: [
    "数字滚动",
    "进度条生长",
    "卡片入场",
    "页面转场",
    "封面/概览/重点页完整模板",
  ],
  params: {
    showDataViz: true,
    accentColor: "#3b82f6",
    highlightColor: "#f59e0b",
    fontScale: 1,
    showIcon: true,
    motionIntensity: "medium",
    coverStyle: "editorial",
    overviewStyle: "timeline",
    metricAnimation: "countup_bar",
    transitionStyle: "slide_fade",
  } as RemotionParams,
};

const AI_ASSET_TECH_MOOD_V1: VideoRoutePreset = {
  id: "ai_asset_tech_mood_v1_candidate",
  route: "ai_asset_then_compose",
  name: "ai_asset_tech_mood_v1_candidate",
  label: "AI 氛围视觉",
  tagline: "AI 背景图 · 科技感氛围 · 封面感 · 背景+信息卡融合",
  description:
    "AI 素材氛围路线：AI 生成背景图，科技感氛围，封面感强，背景+信息卡融合，传播型视觉。",
  capabilities: [
    "AI 生成背景",
    "科技感氛围",
    "封面感",
    "背景+信息卡融合",
    "传播型视觉",
  ],
  params: {
    showDataViz: true,
    imageStyle: "深蓝科技数据可视化背景，未来感，抽象光线，电影质感，无文字，无文本，柔和景深",
    backgroundDarken: 0.55,
    cardOpacity: 0.85,
    cardBlur: true,
    highlightColor: "#f59e0b",
    contentAlign: "top",
    kenBurns: true,
  } as AiAssetParams,
};

// ─── 注册表 ──────────────────────────────────────────────────────────────────

export const VIDEO_ROUTE_PRESETS: VideoRoutePreset[] = [
  PILLOW_DATA_CARD_V1,
  REMOTION_METRIC_MOTION_V1,
  AI_ASSET_TECH_MOOD_V1,
];

// ─── 工具函数 ────────────────────────────────────────────────────────────────

/** 按 routeId 查找候选 preset（每条路线目前只有一个候选） */
export function getPresetForRoute(routeId: string): VideoRoutePreset | undefined {
  return VIDEO_ROUTE_PRESETS.find((p) => p.route === routeId);
}

/** 获取路线的展示名称 */
export const ROUTE_DISPLAY_NAMES: Record<VideoRouteId, string> = {
  local_frame_compose: "Pillow 信息卡",
  template_programmatic_render: "Remotion 动态模板",
  ai_asset_then_compose: "AI 素材氛围",
};

/** 获取路线的 tagline */
export const ROUTE_TAGLINES: Record<VideoRouteId, string> = {
  local_frame_compose: "稳定信息卡 / 批量生成 / 兜底路线",
  template_programmatic_render: "React 时间轴动画 / 动态栏目模板 / 产品化视频模板",
  ai_asset_then_compose: "AI 背景图 / 氛围视觉 / 展示型短视频",
};

/** 判断是否为 Pillow 路线 */
export function isPillowRoute(routeId: string): boolean {
  return routeId === "local_frame_compose";
}

/** 判断是否为 Remotion 路线 */
export function isRemotionRoute(routeId: string): boolean {
  return routeId === "template_programmatic_render";
}

/** 判断是否为 AI Asset 路线 */
export function isAiAssetRoute(routeId: string): boolean {
  return routeId === "ai_asset_then_compose";
}
