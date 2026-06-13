// Video Capability Lab - Frontend Seed Data
// 与后端 seed_data.py 保持同步

import type { VideoTestCase, VideoMethod } from "./types";

export const SEED_TEST_CASES: VideoTestCase[] = [
  {
    id: "case_ai_frontier_daily_001",
    name: "今日 AI 前沿共享短视频",
    description: "将 AI 前沿资讯摘要转成 30-45 秒竖屏共享视频，适合朋友圈/社媒传播",
    inputType: "ai_insight_summary",
    targetDurationSec: 45,
    aspectRatio: "9:16",
    evaluationFocus: [
      "信息准确性",
      "字幕可读性",
      "视觉层次",
      "传播吸引力",
      "批量生成稳定性",
      "产品化价值",
    ],
    recommendedPriority: 1,
    defaultInput: JSON.stringify({
      content: `今日AI前沿呈现多维度进展：评估体系方面，多个针对科学推理、地理空间分析、UI用户体验的基准测试集中发布，同时学界开始质疑多智能体系统的实际优势；安全维度上，代理型AI框架的安全漏洞引发关注，人在循环中的研究架构被证明能显著降低失败率；应用层面，开源医学视觉语言模型OpenMedQ超越80倍规模的竞品，BBVA宣布10万员工规模化部署ChatGPT Enterprise，OpenAI则通过收购Ona强化企业级代理能力。技术优化方向上，LoRA缩放因子的深层机制和光学脉冲神经网络成为亮点。

多智能体系统未必优于单智能体：研究发现在推理和交互任务中，自动MAS成本高出10倍却表现更差，揭示当前多智能体协作方法的根本局限
依据：依据 1

代理型AI框架存在严重安全漏洞：主流框架均未实现内存完整性，单次污染攻击可使政府福利代理的错误拒绝率飙升至88.9%
依据：依据 1

人在循环中架构可将AI辅助研究失败率从72%降至16%，证明人机认知劳动的结构化分工比模型能力本身更关键
依据：依据 1

OpenMedQ以完全开源数据训练，在医学视觉问答上超越参数量达5620亿的Med-PaLM M系列，宏F1均值优于主流开源模型
依据：依据 1

BBVA宣布将ChatGPT Enterprise部署至全部约10万名员工，成为金融行业大规模生成式AI应用的标志性案例
依据：依据 1

OpenAI收购Ona以强化Codex产品线的安全持久云执行环境，拓展企业级长时间运行AI代理市场
依据：依据 1`,
    }),
  },
  {
    id: "case_ai_news_short",
    name: "AI 资讯短视频",
    description: "把一条 AI 资讯或 InsightCard 转成 30-45 秒竖屏短视频",
    inputType: "insight_card",
    targetDurationSec: 45,
    aspectRatio: "9:16",
    evaluationFocus: ["信息表达清晰度", "字幕与旁白同步", "批量生成稳定性", "产品化价值"],
    recommendedPriority: 1,
  },
  {
    id: "case_article_to_video",
    name: "文章转视频",
    description: "将一篇结构化文章（标题+段落+图片引用）转换为视频",
    inputType: "article",
    targetDurationSec: 120,
    aspectRatio: "16:9",
    evaluationFocus: ["内容完整性", "节奏把控", "视觉层次", "字幕准确性"],
    recommendedPriority: 2,
  },
  {
    id: "case_emotional_short",
    name: "情绪短片",
    description: "生成一段强调氛围、情绪和视觉冲击力的短视频",
    inputType: "emotional_content",
    targetDurationSec: 30,
    aspectRatio: "9:16",
    evaluationFocus: ["氛围感", "运动流畅度", "情绪传达", "视觉美学"],
    recommendedPriority: 2,
  },
  {
    id: "case_product_intro",
    name: "产品介绍视频",
    description: "用产品亮点、功能说明、使用场景制作介绍视频",
    inputType: "product_info",
    targetDurationSec: 60,
    aspectRatio: "16:9",
    evaluationFocus: ["信息准确度", "画面稳定性", "文字可读性", "品牌调性"],
    recommendedPriority: 1,
  },
  {
    id: "case_image_motion",
    name: "图片动起来",
    description: "将单张图片通过 AI 视频模型生成动态化内容",
    inputType: "image",
    targetDurationSec: 5,
    aspectRatio: "16:9",
    evaluationFocus: ["运动自然度", "主体一致性", "视觉质量", "运动幅度"],
    recommendedPriority: 1,
  },
  {
    id: "case_knowledge_explainer",
    name: "知识讲解视频",
    description: "将知识内容（概念、流程、对比）转化为可视化讲解视频",
    inputType: "knowledge_content",
    targetDurationSec: 180,
    aspectRatio: "16:9",
    evaluationFocus: ["逻辑清晰度", "图表辅助", "节奏把控", "学习效果"],
    recommendedPriority: 1,
  },
];

export const SEED_VIDEO_METHODS: VideoMethod[] = [
  {
    id: "method_local_frame_compose",
    name: "本地图像帧合成",
    category: "local_frame_compose",
    description: "使用 Pillow / Canvas / OpenCV 生成图像帧，再用 FFmpeg 合成视频。适合程序化生成固定模板内容。",
    suitableScenarios: ["固定模板视频批量生成", "数据可视化动画", "文字动态效果", "简单图标动画"],
    unsuitableScenarios: ["复杂真实场景渲染", "高逼真度人物/风景", "需要创意运动的场景"],
    inputRequirements: "图片素材 + 动画参数（位移、缩放、旋转、淡入淡出）",
    outputType: "MP4 / WebM",
    costLevel: "low",
    controlLevel: "high",
    stabilityLevel: "high",
    productizationLevel: "high",
    implementationStatus: "mock",
  },
  {
    id: "method_local_media_compose",
    name: "本地媒体素材合成",
    category: "local_media_compose",
    description: "使用 MoviePy / FFmpeg 对图片、音频、字幕、BGM、已有视频片段做合成。适合素材拼接和后期编排。",
    suitableScenarios: ["多素材组合编排", "音频+画面同步", "字幕压制", "BGM 适配"],
    unsuitableScenarios: ["从零生成视觉内容", "复杂转场效果", "AI 生成素材整合"],
    inputRequirements: "视频片段 / 图片 / 音频 / 字幕 SRT",
    outputType: "MP4 / WebM",
    costLevel: "low",
    controlLevel: "high",
    stabilityLevel: "high",
    productizationLevel: "high",
    implementationStatus: "mock",
  },
  {
    id: "method_template_programmatic_render",
    name: "Remotion 程序化模板渲染",
    category: "template_programmatic_render",
    description: "用 React / CSS / SVG / Canvas 做模板化视频渲染，适合资讯、日报、产品介绍、知识卡片等结构化内容。",
    suitableScenarios: ["资讯/日报视频", "产品介绍", "知识卡片", "数据报告视频", "结构化图文视频"],
    unsuitableScenarios: ["高逼真度人物场景", "自由创意内容", "实时渲染性能要求高"],
    inputRequirements: "模板参数 JSON + 数据源",
    outputType: "MP4 / WebM",
    costLevel: "medium",
    controlLevel: "high",
    stabilityLevel: "medium",
    productizationLevel: "high",
    implementationStatus: "mock",
  },
  {
    id: "method_ai_video_direct",
    name: "大模型直接生成视频",
    category: "ai_video_direct",
    description: "使用文生视频 / 图生视频 / 首尾帧视频 / 主体参考视频等模型直接生成内容。",
    suitableScenarios: ["情绪/氛围短片", "图片动态化", "创意内容探索", "快速原型验证"],
    unsuitableScenarios: ["需要精确文字/字幕", "结构化信息承载", "批量一致性要求高", "成本敏感型批量生产"],
    inputRequirements: "文本 prompt / 参考图片 / 首尾帧",
    outputType: "MP4 / WebM",
    costLevel: "very_high",
    controlLevel: "low",
    stabilityLevel: "low",
    productizationLevel: "medium",
    implementationStatus: "reserved",
  },
  {
    id: "method_ai_asset_then_compose",
    name: "大模型拆解内容 + 生成素材 + 本地合成",
    category: "ai_asset_then_compose",
    description: "LLM 生成脚本、旁白、字幕、图片提示词，TTS 生成语音，图像模型生成图片，最后由 Remotion / FFmpeg 合成。",
    suitableScenarios: ["长视频内容制作", "多模态内容整合", "半自动化视频流水线", "内容+视觉双重质量要求"],
    unsuitableScenarios: ["实时性要求高", "成本敏感型项目", "需要精确逐帧控制"],
    inputRequirements: "文本内容 / 素材描述 / 旁白脚本",
    outputType: "MP4 / WebM",
    costLevel: "high",
    controlLevel: "medium",
    stabilityLevel: "medium",
    productizationLevel: "medium",
    implementationStatus: "mock",
  },
  {
    id: "method_hybrid_pipeline",
    name: "混合编排流水线",
    category: "hybrid_pipeline",
    description: "按场景自动选择：本地合成、Remotion、AI 视频、AI 图片、TTS、FFmpeg 等能力组合。",
    suitableScenarios: ["复杂多模态内容", "需要多技术配合", "按需调度最优路径", "产品化批量生产"],
    unsuitableScenarios: ["简单单一步骤", "实时渲染要求", "高度定制化单作品"],
    inputRequirements: "场景描述 + 多模态输入",
    outputType: "MP4 / WebM",
    costLevel: "high",
    controlLevel: "medium",
    stabilityLevel: "medium",
    productizationLevel: "high",
    implementationStatus: "mock",
  },
];

export const METHOD_CATEGORY_LABELS: Record<string, string> = {
  local_frame_compose: "本地图像帧合成",
  local_media_compose: "本地媒体素材合成",
  template_programmatic_render: "Remotion 程序化模板",
  ai_video_direct: "大模型直接生成",
  ai_asset_then_compose: "AI 素材 + 本地合成",
  hybrid_pipeline: "混合编排流水线",
};

export const getTestCaseById = (id: string): VideoTestCase | undefined =>
  SEED_TEST_CASES.find((tc) => tc.id === id);

export const getMethodById = (id: string): VideoMethod | undefined =>
  SEED_VIDEO_METHODS.find((m) => m.id === id);
