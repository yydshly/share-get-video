// experimentSummary.ts - Domain logic for experiment conclusions

import type { VideoExperimentResult, VideoExperimentEvaluation } from "../types";

export interface ExperimentSummary {
  recommendation: "高" | "中" | "低";
  recommendationLabel: string;
  mainStrengths: string[];
  mainProblems: string[];
  nextSteps: string[];
  productizationWorthy: boolean;
  reasoning: string;
}

export function buildExperimentSummary(
  result: VideoExperimentResult,
  evaluation?: VideoExperimentEvaluation | null,
): ExperimentSummary {
  const rawOutput = result.rawOutput as Record<string, unknown> | undefined;
  const ffmpegSuccess = (rawOutput?.ffmpegSuccess as boolean | undefined) ?? false;
  const recommendation = (rawOutput?.productizationRecommendation as string | undefined) ?? "";
  const failed = result.productionSteps.some((s) => s.status === "failed");

  // Compute average score from evaluation if available
  let avgScore: number | null = null;
  if (evaluation) {
    const dims = [
      "informationAccuracy",
      "readability",
      "visualQuality",
      "pacing",
      "shareability",
      "stability",
      "productizationValue",
    ] as const;
    const scores = (dims.map((d) => (evaluation as Record<string, unknown>)[d] as number).filter(Boolean));
    avgScore = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
  }

  const mainStrengths: string[] = [];
  const mainProblems: string[] = [];
  const nextSteps: string[] = [];

  // Experiment failed → low recommendation
  if (failed || !ffmpegSuccess) {
    return {
      recommendation: "低",
      recommendationLabel: "✗ 不推荐",
      mainStrengths: [],
      mainProblems: ["视频合成失败（FFmpeg 不可用或执行错误）"],
      nextSteps: [
        "检查 FFmpeg 是否已安装并加入 PATH",
        "确认 runtime 目录存在且可写",
        "重新运行实验",
      ],
      productizationWorthy: false,
      reasoning: "视频合成步骤失败，无法产出可预览的 MP4，需修复底层问题后再评估。",
    };
  }

  // Evaluate quality dimensions from evaluation if available
  if (evaluation) {
    if ((evaluation as Record<string, unknown>).visualQuality as number) {
      const vq = (evaluation as Record<string, unknown>).visualQuality as number;
      if (vq >= 4) mainStrengths.push("视觉质量良好");
      if (vq <= 3) mainProblems.push("视觉质量有待提升");
    }
    if ((evaluation as Record<string, unknown>).readability as number) {
      const r = (evaluation as Record<string, unknown>).readability as number;
      if (r >= 4) mainStrengths.push("可读性良好");
      if (r <= 3) {
        mainProblems.push("可读性有待提升");
        nextSteps.push("优化中文排版和字幕设计");
      }
    }
    if ((evaluation as Record<string, unknown>).shareability as number) {
      const s = (evaluation as Record<string, unknown>).shareability as number;
      if (s >= 4) mainStrengths.push("分享价值高");
      if (s <= 3) {
        mainProblems.push("分享价值有待提升");
        nextSteps.push("优化封面设计和视频开头");
      }
    }
    if ((evaluation as Record<string, unknown>).stability as number) {
      const st = (evaluation as Record<string, unknown>).stability as number;
      if (st >= 4) mainStrengths.push("稳定性良好");
    }
    if ((evaluation as Record<string, unknown>).informationAccuracy as number) {
      const ia = (evaluation as Record<string, unknown>).informationAccuracy as number;
      if (ia >= 4) mainStrengths.push("信息准确性高");
    }
    if ((evaluation as Record<string, unknown>).pacing as number) {
      const p = (evaluation as Record<string, unknown>).pacing as number;
      if (p <= 3) {
        mainProblems.push("节奏有待优化");
        nextSteps.push("调整帧时长分布");
      }
    }
  }

  // General strengths from raw output
  if (recommendation === "recommended") {
    mainStrengths.push("方案已验证可产出真实 MP4");
    mainStrengths.push("产品化价值高，成本可控");
  }

  // Determine recommendation level
  let rec: "高" | "中" | "低" = "中";
  let recLabel = "○ 备选";

  if (avgScore !== null) {
    if (avgScore >= 4) {
      rec = "高";
      recLabel = "✓ 推荐";
    } else if (avgScore < 3) {
      rec = "低";
      recLabel = "✗ 不推荐";
    }
  }

  if (mainProblems.length === 0 && mainStrengths.length > 0) {
    rec = "高";
    recLabel = "✓ 推荐";
  }

  const reasoning = avgScore !== null
    ? `综合评分 ${avgScore.toFixed(2)}/5，${rec === "高" ? "推荐作为 AI 资讯视频基础方案" : rec === "中" ? "可作为备选方案" : "需优化后再评估"}。`
    : recommendation === "recommended"
    ? "方案已验证可产出真实 MP4，建议作为当前场景的基础方案。"
    : "方案可产出 MP4，建议根据实际评分决定优先级。";

  return {
    recommendation: rec,
    recommendationLabel: recLabel,
    mainStrengths: mainStrengths.length ? mainStrengths : ["可产出真实 MP4"],
    mainProblems,
    nextSteps: nextSteps.length ? nextSteps : ["收集人工评分进一步判断"],
    productizationWorthy: rec !== "低",
    reasoning,
  };
}
