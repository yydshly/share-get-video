// data.ts - Shared types for Remotion template
// V0.3.1 minimum verification

export type KeyPoint = {
  title: string;
  body: string;
  source?: string;
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
    },
    {
      title: "Claude 4 发布",
      body: "Anthropic 发布 Claude 4，强化推理能力",
      source: "Anthropic",
    },
  ],
  durationSec: 45,
  stylePreset: "ai_frontier_dark",
};
