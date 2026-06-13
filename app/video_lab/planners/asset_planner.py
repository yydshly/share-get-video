"""
Asset Planner - 素材计划生成
"""

from typing import Any


def generate_asset_plan(
    key_points: dict[str, Any],
    method_category: str,
) -> dict[str, Any]:
    """
    生成素材计划。
    包括：封面图、信息卡片背景图、BGM、图标等。
    """
    kps = key_points.get("keyPoints", [])

    # 封面图
    cover = {
        "type": "cover_image",
        "description": "AI 前沿资讯分享封面",
        "resolution": "1080x1920",
        "format": "PNG",
        "generation": "image_gen_待接入" if method_category == "ai_asset_then_compose" else "placeholder",
    }

    # 每条一个信息卡片背景
    cards = []
    for kp in kps:
        cards.append({
            "type": "info_card_background",
            "segmentIndex": kp["index"],
            "description": f"信息卡片背景：{kp['title'][:20]}",
            "resolution": "1080x1920",
            "format": "PNG",
            "generation": "image_gen_待接入" if method_category == "ai_asset_then_compose" else "solid_color_placeholder",
        })

    # 图标
    icons = []
    for kp in kps:
        icons.append({
            "type": "topic_icon",
            "segmentIndex": kp["index"],
            "description": "关联图标",
            "generation": "image_gen_待接入" if method_category == "ai_asset_then_compose" else "emoji_placeholder",
        })

    return {
        "cover": cover,
        "infoCards": cards,
        "icons": icons,
        "bgm": {
            "type": "background_music",
            "description": "轻快科技风 BGM",
            "duration": 50,
            "source": "待接入",
        },
        "totalAssets": 1 + len(cards) + len(icons) + 1,
    }
