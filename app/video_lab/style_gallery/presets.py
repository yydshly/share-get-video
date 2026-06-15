"""
style_gallery/presets.py - 预置风格数据（V0.4.6）

每条路线提供多个代表性预置风格，覆盖该路线的参数空间，用于探索"每种技术能做出
什么风格、风格跨度和能力边界"（宏观目标①②）。

从 router.py 抽出，便于扩充与测试。字段：
route_id / route_name / style_id / style_name / description / capabilities / tags / params
"""

from typing import Any

PRESET_STYLES: list[dict[str, Any]] = [
    # ──────────────── Pillow 信息卡路线 ────────────────
    {
        "route_id": "local_frame_compose",
        "route_name": "Pillow 信息卡路线",
        "style_id": "pillow_data_card",
        "style_name": "稳定数据卡",
        "description": "清晰展示数据指标，强调数字和来源，适合资讯类内容",
        "capabilities": ["长文本可读", "数据卡清楚", "排版稳定", "批量生成可靠"],
        "tags": ["数据", "资讯", "稳定"],
        "params": {
            "showDataViz": True, "highlightMode": "auto", "contentAlign": "center",
            "themeAdaptive": True, "transitionEnabled": True, "transitionFrames": 4,
            "titleColor": "#f8fafc", "bodyColor": "#94a3b8", "highlightColor": "#f59e0b",
        },
    },
    {
        "route_id": "local_frame_compose",
        "route_name": "Pillow 信息卡路线",
        "style_id": "pillow_minimal",
        "style_name": "极简资讯卡",
        "description": "极简排版，去除装饰，聚焦内容本身，适合深度阅读",
        "capabilities": ["极简排版", "聚焦内容", "无干扰"],
        "tags": ["极简", "深度阅读"],
        "params": {
            "showDataViz": False, "highlightMode": "numbers", "contentAlign": "center",
            "themeAdaptive": False, "transitionEnabled": False, "transitionFrames": 0,
            "titleColor": "#f8fafc", "bodyColor": "#cbd5e1", "highlightColor": "#22d3ee",
        },
    },
    {
        "route_id": "local_frame_compose",
        "route_name": "Pillow 信息卡路线",
        "style_id": "pillow_warm_editorial",
        "style_name": "暖色编辑风",
        "description": "固定暖色调 + 居中排版，杂志编辑质感，展示 Pillow 的品牌化定版能力",
        "capabilities": ["暖色品牌调", "居中编辑感", "固定风格（非自适应）"],
        "tags": ["暖色", "编辑", "品牌化"],
        "params": {
            "showDataViz": True, "highlightMode": "auto", "contentAlign": "center",
            "themeAdaptive": False, "transitionEnabled": True, "transitionFrames": 4,
            "titleColor": "#fff7ed", "bodyColor": "#fed7aa", "highlightColor": "#fb923c",
        },
    },

    # ──────────────── Remotion 动态模板路线 ────────────────
    {
        "route_id": "template_programmatic_render",
        "route_name": "Remotion 动态模板路线",
        "style_id": "remotion_metric_motion",
        "style_name": "动态数据栏目",
        "description": "数字滚动 + 进度条生长，展示 Remotion 时间轴动画能力，适合数据驱动内容",
        "capabilities": ["数字滚动", "进度条生长", "卡片入场", "页面转场", "栏目包装感", "轻背景音"],
        "tags": ["动态", "数据", "栏目包装", "BGM"],
        "params": {
            "showDataViz": True, "accentColor": "#3b82f6", "highlightColor": "#f59e0b",
            "fontScale": 1, "showIcon": True, "motionIntensity": "medium",
            "coverStyle": "editorial", "overviewStyle": "timeline",
            "metricAnimation": "countup_bar", "transitionStyle": "slide_fade",
            "bgm": {"mode": "generated_ambient", "volume": 0.06, "fadeIn": 1.2, "fadeOut": 1.5},
        },
    },
    {
        "route_id": "template_programmatic_render",
        "route_name": "Remotion 动态模板路线",
        "style_id": "remotion_cinematic",
        "style_name": "电影感快讯",
        "description": "电影感配色 + 慢速转场，营造大屏资讯氛围，适合重点报道",
        "capabilities": ["电影感", "慢速转场", "大屏氛围", "重点报道"],
        "tags": ["电影感", "大屏", "重点"],
        "params": {
            "showDataViz": True, "accentColor": "#a78bfa", "highlightColor": "#fbbf24",
            "fontScale": 1.1, "showIcon": False, "motionIntensity": "low",
            "coverStyle": "cinematic", "overviewStyle": "grid",
            "metricAnimation": "countup_number", "transitionStyle": "fade",
        },
    },
    {
        "route_id": "template_programmatic_render",
        "route_name": "Remotion 动态模板路线",
        "style_id": "remotion_minimal_clean",
        "style_name": "极简动效",
        "description": "克制的动效 + 干净排版，去掉数字动画和图标，展示 Remotion 低强度端的一面",
        "capabilities": ["克制动效", "干净排版", "无数字动画", "低干扰"],
        "tags": ["极简", "克制", "干净"],
        "params": {
            "showDataViz": False, "accentColor": "#60a5fa", "highlightColor": "#93c5fd",
            "fontScale": 1.05, "showIcon": False, "motionIntensity": "low",
            "coverStyle": "minimal", "overviewStyle": "clean",
            "metricAnimation": "none", "transitionStyle": "fade",
        },
    },
    {
        "route_id": "template_programmatic_render",
        "route_name": "Remotion 动态模板路线",
        "style_id": "remotion_high_energy",
        "style_name": "高能快剪",
        "description": "高强度动效 + 滑动转场 + 数字滚动，节奏强烈，展示 Remotion 动效上限",
        "capabilities": ["高强度动效", "滑动转场", "数字滚动", "强节奏"],
        "tags": ["高能", "快剪", "强动效"],
        "params": {
            "showDataViz": True, "accentColor": "#22c55e", "highlightColor": "#f59e0b",
            "fontScale": 1, "showIcon": True, "motionIntensity": "high",
            "coverStyle": "editorial", "overviewStyle": "timeline",
            "metricAnimation": "countup_bar", "transitionStyle": "slide",
            "bgm": {"mode": "generated_ambient", "volume": 0.07, "fadeIn": 1.0, "fadeOut": 1.2},
        },
    },

    # ──────────────── AI 素材氛围路线 ────────────────
    {
        "route_id": "ai_asset_then_compose",
        "route_name": "AI 素材氛围路线",
        "style_id": "ai_asset_tech_mood",
        "style_name": "深蓝科技氛围",
        "description": "AI 生成深蓝科技背景 + 信息卡融合，传播型视觉，适合前沿资讯",
        "capabilities": ["AI 背景", "科技感氛围", "封面感", "背景+信息卡融合", "传播型视觉", "轻背景音"],
        "tags": ["科技", "氛围", "传播", "BGM"],
        "params": {
            "showDataViz": True,
            "imageStyle": "深蓝科技数据可视化背景，未来感，抽象光线，电影质感，无文字，无文本，柔和景深",
            "backgroundDarken": 0.55, "cardOpacity": 0.85, "cardBlur": True,
            "highlightColor": "#f59e0b", "contentAlign": "top", "kenBurns": True,
            "bgm": {"mode": "generated_ambient", "volume": 0.06, "fadeIn": 1.2, "fadeOut": 1.5},
        },
    },
    {
        "route_id": "ai_asset_then_compose",
        "route_name": "AI 素材氛围路线",
        "style_id": "ai_asset_cinematic",
        "style_name": "电影感光线背景",
        "description": "暖色调电影感光线背景 + 高对比度信息卡，适合深度分析和专题报道",
        "capabilities": ["电影感光线", "高对比度信息卡", "深度分析", "专题报道"],
        "tags": ["电影感", "光线", "深度"],
        "params": {
            "showDataViz": True,
            "imageStyle": "暖色调电影感光线背景，柔和散景，戏剧性光照，无文字，无文本，电影质感",
            "backgroundDarken": 0.6, "cardOpacity": 0.9, "cardBlur": False,
            "highlightColor": "#fbbf24", "contentAlign": "center", "kenBurns": True,
        },
    },
    {
        "route_id": "ai_asset_then_compose",
        "route_name": "AI 素材氛围路线",
        "style_id": "ai_asset_minimal_dark",
        "style_name": "极简暗调氛围",
        "description": "极简深色抽象背景 + 大量留白 + 静态稳定，展示 AI 素材路线的克制端",
        "capabilities": ["极简暗调", "大量留白", "静态稳定", "高级感"],
        "tags": ["极简", "暗调", "静态"],
        "params": {
            "showDataViz": False,
            "imageStyle": "极简深色抽象几何背景，大量留白，柔和光晕，高级感，无文字，无文本",
            "backgroundDarken": 0.5, "cardOpacity": 0.78, "cardBlur": True,
            "highlightColor": "#22d3ee", "contentAlign": "center", "kenBurns": False,
        },
    },
]


def list_preset_styles() -> list[dict[str, Any]]:
    """返回所有预置风格（每条路线多个，覆盖参数空间）。"""
    return PRESET_STYLES
