// data.ts - Shared types for Remotion template
// V0.3.6-b1: Added emphasisTerms to KeyPoint

export type KeyPoint = {
  title: string;
  body: string;
  source?: string;
  // V0.3.6-b1: explicit emphasis terms for highlight; falls back to auto-extract
  emphasisTerms?: string[];
};

export type SegmentDurations = {
  coverSec: number;
  cardSecs: number[];
  summarySec: number;
};

export type AiNewsVideoProps = {
  title: string;
  subtitle?: string;
  keyPoints: KeyPoint[];
  durationSec: number;
  stylePreset: "ai_frontier_dark";
  // 每段时长（与旁白对齐）；缺省时模板用固定时长
  segmentDurations?: SegmentDurations;
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
