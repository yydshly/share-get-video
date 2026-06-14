/**
 * Template Review - V0.2.5
 * Template acceptance suggestions based on experiment result and evaluation
 */

import type { VideoExperimentResult, VideoExperimentEvaluation } from "../types";

export interface TemplateReviewResult {
  templateStatus: "usable" | "needs_tuning" | "not_ready";
  scoreSummary: string;
  parameterSuggestions: string[];
  nextActions: string[];
}

/**
 * Generate template review suggestions based on result and evaluation.
 */
export function buildTemplateReview(
  result: VideoExperimentResult,
  evaluation: VideoExperimentEvaluation | null | undefined,
): TemplateReviewResult {
  const parameterSuggestions: string[] = [];
  const nextActions: string[] = [];

  // If no evaluation, needs tuning
  if (!evaluation) {
    return {
      templateStatus: "needs_tuning",
      scoreSummary: "暂无人工评分，需要先完成评分才能给出模板验收结论",
      parameterSuggestions: [],
      nextActions: ["请先完成人工评分"],
    };
  }

  // Use averageScore field (from API) or compute from individual dimensions
  const avgScore = (evaluation as Record<string, unknown>).averageScore as number | null;
  const visualQuality = (evaluation as Record<string, unknown>).visualQuality as number;
  const readability = (evaluation as Record<string, unknown>).readability as number;
  const pacing = (evaluation as Record<string, unknown>).pacing as number;
  const shareability = (evaluation as Record<string, unknown>).shareability as number;

  let templateStatus: TemplateReviewResult["templateStatus"] = "needs_tuning";

  // Determine template status based on average score
  if (avgScore !== null && avgScore >= 4) {
    templateStatus = "usable";
  } else if (avgScore !== null && avgScore < 2.5) {
    templateStatus = "not_ready";
  } else {
    templateStatus = "needs_tuning";
  }

  // Build score summary
  let scoreSummary = "";
  if (avgScore !== null) {
    scoreSummary = `综合评分: ${avgScore.toFixed(1)}/5`;
  } else {
    scoreSummary = "评分不足";
  }

  // Parameter suggestions based on low scores
  if (visualQuality > 0 && visualQuality <= 3) {
    parameterSuggestions.push("优化封面/背景/字号/卡片层次以提升视觉质量");
  }

  if (readability > 0 && readability <= 3) {
    parameterSuggestions.push("减少 keyPointCount 或增加单帧时长以提升可读性");
  }

  if (pacing > 0 && pacing <= 3) {
    parameterSuggestions.push("调整 targetDuration 或 transitionFrames 以优化节奏");
  }

  if (shareability > 0 && shareability <= 3) {
    parameterSuggestions.push("优化封面标题和 CTA 以提升分享意愿");
  }

  // Build next actions based on status
  if (templateStatus === "usable") {
    nextActions.push("可作为当前 AI 资讯视频默认模板");
    nextActions.push("建议使用当前参数固化模板配置");
    if (parameterSuggestions.length > 0) {
      nextActions.push("小幅优化后可进入 V0.3 Remotion 方案评估");
    }
  } else if (templateStatus === "needs_tuning") {
    nextActions.push("根据评分调整生成参数后重新验证");
    if (avgScore !== null && avgScore < 3) {
      nextActions.push("评分偏低，建议优先解决可读性和视觉质量问题");
    }
  } else {
    nextActions.push("评分过低，不建议作为默认模板");
    nextActions.push("需要重大改进后再评估产品化价值");
  }

  return {
    templateStatus,
    scoreSummary,
    parameterSuggestions,
    nextActions,
  };
}
