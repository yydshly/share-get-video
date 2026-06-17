# V1.2.3 Remotion Visual Technique: academic_sketch

## 1. academic_sketch 的定位

`academic_sketch` 是第一个从"效果样机库"（Effect Prototype Gallery）转化而来的真实可渲染 `visualTechnique`。

它代表"学术手绘草稿流"风格 —— 以纸张质感、网格线、手绘批注为核心特征，与深蓝科技感的默认 Remotion 背景形成鲜明对比。

## 2. 为什么先实现 academic_sketch

| 维度 | 说明 |
|---|---|
| **需求明确** | 来自 remotion.html 的 academic 原型，视觉方向清晰 |
| **技术可行** | 纯 CSS/SVG 实现，无需引入 Rough.js 等新依赖 |
| **差异化明显** | 米白纸张 vs 深蓝科技，视觉对比最强 |
| **覆盖场景** | 论文解读、AI 原理解释、技术概念、研究报告 |
| **实现风险** | 低 — 不改现有 family 结构，只加背景层和叠加层 |

## 3. 实现了哪些视觉特征

### 背景层 (BackgroundLayer / academic_sketch case)

- **纸张背景色**: `#faf7f2`（暖米白，非纯白）
- **网格纸线条**: 32px 间隔，`rgba(180, 160, 120, 0.18)` 细线，带 frame 驱动的轻微 wobble
- **红色边距线**: 左侧 `12%` 处 + 顶部 `8%` 处，`rgba(220, 80, 60, 0.28)`
- **纸张纹理**: radial gradient 噪点叠加，模拟真实纸张
- **边缘晕影**: radial gradient 边缘暗化，增加纸张厚度感

### 批注叠加层 (AcademicSketchLayer)

- **SVG 手绘下划线**: 2 条 wavy path，stroke 2-2.5px，低透明度
- **手绘圆圈批注**: 椭圆虚线，出现在画面右上区域
- **手绘箭头**: 从左侧指向右上，带曲线手绘感
- **问号**: 2 个，手写斜体风格，分别在左上/右下
- **星号标注**: 底部居中
- **动画**: 2 秒淡入 + 持续 wobble（frame 驱动）

### 配色

- accent: `#b45309`（暖棕褐）
- highlight: `#d97706`（琥珀色）
- 两者都与纸张/墨水调性一致，不抢正文

### 正文可读性

- 叠加层 `zIndex: 12`，在内容之下
- 所有 SVG 元素 `opacity` ≤ 0.4
- `pointerEvents: none` 不阻挡交互

## 4. 没有实现哪些高级效果

以下为"未实现"项，留待后续扩展：

- ❌ Rough.js 风格的不规则线条（需要引入库）
- ❌ 手写字体渲染（需要 web font 或 SVG path 模拟）
- ❌ 墨水晕开动画（需要复杂 SVG filter）
- ❌ 公式渲染（需要 KaTeX/MathJax）
- ❌ 多纸张层叠（当前单层纸张）
- ❌ 橡皮擦除动画（需要 canvas 或复杂 SVG mask）

## 5. 接口说明

### POST /video-lab/style-family/visual-technique-matrix

**请求示例**：

```json
{
  "content": "研究显示，新一代 AI 模型在多模态理解、工具调用和复杂推理任务上都有显著提升，但评测指标仍然难以完整衡量真实智能。",
  "params": {
    "clipSeconds": 2,
    "keyPointCount": 2,
    "visualStylePreset": "warm_paper",
    "backgroundPreset": "warm_cinematic",
    "transitionStyle": "slide_fade"
  },
  "matrix": {
    "families": ["caption_story", "data_news", "timeline_news"],
    "visualTechniques": ["academic_sketch"]
  }
}
```

**响应**：

```json
{
  "items": [
    {
      "family": "caption_story",
      "visualTechnique": "academic_sketch",
      "success": true,
      "videoUrl": "/runtime/video_lab/experiments/clip_xxx/clip.mp4",
      "experimentId": "...",
      "clipSeconds": 2,
      "elapsedMs": 12345,
      "message": "",
      "warnings": []
    }
  ],
  "totalElapsedMs": 123456
}
```

**约束**：
- `families` 仅允许: `caption_story`, `data_news`, `timeline_news`
- `visualTechniques` 仅允许: `academic_sketch`（v1.2.4）
- 组合数 ≤ MAX_MATRIX_ITEMS = 9

## 6. 前端展示位置

- **入口**: `/video-lab/remotion-style-family` → 视觉技法矩阵 section（`#visual-technique-matrix`）
- **标签**: 视觉技法矩阵 · V1.2.4
- **默认**: 3 family × 1 technique = 3 clips
- **跳回**: `/video-lab/remotion-lab` → 效果样机库 → academic_sketch 卡片 → "前往生成 academic_sketch 样片" 按钮

## 7. 测试结果

```
tests/test_style_family_visual_technique_matrix.py
  test_visual_technique_matrix_passes_technique_params     PASSED
  test_visual_technique_matrix_injects_defaults            PASSED
  test_visual_technique_matrix_3_clips_at_limit            PASSED
  test_visual_technique_matrix_invalid_technique_returns_400 PASSED
  test_visual_technique_matrix_over_limit_returns_400      PASSED
  test_visual_technique_matrix_endpoint_valid_1x1           PASSED
  test_visual_technique_matrix_endpoint_empty_families_returns_400 PASSED
```

## 8. 实测结果

### 1×1 接口实测（caption_story × academic_sketch）

| 检查项 | 实际值 | 结果 |
|---|---|---|
| HTTP 状态码 | 200 | ✅ |
| items.length | 1 | ✅ |
| items[0].success | true | ✅ |
| items[0].family | caption_story | ✅ |
| items[0].visualTechnique | academic_sketch | ✅ |
| items[0].videoUrl | /runtime/video_lab/experiments/clip_ccc702e1/clip.mp4 | ✅ |
| videoUrl HTTP 访问 | 200, content-type: video/mp4, 210021 bytes | ✅ |

### 3 clips 接口实测（caption_story + data_news + timeline_news × academic_sketch）

| 检查项 | 实际值 | 结果 |
|---|---|---|
| HTTP 状态码 | 200 | ✅ |
| items.length | 3 | ✅ |
| success 数量 | 3/3 | ✅ |
| clip_ca7df3bb HTTP | 200 | ✅ |
| clip_6b73d4fb HTTP | 200 | ✅ |
| clip_2f8b07cb HTTP | 200 | ✅ |

## 9. 浏览器验收（待人工执行）

前端已启动于 http://localhost:3002，页面路径：`/video-lab/remotion-style-family`

**待人工观察**：
1. 背景是否为米白纸张色（#faf7f2）而非深蓝科技色？
2. 是否有可见的网格纸线条（32px 间隔）？
3. 是否有手绘批注元素（下划线/圆圈/问号/箭头）？
4. 红色边距线是否可见？
5. 正文是否仍然可读？
6. caption_story / data_news / timeline_news 三种 family 下是否都能保持学术草稿质感？

## 10. 当前结论

academic_sketch 最小真实渲染链路已接入。
- 接口实测通过（1×1 + 3 clips）
- 所有 videoUrl 均 HTTP 200 可访问
- 视觉效果仍需进一步人工样片对比
