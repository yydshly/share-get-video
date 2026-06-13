// Video Capability Lab - Method Advice
// 与后端 advisor.py 保持同步的静态推荐规则

import type { VideoMethodAdvice } from "./types";
import { SEED_TEST_CASES, getTestCaseById } from "./seedData";

export const ADVISOR_RULES: Record<string, Omit<VideoMethodAdvice, "scenario">> = {
  case_ai_frontier_daily_001: {
    recommendedMethodId: "method_template_programmatic_render",
    backupMethodIds: ["method_ai_asset_then_compose", "method_local_media_compose"],
    notRecommendedMethodIds: ["method_ai_video_direct"],
    reasoning:
      "AI 资讯共享视频要求信息准确、结构清晰、字幕可控、旁白稳定、批量生成能力强。大模型直接文生视频不适合承载精确信息表达，更适合作为背景素材或情绪镜头。Remotion 模板化渲染可确保文字准确、节奏一致、产品化成本低。",
    productizationLevel: "high",
    suggestedStack: ["Remotion", "FFmpeg (字幕压制)", "TTS (旁白)", "结构化数据解析"],
    riskNotes: ["模板设计成本前期较高", "多条目内容需要拆条处理", "字幕长度需限制以保证可读性"],
    nextActions: [
      "优先打通本地帧合成 + FFmpeg 真实 MP4",
      "再打通 Remotion 模板渲染",
      "接入 TTS 生成旁白",
      "接入图片生成做封面和背景素材",
      "最后再验证 AI 视频模型作为局部素材",
    ],
  },
  case_ai_news_short: {
    recommendedMethodId: "method_template_programmatic_render",
    backupMethodIds: ["method_ai_asset_then_compose", "method_local_media_compose"],
    notRecommendedMethodIds: ["method_ai_video_direct"],
    reasoning:
      "该场景要求信息表达准确、字幕和旁白稳定、批量生成可控，不适合直接依赖文生视频承载全部内容。Remotion 模板化渲染可确保文字准确、节奏一致、产品化成本低。",
    productizationLevel: "high",
    suggestedStack: ["Remotion", "FFmpeg (字幕压制)", "TTS (旁白，可选)"],
    riskNotes: ["模板设计成本前期较高", "动态数据接入需 ETL 适配"],
    nextActions: ["设计资讯视频模板组件库", "对接结构化数据源", "验证字幕与旁白同步机制"],
  },
  case_emotional_short: {
    recommendedMethodId: "method_ai_video_direct",
    backupMethodIds: ["method_ai_asset_then_compose", "method_local_media_compose"],
    notRecommendedMethodIds: ["method_local_frame_compose"],
    reasoning:
      "该场景更重视氛围、运动画面和视觉情绪，直接视频模型或图生视频更适合。强视觉冲击和自然运动是本地帧合成无法达到的。",
    productizationLevel: "low",
    suggestedStack: ["Pika / Runway / Kling (图生视频)", "Sora / Veo (文生视频，可选)"],
    riskNotes: ["生成结果不可控", "批量一致性差", "成本高"],
    nextActions: ["评估主流图生视频模型效果", "建立情绪类 prompt 库", "设计二次筛选机制"],
  },
  case_product_intro: {
    recommendedMethodId: "method_template_programmatic_render",
    backupMethodIds: ["method_local_media_compose"],
    notRecommendedMethodIds: ["method_ai_video_direct"],
    reasoning:
      "产品介绍需要结构清晰、文字准确、画面稳定，纯文生视频不可控。Remotion 模板化渲染可以确保品牌调性一致、版本迭代可控。",
    productizationLevel: "high",
    suggestedStack: ["Remotion", "React SVG 动画", "FFmpeg 合成"],
    riskNotes: ["首次模板开发成本", "多产品线需要多模板"],
    nextActions: ["建立产品介绍模板体系", "设计可配置化产品参数", "验证多分辨率适配"],
  },
  case_article_to_video: {
    recommendedMethodId: "method_template_programmatic_render",
    backupMethodIds: ["method_ai_asset_then_compose", "method_local_media_compose"],
    notRecommendedMethodIds: ["method_ai_video_direct"],
    reasoning:
      "文章转视频需要保持内容完整性、逻辑清晰，模板化渲染可以精确控制每个段落的展示节奏和视觉层次。",
    productizationLevel: "medium",
    suggestedStack: ["Remotion", "LLM 摘要拆分", "TTS 旁白"],
    riskNotes: ["长视频渲染时间长", "图文排版设计成本"],
    nextActions: ["设计文章模板组件", "对接文章解析 API", "验证字幕与旁白时间轴对齐"],
  },
  case_knowledge_explainer: {
    recommendedMethodId: "method_template_programmatic_render",
    backupMethodIds: ["method_local_frame_compose", "method_ai_asset_then_compose"],
    notRecommendedMethodIds: ["method_ai_video_direct"],
    reasoning:
      "知识讲解需要逻辑、图表、字幕和节奏可控，程序化渲染更适合。图表动画、数据标注、概念可视化是模板化渲染的优势。",
    productizationLevel: "high",
    suggestedStack: ["Remotion", "D3.js / Recharts 图表", "FFmpeg 字幕", "TTS 旁白"],
    riskNotes: ["知识内容结构化成本", "图表动画开发工作量大"],
    nextActions: ["设计知识视频模板库", "开发图表动画组件", "建立知识内容Schema"],
  },
  case_image_motion: {
    recommendedMethodId: "method_ai_video_direct",
    backupMethodIds: ["method_hybrid_pipeline"],
    notRecommendedMethodIds: ["method_local_frame_compose"],
    reasoning:
      "图片动态化需要真实运动生成能力，本地帧合成只能做简单缩放和平移，视觉上限有限。图生视频模型能够产生自然的物体运动和镜头移动。",
    productizationLevel: "medium",
    suggestedStack: ["Kling", "Runway Gen-2", "Pika", "Sora (图生视频)"],
    riskNotes: ["运动幅度不可控", "主体变形风险", "成本按次计费"],
    nextActions: ["评测主流图生视频模型", "设计运动强度控制策略", "建立图片质量标准"],
  },
};

export function getAdviceForTestCase(testCaseId: string): VideoMethodAdvice | null {
  const rule = ADVISOR_RULES[testCaseId];
  if (!rule) return null;

  const tc = getTestCaseById(testCaseId);

  return {
    scenario: tc?.name ?? testCaseId,
    ...rule,
  };
}

export function getAllAdvice(): VideoMethodAdvice[] {
  return SEED_TEST_CASES.map((tc) => ({
    scenario: tc.name,
    ...(ADVISOR_RULES[tc.id] ?? {
      recommendedMethodId: "method_template_programmatic_render",
      backupMethodIds: ["method_ai_asset_then_compose"],
      notRecommendedMethodIds: ["method_ai_video_direct"],
      reasoning: "默认推荐模板化渲染路线，可控性最强。",
      productizationLevel: "medium",
      suggestedStack: ["Remotion", "FFmpeg"],
      riskNotes: ["需评估具体场景适配性"],
      nextActions: ["补充场景特征定义"],
    }),
  }));
}
