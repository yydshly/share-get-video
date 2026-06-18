export interface VisualStylePresetDefinition {
  id: "light_editorial" | "warm_paper" | "bold_magazine";
  label: string;
  shortLabel: string;
  positioning: string;
  tone: string;
  suitable: string;
  motion: string;
  evaluationFocus: string;
  colors: {
    background: string;
    surface: string;
    text: string;
    accent: string;
    highlight: string;
    border: string;
  };
}

export const VISUAL_STYLE_PRESETS: VisualStylePresetDefinition[] = [
  {
    id: "light_editorial",
    label: "浅色编辑",
    shortLabel: "清爽资讯",
    positioning: "面向资讯、产品动态和轻量知识内容的清晰编辑风格。",
    tone: "白色与浅灰底，深色正文，蓝青色强调。",
    suitable: "AI 资讯、工具推荐、创业公司动态、产品更新",
    motion: "柔和、克制，优先保证留白和文字可读性。",
    evaluationFocus: "浅色表面是否真实生效，正文与数据是否保持足够对比度。",
    colors: {
      background: "#ffffff",
      surface: "#f8fafc",
      text: "#0f172a",
      accent: "#3b82f6",
      highlight: "#0ea5e9",
      border: "#e2e8f0",
    },
  },
  {
    id: "warm_paper",
    label: "暖纸报告",
    shortLabel: "稳重报告",
    positioning: "面向报告、研究摘要和专业解读的纸张质感风格。",
    tone: "米白纸张底，深棕正文，琥珀与橙色强调。",
    suitable: "咨询报告、行业研究、论文解读、正式新闻",
    motion: "克制、沉稳，减少高频闪动和大面积辉光。",
    evaluationFocus: "暖色纸张是否区别于纯白，卡片和图表是否仍然清楚。",
    colors: {
      background: "#faf8f5",
      surface: "#f5f0e8",
      text: "#292524",
      accent: "#b45309",
      highlight: "#d97706",
      border: "#e7e5e4",
    },
  },
  {
    id: "bold_magazine",
    label: "高对比杂志",
    shortLabel: "爆点表达",
    positioning: "面向突发新闻和观点短评的高冲击杂志封面风格。",
    tone: "近黑背景，纯白正文，红橙色强强调。",
    suitable: "突发新闻、观点短评、趋势判断、爆点资讯",
    motion: "更有力量和节奏，但不能牺牲正文可读性。",
    evaluationFocus: "红橙强调是否明显，黑白层级是否避免重新退化成科技蓝。",
    colors: {
      background: "#0a0a0a",
      surface: "#18181b",
      text: "#fafafa",
      accent: "#ef4444",
      highlight: "#f97316",
      border: "#27272a",
    },
  },
];

export const VISUAL_STYLE_EXPLORATION_DIRECTIONS = [
  {
    id: "pastel_glass",
    label: "粉彩玻璃",
    summary: "粉蓝、淡紫与毛玻璃表面，适合轻产品和生活方式内容。",
  },
  {
    id: "apple_keynote",
    label: "产品发布会",
    summary: "极简深色舞台、大字号标题与缓慢镜头感。",
  },
  {
    id: "calm_enterprise",
    label: "企业咨询",
    summary: "低饱和企业色、结构化信息和高密度专业表达。",
  },
];

export const VISUAL_STYLE_MATRIX_FAMILIES = [
  { id: "data_news", name: "Data News", color: "#7c3aed" },
  { id: "dashboard_brief", name: "Dashboard", color: "#f59e0b" },
  { id: "caption_story", name: "Caption Story", color: "#ec4899" },
];
