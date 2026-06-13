"""
Video Capability Lab - Seed Data
内置测试用例和生成方案配置
"""

from app.video_lab.models import (
    VideoTestCase,
    VideoMethod,
    MethodCategory,
    CostLevel,
    ControlLevel,
    StabilityLevel,
    ProductizationLevel,
    ImplementationStatus,
    InputType,
)


# ─────────────────────────────────────────────
# 内置测试用例
# ─────────────────────────────────────────────
SEED_TEST_CASES: list[VideoTestCase] = [
    VideoTestCase(
        id="case_ai_news_short",
        name="AI 资讯短视频",
        description="把一条 AI 资讯或 InsightCard 转成 30-45 秒竖屏短视频",
        inputType=InputType.INSIGHT_CARD,
        targetDurationSec=45,
        aspectRatio="9:16",
        evaluationFocus=[
            "信息表达清晰度",
            "字幕与旁白同步",
            "批量生成稳定性",
            "产品化价值",
        ],
        recommendedPriority=1,
    ),
    VideoTestCase(
        id="case_article_to_video",
        name="文章转视频",
        description="将一篇结构化文章（标题+段落+图片引用）转换为视频",
        inputType=InputType.ARTICLE,
        targetDurationSec=120,
        aspectRatio="16:9",
        evaluationFocus=[
            "内容完整性",
            "节奏把控",
            "视觉层次",
            "字幕准确性",
        ],
        recommendedPriority=2,
    ),
    VideoTestCase(
        id="case_emotional_short",
        name="情绪短片",
        description="生成一段强调氛围、情绪和视觉冲击力的短视频",
        inputType=InputType.EMOTIONAL_CONTENT,
        targetDurationSec=30,
        aspectRatio="9:16",
        evaluationFocus=[
            "氛围感",
            "运动流畅度",
            "情绪传达",
            "视觉美学",
        ],
        recommendedPriority=2,
    ),
    VideoTestCase(
        id="case_product_intro",
        name="产品介绍视频",
        description="用产品亮点、功能说明、使用场景制作介绍视频",
        inputType=InputType.PRODUCT_INFO,
        targetDurationSec=60,
        aspectRatio="16:9",
        evaluationFocus=[
            "信息准确度",
            "画面稳定性",
            "文字可读性",
            "品牌调性",
        ],
        recommendedPriority=1,
    ),
    VideoTestCase(
        id="case_image_motion",
        name="图片动起来",
        description="将单张图片通过 AI 视频模型生成动态化内容",
        inputType=InputType.IMAGE,
        targetDurationSec=5,
        aspectRatio="16:9",
        evaluationFocus=[
            "运动自然度",
            "主体一致性",
            "视觉质量",
            "运动幅度",
        ],
        recommendedPriority=1,
    ),
    VideoTestCase(
        id="case_knowledge_explainer",
        name="知识讲解视频",
        description="将知识内容（概念、流程、对比）转化为可视化讲解视频",
        inputType=InputType.KNOWLEDGE_CONTENT,
        targetDurationSec=180,
        aspectRatio="16:9",
        evaluationFocus=[
            "逻辑清晰度",
            "图表辅助",
            "节奏把控",
            "学习效果",
        ],
        recommendedPriority=1,
    ),
]


# ─────────────────────────────────────────────
# 内置生成方案
# ─────────────────────────────────────────────
SEED_VIDEO_METHODS: list[VideoMethod] = [
    VideoMethod(
        id="method_local_frame_compose",
        name="本地图像帧合成",
        category=MethodCategory.LOCAL_FRAME_COMPOSE,
        description="使用 Pillow / Canvas / OpenCV 生成图像帧，再用 FFmpeg 合成视频。适合程序化生成固定模板内容。",
        suitableScenarios=[
            "固定模板视频批量生成",
            "数据可视化动画",
            "文字动态效果",
            "简单图标动画",
        ],
        unsuitableScenarios=[
            "复杂真实场景渲染",
            "高逼真度人物/风景",
            "需要创意运动的场景",
        ],
        inputRequirements="图片素材 + 动画参数（位移、缩放、旋转、淡入淡出）",
        outputType="MP4 / WebM",
        costLevel=CostLevel.LOW,
        controlLevel=ControlLevel.HIGH,
        stabilityLevel=StabilityLevel.HIGH,
        productizationLevel=ProductizationLevel.HIGH,
        implementationStatus=ImplementationStatus.MOCK,
    ),
    VideoMethod(
        id="method_local_media_compose",
        name="本地媒体素材合成",
        category=MethodCategory.LOCAL_MEDIA_COMPOSE,
        description="使用 MoviePy / FFmpeg 对图片、音频、字幕、BGM、已有视频片段做合成。适合素材拼接和后期编排。",
        suitableScenarios=[
            "多素材组合编排",
            "音频+画面同步",
            "字幕压制",
            "BGM 适配",
        ],
        unsuitableScenarios=[
            "从零生成视觉内容",
            "复杂转场效果",
            "AI 生成素材整合",
        ],
        inputRequirements="视频片段 / 图片 / 音频 / 字幕 SRT",
        outputType="MP4 / WebM",
        costLevel=CostLevel.LOW,
        controlLevel=ControlLevel.HIGH,
        stabilityLevel=StabilityLevel.HIGH,
        productizationLevel=ProductizationLevel.HIGH,
        implementationStatus=ImplementationStatus.MOCK,
    ),
    VideoMethod(
        id="method_template_programmatic_render",
        name="Remotion 程序化模板渲染",
        category=MethodCategory.TEMPLATE_PROGRAMMATIC_RENDER,
        description="用 React / CSS / SVG / Canvas 做模板化视频渲染，适合资讯、日报、产品介绍、知识卡片等结构化内容。",
        suitableScenarios=[
            "资讯/日报视频",
            "产品介绍",
            "知识卡片",
            "数据报告视频",
            "结构化图文视频",
        ],
        unsuitableScenarios=[
            "高逼真度人物场景",
            "自由创意内容",
            "实时渲染性能要求高",
        ],
        inputRequirements="模板参数 JSON + 数据源",
        outputType="MP4 / WebM",
        costLevel=CostLevel.MEDIUM,
        controlLevel=ControlLevel.HIGH,
        stabilityLevel=StabilityLevel.MEDIUM,
        productizationLevel=ProductizationLevel.HIGH,
        implementationStatus=ImplementationStatus.MOCK,
    ),
    VideoMethod(
        id="method_ai_video_direct",
        name="大模型直接生成视频",
        category=MethodCategory.AI_VIDEO_DIRECT,
        description="使用文生视频 / 图生视频 / 首尾帧视频 / 主体参考视频等模型直接生成内容。",
        suitableScenarios=[
            "情绪/氛围短片",
            "图片动态化",
            "创意内容探索",
            "快速原型验证",
        ],
        unsuitableScenarios=[
            "需要精确文字/字幕",
            "结构化信息承载",
            "批量一致性要求高",
            "成本敏感型批量生产",
        ],
        inputRequirements="文本 prompt / 参考图片 / 首尾帧",
        outputType="MP4 / WebM",
        costLevel=CostLevel.VERY_HIGH,
        controlLevel=ControlLevel.LOW,
        stabilityLevel=StabilityLevel.LOW,
        productizationLevel=ProductizationLevel.MEDIUM,
        implementationStatus=ImplementationStatus.RESERVED,
    ),
    VideoMethod(
        id="method_ai_asset_then_compose",
        name="大模型拆解内容 + 生成素材 + 本地合成",
        category=MethodCategory.AI_ASSET_THEN_COMPOSE,
        description="LLM 生成脚本、旁白、字幕、图片提示词，TTS 生成语音，图像模型生成图片，最后由 Remotion / FFmpeg 合成。",
        suitableScenarios=[
            "长视频内容制作",
            "多模态内容整合",
            "半自动化视频流水线",
            "内容+视觉双重质量要求",
        ],
        unsuitableScenarios=[
            "实时性要求高",
            "成本敏感型项目",
            "需要精确逐帧控制",
        ],
        inputRequirements="文本内容 / 素材描述 / 旁白脚本",
        outputType="MP4 / WebM",
        costLevel=CostLevel.HIGH,
        controlLevel=ControlLevel.MEDIUM,
        stabilityLevel=StabilityLevel.MEDIUM,
        productizationLevel=ProductizationLevel.MEDIUM,
        implementationStatus=ImplementationStatus.MOCK,
    ),
    VideoMethod(
        id="method_hybrid_pipeline",
        name="混合编排流水线",
        category=MethodCategory.HYBRID_PIPELINE,
        description="按场景自动选择：本地合成、Remotion、AI 视频、AI 图片、TTS、FFmpeg 等能力组合。",
        suitableScenarios=[
            "复杂多模态内容",
            "需要多技术配合",
            "按需调度最优路径",
            "产品化批量生产",
        ],
        unsuitableScenarios=[
            "简单单一步骤",
            "实时渲染要求",
            "高度定制化单作品",
        ],
        inputRequirements="场景描述 + 多模态输入",
        outputType="MP4 / WebM",
        costLevel=CostLevel.HIGH,
        controlLevel=ControlLevel.MEDIUM,
        stabilityLevel=StabilityLevel.MEDIUM,
        productizationLevel=ProductizationLevel.HIGH,
        implementationStatus=ImplementationStatus.MOCK,
    ),
]


def get_test_case_by_id(case_id: str) -> VideoTestCase | None:
    for tc in SEED_TEST_CASES:
        if tc.id == case_id:
            return tc
    return None


def get_method_by_id(method_id: str) -> VideoMethod | None:
    for m in SEED_VIDEO_METHODS:
        if m.id == method_id:
            return m
    return None


def get_methods_by_category(category: MethodCategory) -> list[VideoMethod]:
    return [m for m in SEED_VIDEO_METHODS if m.category == category]
