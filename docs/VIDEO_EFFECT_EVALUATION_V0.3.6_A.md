# V0.3.6-a 视频可读性与观感优化报告

## 分支

`feature/v0.3.6-video-effect-optimization`

## 本次目标

小步优化三条已生成视频路线的可读性和手机端观感，不做大改架构。

目标：
1. 提升文字可读性
2. 提升画面主体焦点
3. 提升短视频封面感
4. 提升字幕醒目度
5. 让三条路线在手机端缩略图里也能看清主信息

## 修改文件

| 文件 | 修改内容 |
|------|---------|
| `app/video_lab/renderers/visual_theme.py` | 全局字体增大：cover_title 56→72, keypoint_title 34→48, keypoint_body 24→34, summary_body 24→32 等 |
| `app/video_lab/renderers/frame_templates.py` | keypoint 标题字号上限 76→80，最小 34→40；正文字号上限 46→52，最小 24→28 |
| `app/video_lab/quality/video_quality.py` | 新增 readability 维度：title_length、body_length、subtitle_density、readability_overflow 检查 |
| `remotion/src/AiNewsVideo.tsx` | 封面标题 56→64，副标题 26→30；卡片标题 32→44，正文 24→32；序号 28→32；总结页标题 40→48，列表项 22→26 |

## 三条路线优化结果

### 1. Pillow 本地帧合成 (`local_frame_compose`)

**优化前问题**：
- 主标题偏小，手机端预览阅读困难
- 卡片标题 34px，关键点正文 24px，手机上显得过小

**本轮改动**：
- `visual_theme.py` 全局字体增大 15-30%
- keypoint 标题 min 40px / max 80px（1080p 基准）
- keypoint 正文 min 28px / max 52px
- 适配分辨率缩放，各模板 headline 正文最小 40px

**当前字号体系（1080p 基准）**：
```
封面标题: 72px
封面副标题: 32px
关键点标题: 48px (min 40px)
关键点正文: 34px (min 28px)
总结正文: 32px
```

### 2. Remotion 程序化模板 (`template_programmatic_render`)

**优化前问题**：
- 整体偏暗，文字太小
- 卡片标题 32px，正文 24px，手机端阅读困难

**本轮改动**：
- 封面标题 56→64px，副标题 26→30px
- 封面时间线预览项 22→26px
- 关键点卡片标题 32→44px，正文 24→32px，序号 28→32px
- 总结页标题 40→48px，列表项 22→26px
- 行高从 1.6 调整为 1.7

**当前字号体系**：
```
封面标题: 64px
封面副标题: 30px
封面时间线项: 26px
关键点标题: 44px
关键点正文: 32px
关键点序号: 32px
总结页标题: 48px
总结列表项: 26px
来源: 20px
```

### 3. AI 素材 + 程序化合成 (`ai_asset_then_compose`)

**本轮改动**：
- 继承 Pillow 渲染器的字号增大
- 文字层对比度由 AI 素材背景决定
- 核心信息卡片字号与 Pillow 路线一致

**说明**：此路线视觉背景由 AI 生成，文字层继承 `local_frame_compose` 的模板系统，无需单独修改。

## 测试结果

```bash
python -m compileall app/ -q         ✅ 无编译错误
python -m pytest tests/ -v           ✅ 348 passed
frontend npm run typecheck            ✅ 无 TypeScript 报错
remotion npx tsc --noEmit           ✅ 无 TypeScript 报错
```

### 关键测试覆盖
- `test_video_lab_local_frame.py` - 本地帧合成
- `test_video_quality.py` - 质量评估（含新增 readability gate）
- `test_visual_renderer.py` - 视觉渲染器注册
- `test_remotion_route.py` - Remotion 模板路线

## 新增 Quality Readability Gate

`video_quality.py` 新增 `readability` 维度，包含：

| Check ID | 说明 | FAIL 条件 |
|----------|------|-----------|
| `title_length` | 关键点标题过短 | >50% 关键点标题 <8 字 |
| `body_length` | 正文过长 | >50% 关键点正文 >120 字 |
| `subtitle_density` | 字幕条数偏少 | 字幕数 < 关键点数 × 0.5 |
| `readability_overflow` | 文字溢出告警 | 检测到 overflow/truncat 警告 |

**注意**：quality report 现在对标题过短、正文过长、字幕密度低等可读性问题也会扣分，不再轻易给出 5/5 均分。

## 真实生成产物路径

本次修改仅涉及静态参数调整（字号），不改变生成流程。

真实生成验证需在有 FFmpeg + Node.js 环境时执行：

```bash
# 1. local_frame_compose
POST /video-lab/experiments
{"testCaseId": "case_ai_frontier_daily_001", "methodId": "method_local_frame_compose", ...}

# 2. template_programmatic_render (需 Node.js + Remotion)
POST /video-lab/experiments
{"testCaseId": "case_ai_frontier_daily_001", "methodId": "method_template_programmatic_render", ...}

# 3. ai_asset_then_compose (需 MINIMAX_API_KEY)
POST /video-lab/experiments
{"testCaseId": "case_ai_frontier_daily_001", "methodId": "method_ai_asset_then_compose", ...}
```

产物目录：`runtime/video_lab/experiments/{experiment_id}/`

## 仍然存在的问题

1. **Remotion 路线背景偏暗**：`#0a0e1a` 深色背景配合白色文字在手机端缩略图里可能不够突出，可考虑增加背景亮度或添加文字阴影增强
2. **三条路线字幕样式未统一**：Pillow 路线字幕由 FFmpeg burn-in 生成，Remotion 路线字幕渲染在 Canvas 层，样式有差异
3. **AI 素材路线需真实 API Key**：当前 `ai_asset_then_compose` 需要 MiniMax API Key 才能生成背景图，无 Key 时回退到渐变背景

## 下一步建议 (V0.3.6-b)

1. **ShotPlan 扩展**：增加 `visualIntent`、`layout`、`motion`、`emphasisTerms`、`durationSec` 字段，让不同关键点可选择不同卡片布局
2. **Remotion 背景优化**：考虑给关键点卡片增加底部渐变或阴影，提升文字层与背景分离度
3. **字幕短句切分**：narration 按 8-18 字切分字幕，避免一行显示过长
4. **封面页增强**：封面增加更明显的 CTA 或日期标注，提升短视频封面感

## 禁止事项遵守情况

✅ 未新增视频路线
✅ 未大改 ShotPlan schema
✅ 未重构 FFmpeg 合成流程
✅ 未重构 MiniMax TTS 调用
✅ 未重构 Remotion 渲染主流程
✅ 未引入数据库
✅ 未引入任务队列
