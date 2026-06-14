# LOCAL_FRAME_VISUAL_PRESET_V0.2.4

## 概述

V0.2.4 为 `local_frame_compose` 引入了 AI Frontier Dark 视觉主题，使用 Pillow 生成专业感的信息卡片帧。

## 视觉主题：AI Frontier Dark

### 配色方案

| 用途 | 颜色 | RGB |
|------|------|-----|
| 主背景 | 深蓝黑 | `(12, 12, 30)` |
| 次背景 | 深蓝紫 | `(20, 20, 50)` |
| 卡片背景 | 蓝灰 | `(25, 30, 65)` |
| 主文字 | 纯白 | `(255, 255, 255)` |
| 次文字 | 浅蓝灰 | `(185, 195, 215)` |
| 强调色 | 科技蓝 | `(80, 140, 255)` |
| 高亮色 | 金黄 | `(255, 215, 60)` |

### 字体大小

| 元素 | 字号 |
|------|------|
| 封面标题 | 80px |
| 封面副标题 | 36px |
| 关键点标题 | 52px |
| 关键点正文 | 30px |
| 摘要正文 | 28px |

### 分辨率

- 竖屏 (9:16): 1080 × 1920
- 横屏 (16:9): 1920 × 1080
- 方形 (1:1): 1080 × 1080

## 帧类型

### 1. 封面帧 (Cover)
- 大标题 + 副标题
- 3 个信号 tag（来自前 3 个关键点）
- 日期字符串
- 背景渐变 + 装饰元素

### 2. 概览帧 (Overview)
- 前 4 个关键点的索引和标题列表
- 快速预览整体内容

### 3. 关键点帧 (Keypoint)
- 分类标签（安全/研究/应用等，带颜色）
- 序号 + 总数
- 标题 + 正文
- 高亮词（金黄色标注数字/百分比/倍数）
- 来源标注

### 4. 总结帧 (Summary)
- 关键发现列表
- CTA（Call-to-Action）
- 收尾感

## 转场效果

### Fade 转场

- 类型：Fade（淡入淡出）
- 中间帧数：默认 4 帧（可配置 0-8）
- 实现方式：Pillow 逐帧混合

```
主帧A → fade_1 → fade_2 → fade_3 → fade_4 → 主帧B
```

### transitionFrames 参数

| 值 | 效果 |
|----|------|
| 0 | 无转场，直接切换 |
| 2 | 快速过渡 |
| 4 | 默认，平滑过渡 |
| 8 | 慢速过渡 |

## 高亮提取

### extract_highlights()

自动识别以下模式：

1. **百分比**: `88.9%`, `72%`, `16%`
2. **倍数**: `10倍`, `5x`, `3X`
3. **中文数字**: `10万`, `5620亿`
4. **数量短语**: `10万名员工`, `5620亿参数`

### highlightMode

| 模式 | 说明 |
|------|------|
| `auto` | 提取所有类型高亮词 |
| `numbers` | 只提取纯数字类（百分比、倍数、小数、大整数） |
| `none` | 不提取高亮词 |

## V0.2.5 参数化

V0.2.5 在 V0.2.4 视觉基础上增加了参数化支持：

```python
@dataclass
class LocalFrameRenderParams:
    style_preset: str = "ai_frontier_dark"      # 视觉风格
    target_duration: int = 45                    # 目标时长（秒）
    aspect_ratio: str = "9:16"                   # 画面比例
    key_point_count: int = 6                     # 关键点数
    highlight_mode: str = "auto"                  # 高亮模式
    transition_enabled: bool = True               # 启用转场
    transition_frames: int = 4                    # 转场帧数
    include_overview: bool = True                # 包含概览帧
    include_summary: bool = True                  # 包含总结帧
```

## 相关文件

- `app/video_lab/renderers/visual_theme.py` - 主题常量
- `app/video_lab/renderers/frame_templates.py` - 帧模板
- `app/video_lab/renderers/transition_composer.py` - 转场生成
- `app/video_lab/renderers/text_layout.py` - 文字布局和高亮提取
- `app/video_lab/renderers/render_params.py` - V0.2.5 参数模型

## V0.2.4.1 修复

V0.2.4.1 修复了 fade 转场的顺序问题：

- **问题**：fade 帧在主帧之后而非之间，导致视觉顺序错误
- **修复**：`build_frame_sequence_with_transitions` 修正顺序逻辑
- **验证**：`frameSequenceCount` 现在正确反映帧序列长度
