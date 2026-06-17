# V1.2.4 Visual Style Preset Matrix 探索记录

## 一、为什么需要 Visual Style Preset

**背景 ≠ 风格。**

现有的 Remotion 能力中，`backgroundPreset` 控制背景动画（科技网格、极光、玻璃等），但它不控制：

- 页面整体色调（浅色 vs 深色 vs 高对比）
- 卡片底色和边框
- 文字颜色层级
- 强调色策略
- 动效气质（克制 vs 活泼 vs 强冲击）

同一种背景 preset（tech_grid_dark）搭配不同的视觉风格，可以呈现完全不同的"气质"。

---

## 二、为什么第一批只做 3 个

1. **覆盖核心诉求**：浅色（light_editorial）/ 稳妥（warm_paper）/ 惊艳（bold_magazine）
2. **渲染成本可控**：3 × 3 = 9 clips，仍在 MAX_MATRIX_ITEMS=9 限制内
3. **便于人工观察差异**：三种风格对比鲜明，容易判断是否有效
4. **不依赖外部素材**：完全由 Remotion 程序化渲染

---

## 三、三个视觉风格定义

### 1. light_editorial（浅色科技媒体）

| 维度 | 设计 |
|------|------|
| 定位 | 白底资讯 / 清爽报告 |
| 主背景 | #ffffff（纯白） |
| 卡片底色 | #ffffff |
| 文字主色 | #0f172a（深蓝黑） |
| 文字次色 | #334155（次级灰） |
| 强调色 | #3b82f6（科技蓝） |
| 高亮色 | #0ea5e9（青色） |
| 边框色 | #e2e8f0（浅灰） |
| 动效气质 | gentle（柔和克制） |
| 禁止 | 大面积深蓝背景、霓虹、强烈黑底 |

### 2. warm_paper（稳妥纸张报告）

| 维度 | 设计 |
|------|------|
| 定位 | 米白纸张 / 咨询报告 / 日报 |
| 主背景 | #faf8f5（米白） |
| 卡片底色 | #faf8f5 |
| 文字主色 | #292524（深棕） |
| 文字次色 | #44403c（次级棕） |
| 强调色 | #b45309（琥珀） |
| 高亮色 | #d97706（橙黄） |
| 边框色 | #e7e5e4（暖灰） |
| 动效气质 | restrained（克制静态） |
| 禁止 | 科技蓝主导、高饱和霓虹 |

### 3. bold_magazine（惊艳杂志爆点）

| 维度 | 设计 |
|------|------|
| 定位 | 杂志封面 / 高冲击 / 惊艳但可读 |
| 主背景 | #0a0a0a（近黑） |
| 卡片底色 | #0a0a0a |
| 文字主色 | #fafafa（纯白） |
| 文字次色 | #e4e4e7（次级白） |
| 强调色 | #ef4444（红色） |
| 高亮色 | #f97316（橙色） |
| 边框色 | #27272a（暗灰） |
| 动效气质 | energetic（强冲击） |
| 注意 | 惊艳不等于不可读；标题和关键点必须清楚 |

---

## 四、后端接口

### 接口

```
POST /video-lab/style-family/visual-style-matrix
```

### 请求体

```json
{
  "content": "OpenAI 发布新一代多模态模型，重点提升语音、图像和视频理解能力。",
  "params": {
    "clipSeconds": 2,
    "keyPointCount": 2
  },
  "matrix": {
    "families": ["data_news", "dashboard_brief", "caption_story"],
    "visualStylePresets": ["light_editorial", "warm_paper", "bold_magazine"]
  }
}
```

### 响应体

```json
{
  "items": [
    {
      "family": "data_news",
      "visualStylePreset": "light_editorial",
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

### 约束

- families 过滤到允许值后为空 → 400
- visualStylePresets 过滤到允许值后为空 → 400
- 组合数 > 9 → 400（含清晰错误信息）

---

## 五、Remotion 实现

### data.ts

新增类型：

```ts
export type VisualStylePreset = "light_editorial" | "warm_paper" | "bold_magazine";
```

扩展 `RemotionStyle` 接口：

```ts
visualStylePreset?: VisualStylePreset;
```

### props_builder.py

`visualStylePreset` 只在白名单内透传：

```python
visual_style_preset = rstyle.get("visualStylePreset") or params.get("visualStylePreset")
if visual_style_preset in ("light_editorial", "warm_paper", "bold_magazine"):
    style["visualStylePreset"] = visual_style_preset
```

### AiNewsVideo.tsx

新增 `resolveVisualStyleTokens(preset)` 返回视觉 token：

```ts
{
  surfaceBackground,  // 主背景色
  surfaceTextPrimary,  // 主文字色
  surfaceTextSecondary,
  surfaceAccent,
  surfaceHighlight,
  surfaceBorder,
  motionTone,         // "gentle" | "restrained" | "energetic"
}
```

`BackgroundLayer` 组件使用 `tokens.surfaceBackground` 替换硬编码的深色背景值，使三种视觉风格得以在白色/米白/黑色背景间切换。

所有 `BackgroundLayer` 调用点均已透传 `visualStylePreset` 参数。

---

## 六、前端展示位置

- `/video-lab/remotion-style-family` → 新增「视觉风格矩阵 · V1.2.4」区域（3×3 网格）
- `/video-lab/remotion-lab` → 视觉风格 tab → 新增「前往生成视觉风格矩阵 →」按钮

---

## 七、测试结果

| 测试 | 结果 |
|------|------|
| test_visual_style_matrix_passes_preset_params | ✅ |
| test_visual_style_matrix_3x3_at_limit | ✅ |
| test_visual_style_matrix_over_limit_returns_error | ✅ |
| test_visual_style_matrix_invalid_preset_returns_error | ✅ |
| test_visual_style_matrix_endpoint_filters_supported_values | ✅ |
| test_visual_style_matrix_endpoint_empty_families_returns_400 | ✅ |

---

## 八、当前结论

**工程能力通过，视觉效果待人工验收。**

- 三个 visualStylePreset 参数已透传到 Remotion
- `resolveVisualStyleTokens` 返回正确的色值 token
- `BackgroundLayer` 使用 token 替换了深色硬编码背景
- 9-clip 限制有效
- invalid input 400 错误有效

**待验证**：
- light_editorial 在 9:16 视频中白色背景是否影响文字可读性
- warm_paper 的米白色调是否与数据图表冲突
- bold_magazine 的高对比是否导致视觉疲劳

---

## 九、禁止事项

- 不新增更多 visualStylePreset
- 不改 Style Sweep 主链路
- 不改 Style Gallery promote
- 不把 visualStylePreset 写入正式 presets.py
- 不默认一次生成超过 9 个 clip
