# V0.3.6-a2 字幕、封面、卡片聚焦优化报告

## 分支

`feature/v0.3.6-a2-caption-cover-card-polish`

## 修改摘要

| 优化项 | 文件 | 改动 |
|--------|------|------|
| 字幕增强 | `subtitle_planner.py` | font_size 32→36, margin_v 240→150 (距底部120-180px), shadow 1→3, back_colour 99→BB (更不透明底板), max_chars 18→22 |
| 封面页增强 | `frame_templates.py` | 顶部标签 "AI Frontier Radar"→"AI前沿"; 标题上移; 新增 hook 句; 标签字号×1.25, padding 16→20, radius 10→14, border width 1→2 |
| 今日重点卡片化 | `frame_templates.py` | 从文本列表改为3条半透明卡片，固定 card_height，集中于画面中部，减少空白 |
| Remotion 关键词高亮 | `AiNewsVideo.tsx` | 新增 `extractHighlights()` + `HighlightedText` 组件，自动识别数字/百分比并用 highlight 色渲染 |

---

## 字幕增强详情

**文件**: `app/video_lab/planners/subtitle_planner.py`

**DEFAULT_ASS_STYLE 变更**:
```
font_size:    32 → 36  (更大更醒目)
margin_v:     240 → 150 (距底部 120-180px，避免播放器控制条遮挡)
shadow:       1 → 3    (更强阴影分离度)
back_colour:  99 → BB  (半透明黑色底板更不透明)
max_chars:    18 → 22  (字幕宽度约 72-82%)
```

**不修改**: 主合成流程、FFmpeg 命令行参数、ASS 格式解析逻辑。

---

## 封面页增强详情

**文件**: `app/video_lab/renderers/frame_templates.py`

| 元素 | 优化前 | 优化后 (V0.3.6-a2) |
|------|--------|-------------------|
| 顶部标签 | "AI Frontier Radar" | "AI前沿" (更简洁) |
| 标题位置 | 居中偏下 | 上移约60px，给hook留空间 |
| Hook句 | 无 | subtitle 文本或"今天这3件事，值得注意" |
| 标签字号 | 22px | 27px (+25%) |
| 标签padding | 16 | 20 |
| 标签圆角 | radius 10 | radius 14 |
| 标签边框 | 1px | 2px |
| 标签间距 | 30px | 40px |

---

## 今日重点卡片化详情

**文件**: `app/video_lab/renderers/frame_templates.py`

**优化前**: 4条文本列表，大面积空白，编号不醒目
**优化后**: 3条半透明卡片，固定高度，集中于画面中部

```
布局: title(12%) → 装饰线 → cards(32%-88%) → footer(8%)
每卡片: 左侧蓝色竖条 + 编号 + 标题
卡片间距: height * 0.03
```

---

## Remotion 关键词高亮详情

**文件**: `remotion/src/AiNewsVideo.tsx`

**新增函数**:
- `extractHighlights(text)`: 识别百分比(88.9%, 72%)、数量词(10倍, 5620亿, 10万)、独立数字
- `HighlightedText`: React 组件，将识别出的词段着 highlight 色 (C.highlight = `#f59e0b`)

**应用位置**: KeyPointCard 的 title 和 body 均通过 `<HighlightedText>` 渲染

**不修改**: 正文布局，highlights 识别失败时正常渲染。

---

## 三条路线生成结果

### 测试执行

```bash
python -m compileall app/ -q                          ✅ 无编译错误
python -m pytest tests/test_video_lab_local_frame.py  ✅ 26 passed
python -m pytest tests/test_video_quality.py          ✅ 6 passed
python -m pytest tests/test_visual_renderer.py         ✅ 9 passed
python -m pytest tests/test_remotion_route.py          ✅ 11 passed
cd frontend && npm run typecheck                       ✅ 无 TS 报错
cd remotion && npx tsc --noEmit                      ✅ 无 TS 报错
```

### 模板渲染验证

```
Cover template:   ✅ 成功生成 cover.png
Overview template: ✅ 成功生成 overview.png, itemCount=3
ASS subtitle:    ✅ 2条字幕, font_size=36, margin_v=150, back_colour=&HBb000000
```

### 三条路线覆盖情况

| 路线 | 字幕 | 封面 | 今日重点 | 关键词高亮 | 备注 |
|------|------|------|----------|-----------|------|
| `local_frame_compose` (Pillow) | ✅ ASS样式 | ✅ 封面hook | ✅ 卡片化 | N/A | 用 FFmpeg burn-in |
| `template_programmatic_render` (Remotion) | N/A | ✅ 封面hook | ✅ 卡片化 | ✅ 新增 | Canvas渲染 |
| `ai_asset_then_compose` (AI素材+Pillow) | ✅ ASS样式 | ✅ 封面hook | ✅ 卡片化 | N/A | AI背景+文字卡 |

---

## 真实视频生成

需在有 FFmpeg + (Remotion路线需 Node.js) + (AI素材路线需 MINIMAX_API_KEY) 的环境执行：

```bash
# 1. local_frame_compose
POST /video-lab/experiments
{"testCaseId": "case_ai_frontier_daily_001", "methodId": "method_local_frame_compose", "params": {...}}

# 2. template_programmatic_render (需 Node.js)
POST /video-lab/experiments
{"testCaseId": "case_ai_frontier_daily_001", "methodId": "method_template_programmatic_render", "params": {...}}

# 3. ai_asset_then_compose (需 MINIMAX_API_KEY)
POST /video-lab/experiments
{"testCaseId": "case_ai_frontier_daily_001", "methodId": "method_ai_asset_then_compose", "params": {...}}
```

**产物目录**: `runtime/video_lab/experiments/{experiment_id}/`

**验证清单** (生成后人工检查):
- [ ] 字幕是否距离底部 120-180px，无遮挡
- [ ] 封面是否有 hook 句，点击理由明确
- [ ] 今日重点是否3条卡片，集中无空白
- [ ] Remotion 关键点页数字/百分比是否高亮显示

---

## 仍然存在的问题

1. **Remotion 路线 hook 句未统一**: 封面 hook 句依赖 subtitle 字段，若 subtitle 为空才用默认句；建议后续在 ShotPlan 层保证 opening 字段有值
2. **三条路线封面 hook 句未对齐**: Pillow 路线用 subtitle，Remotion 路线也用 subtitle；建议后续统一从 ShotPlan.opening 取值
3. **Remotion highlight 暂不支持中文数字词**: 如"五"不会高亮（只识别阿拉伯数字+单位）；如需支持专业术语高亮，需在 `extract_highlights_by_mode` 增加字典模式
4. **字幕 ASS 底板颜色固定**: 黑色底板在纯白/纯亮背景视频上可能不协调；建议后续支持 `back_colour` 按背景亮度自动调整

---

## 下一步建议 (V0.3.6-b)

1. **ShotPlan.opening 字段标准化**: 让封面 hook 句从 ShotPlan 语义层传入，而不是依赖 subtitle 字段回退
2. **Remotion highlight 增强**: 支持按字典匹配专业术语（模型名、机构名），不只是数字
3. **字幕底板自适应**: 检测背景亮度，亮背景用深色底板，暗背景用带描边的白色字
4. **三条路线封面元素对齐**: 确认 Pillow 封面和 Remotion 封面使用一致的 hook 文案策略
5. **视频截图验证流程**: 建议在 `scripts/generate_ai_frontier_sample.py` 后自动截取封面/今日重点/关键点三帧截图

---

## 禁止事项遵守情况

| 禁止项 | 遵守 |
|--------|------|
| 不新增视频路线 | ✅ |
| 不扩展完整 ShotPlan schema | ✅ (仅改 DEFAULT_ASS_STYLE 和模板渲染参数) |
| 不重构 FFmpeg 合成流程 | ✅ |
| 不重构 MiniMax TTS 调用 | ✅ |
| 不重构 Remotion 渲染主流程 | ✅ |
| 不引入数据库/任务队列 | ✅ |
| 不大改前端页面结构 | ✅ |
