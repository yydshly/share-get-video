"""
Video Capability Lab - Method Advisor
根据测试场景输出方案推荐建议
"""

from app.video_lab.models import (
    VideoMethodAdvice,
    ProductizationLevel,
)
from app.video_lab.seed_data import SEED_TEST_CASES, get_test_case_by_id


# ─────────────────────────────────────────────
# 推荐规则表
# ─────────────────────────────────────────────
ADVISOR_RULES: dict[str, dict] = {
    "case_ai_news_short": {
        "recommendedMethodId": "method_template_programmatic_render",
        "backupMethodIds": [
            "method_ai_asset_then_compose",
            "method_local_media_compose",
        ],
        "notRecommendedMethodIds": ["method_ai_video_direct"],
        "reasoning": (
            "该场景要求信息表达准确、字幕和旁白稳定、批量生成可控，"
            "不适合直接依赖文生视频承载全部内容。Remotion 模板化渲染可确保"
            "文字准确、节奏一致、产品化成本低。"
        ),
        "productizationLevel": ProductizationLevel.HIGH,
        "suggestedStack": [
            "Remotion",
            "FFmpeg (字幕压制)",
            "TTS (旁白，可选)",
        ],
        "riskNotes": [
            "模板设计成本前期较高",
            "动态数据接入需 ETL 适配",
        ],
        "nextActions": [
            "设计资讯视频模板组件库",
            "对接结构化数据源",
            "验证字幕与旁白同步机制",
        ],
    },
    "case_emotional_short": {
        "recommendedMethodId": "method_ai_video_direct",
        "backupMethodIds": [
            "method_ai_asset_then_compose",
            "method_local_media_compose",
        ],
        "notRecommendedMethodIds": ["method_local_frame_compose"],
        "reasoning": (
            "该场景更重视氛围、运动画面和视觉情绪，"
            "直接视频模型或图生视频更适合。强视觉冲击和自然运动"
            "是本地帧合成无法达到的。"
        ),
        "productizationLevel": ProductizationLevel.LOW,
        "suggestedStack": [
            "Pika / Runway / Kling (图生视频)",
            "Sora / Veo (文生视频，可选)",
        ],
        "riskNotes": [
            "生成结果不可控",
            "批量一致性差",
            "成本高",
        ],
        "nextActions": [
            "评估主流图生视频模型效果",
            "建立情绪类 prompt 库",
            "设计二次筛选机制",
        ],
    },
    "case_product_intro": {
        "recommendedMethodId": "method_template_programmatic_render",
        "backupMethodIds": ["method_local_media_compose"],
        "notRecommendedMethodIds": ["method_ai_video_direct"],
        "reasoning": (
            "产品介绍需要结构清晰、文字准确、画面稳定，"
            "纯文生视频不可控。Remotion 模板化渲染可以确保"
            "品牌调性一致、版本迭代可控。"
        ),
        "productizationLevel": ProductizationLevel.HIGH,
        "suggestedStack": [
            "Remotion",
            "React SVG 动画",
            "FFmpeg 合成",
        ],
        "riskNotes": [
            "首次模板开发成本",
            "多产品线需要多模板",
        ],
        "nextActions": [
            "建立产品介绍模板体系",
            "设计可配置化产品参数",
            "验证多分辨率适配",
        ],
    },
    "case_article_to_video": {
        "recommendedMethodId": "method_template_programmatic_render",
        "backupMethodIds": [
            "method_ai_asset_then_compose",
            "method_local_media_compose",
        ],
        "notRecommendedMethodIds": ["method_ai_video_direct"],
        "reasoning": (
            "文章转视频需要保持内容完整性、逻辑清晰，"
            "模板化渲染可以精确控制每个段落的展示节奏和视觉层次。"
        ),
        "productizationLevel": ProductizationLevel.MEDIUM,
        "suggestedStack": [
            "Remotion",
            "LLM 摘要拆分",
            "TTS 旁白",
        ],
        "riskNotes": [
            "长视频渲染时间长",
            "图文排版设计成本",
        ],
        "nextActions": [
            "设计文章模板组件",
            "对接文章解析 API",
            "验证字幕与旁白时间轴对齐",
        ],
    },
    "case_knowledge_explainer": {
        "recommendedMethodId": "method_template_programmatic_render",
        "backupMethodIds": [
            "method_local_frame_compose",
            "method_ai_asset_then_compose",
        ],
        "notRecommendedMethodIds": ["method_ai_video_direct"],
        "reasoning": (
            "知识讲解需要逻辑、图表、字幕和节奏可控，"
            "程序化渲染更适合。图表动画、数据标注、概念可视化"
            "是模板化渲染的优势。"
        ),
        "productizationLevel": ProductizationLevel.HIGH,
        "suggestedStack": [
            "Remotion",
            "D3.js / Recharts 图表",
            "FFmpeg 字幕",
            "TTS 旁白",
        ],
        "riskNotes": [
            "知识内容结构化成本",
            "图表动画开发工作量大",
        ],
        "nextActions": [
            "设计知识视频模板库",
            "开发图表动画组件",
            "建立知识内容Schema",
        ],
    },
    "case_image_motion": {
        "recommendedMethodId": "method_ai_video_direct",
        "backupMethodIds": ["method_hybrid_pipeline"],
        "notRecommendedMethodIds": ["method_local_frame_compose"],
        "reasoning": (
            "图片动态化需要真实运动生成能力，"
            "本地帧合成只能做简单缩放和平移，视觉上限有限。"
            "图生视频模型能够产生自然的物体运动和镜头移动。"
        ),
        "productizationLevel": ProductizationLevel.MEDIUM,
        "suggestedStack": [
            "Kling",
            "Runway Gen-2",
            "Pika",
            "Sora (图生视频)",
        ],
        "riskNotes": [
            "运动幅度不可控",
            "主体变形风险",
            "成本按次计费",
        ],
        "nextActions": [
            "评测主流图生视频模型",
            "设计运动强度控制策略",
            "建立图片质量标准",
        ],
    },
}


def getVideoMethodAdvice(testCaseId: str) -> VideoMethodAdvice | None:
    """
    根据测试用例 ID 返回结构化方案建议。
    如果找不到对应规则，返回 None。
    """
    rule = ADVISOR_RULES.get(testCaseId)
    if not rule:
        tc = get_test_case_by_id(testCaseId)
        if not tc:
            return None
        return VideoMethodAdvice(
            scenario=tc.name,
            recommendedMethodId="method_template_programmatic_render",
            backupMethodIds=["method_ai_asset_then_compose"],
            notRecommendedMethodIds=["method_ai_video_direct"],
            reasoning="默认推荐模板化渲染路线，可控性最强。",
            productizationLevel=ProductizationLevel.MEDIUM,
            suggestedStack=["Remotion", "FFmpeg"],
            riskNotes=["需评估具体场景适配性"],
            nextActions=["补充场景特征定义"],
        )

    tc = get_test_case_by_id(testCaseId)
    scenario_name = tc.name if tc else testCaseId

    return VideoMethodAdvice(
        scenario=scenario_name,
        **rule,
    )


def get_all_advice() -> list[VideoMethodAdvice]:
    """返回所有场景的建议列表"""
    results = []
    for tc in SEED_TEST_CASES:
        advice = getVideoMethodAdvice(tc.id)
        if advice:
            results.append(advice)
    return results
