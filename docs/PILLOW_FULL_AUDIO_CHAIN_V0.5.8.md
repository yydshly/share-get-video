# V0.5.8 Pillow 带音频整片对比报告

## 分支与 Commit

- 分支：`feature/v0.3.6-b1-shotplan-standardization`
- 最新 commit：`bb414c7 docs: add V0.5.7 handoff summary for cross-model continuation`

---

## 使用内容摘要

两条路线使用完全相同的 AI 新闻内容，3条关键点，约 56–85 秒竖屏视频：

| # | 标题 | 正文摘要 |
|---|---|---|
| 1 | ProReviewer评审系统突破 | 马尔可夫决策过程，5个质量维度比提示工程方法高39% |
| 2 | 购物AI助手测评结果不佳 | GPT/Claude/Gemini在Shopping Reasoning Bench通过率57–77% |
| 3 | 企业级AI加速落地 | Anthropic+TCS/DXC全球联盟；DeepMind千万美元多智能体安全研究 |

开篇语：**"不是模型更强，而是AI正在落地。"**
结语：**"AI落地加速，安全与评估成新焦点。"**

---

## Pillow 完整链路结果

- **实验 ID**：`web_local_frame_compose_fca5e1f8`
- **生成时间**：2026-06-15T10:25
- **final video**: `runtime/video_lab/experiments/web_local_frame_compose_fca5e1f8/final_with_audio.mp4` (1.79 MB)
- **audio**: `.../audio/voiceover.mp3`
- **subtitle**: `.../subtitles/subtitles.srt` + `subtitles.ass`
- **manifest**: `.../manifest.json`
- **duration**: 56.8s（视频轴），56.0s（画面规划），比率 0.99
- **subtitleCount**: 11 条 ASS 字幕，烧入成功
- **failed**: 否
- **failed_reason**: N/A
- **帧结构**：cover(1.5s) + fade → overview(2.0s) + fade → frame_001 keypoint1(14.4s) + fade → frame_002 keypoint2(18.8s) + fade → frame_003 keypoint3(16.4s) + fade → summary(3.7s)，共 6 个主体帧 + 20 个 Ken Burns 过渡帧（fade_XX_XXX.png，每帧 0.08s）

---

## Remotion 对比对象

- **来源**：复用已有 Remotion 整片（`web_template_programmatic_render_fb270ca2`，2026-06-14T17:15）
- **final video**: `runtime/video_lab/experiments/web_template_programmatic_render_fb270ca2/final_with_audio.mp4` (2.51 MB)
- **manifest**: `.../manifest.json`
- **duration**: 85.3s
- **subtitleCount**: 12 条 ASS 字幕，烧入成功
- **segment**: cover(8.9s) + keypoint1(19.0s) + keypoint2(26.4s) + keypoint3(22.6s) + summary(8.4s)

> 注：Remotion 与 Pillow 使用相同内容但标题措辞略有不同（Remotion："AI前沿：多领域突破与挑战并存" vs Pillow 更强调落地感），时长 Remotion 更长（85s vs 57s）。

---

## Pillow 抽帧观察

### 封面帧

- 深色背景，白色大标题"AI前沿：多领域突破与挑战并存"居中
- 副标题"今日 AI 前沿速览"置于标题下方
- 无 Ken Burns 动画（静帧）
- 字幕烧入位置：底部居中，白色描边
- 整体：干净、严肃、阅读感强，无截断无溢出

### 关键点 1（frame_001，14.4s 停留）

- 深色内容卡片布局，白底黑字
- 标题"ProReviewer评审系统突破"清晰
- 正文"ProReviewer系统将评审过程建模为马尔可夫决策过程，在五个质量维度上比传统提示工程方法高出39%"，关键数字"39%"红色高亮
- 数据卡：39% 用红色强调，位置自然
- 字幕叠加在画面下方，不遮挡正文关键区域
- 无文本溢出，无截断
- Ken Burns 效果：缓慢推进（fade_00_XXX.png 序列，4帧×0.08s），肉眼看几乎察觉不到

### 关键点 2（frame_002，18.8s 停留）

- 布局结构与 KP1 一致
- 正文覆盖 Shopping Reasoning Bench 测评，GPT/Claude/Gemini 通过率 57-77%
- "57%"、"77%" 有红色高亮
- 字幕分多条（对应 TTS 分句），逐条显示
- 无溢出，无截断

### 关键点 3（frame_003，16.4s 停留）

- 正文覆盖企业级AI落地（Anthropic+TCS/DCX，DeepMind千万美元投资）
- 数据"千万美元"有强调
- 字幕显示正常

### 总结页（summary.png，3.7s 停留）

- 深色背景，白色文字
- 结语"不是模型更强，而是AI正在落地。AI落地加速，安全与评估成新焦点。"
- 居中布局，无截断
- 停留时间 3.7s（Remotion 总结页 8.4s），略短但可接受

### 整体观察

- 字幕烧入位置合理，不遮挡正文
- 关键数字高亮一致呈现
- Ken Burns 过渡帧（fade_XX_XXX.png）非常细微，4帧×0.08s 推进，对观感影响极小
- 整体画面稳定，无抖动，无闪烁
- 成片刻意感弱，偏向静态信息展示

---

## Remotion 抽帧观察

### 封面帧

- 全屏深色背景 + 动态标题入场动画
- 主标题"AI前沿：多领域突破与挑战并存"有 zoom-in 入场效果
- 副标题淡入
- 持续 8.9s，有明显动效，封面感强
- 字幕从第 5s 开始烧入

### 关键点页

- 全屏卡片入场动画（从下方滑入 + fade）
- 标题 + 正文分两层显示，有淡入时序差
- 数字（39%、57-77%）有明显高亮框或色块强调
- 停留时间长（19-26s/卡），阅读从容
- 字幕随旁白逐句出现
- 动效丰富：卡片入场、标题淡入、数字强调

### 总结页

- 深色背景，内容淡入
- 结语分两行显示
- 持续 8.4s，时间充裕
- 有去画面感（总结感强）

---

## Pillow vs Remotion 对比表

| 维度 | Pillow | Remotion | 判断 |
|---|---|---|---|
| 可读性 | ✅ 文字清晰不遮挡 | ✅ 文字清晰不遮挡 | 平局 |
| 信息密度 | ✅ 数字高亮一致 | ✅ 数字高亮更醒目（色块框） | Remotion 小优 |
| 成片感 | ⚠️ 静态为主，Ken Burns极轻微 | ✅ 卡片动效丰富，入场动画 | **Remotion 明显优** |
| 动效吸引力 | ❌ Ken Burns 4帧×0.08s 几不可感知 | ✅ 每卡入场动画，标题时序动画 | **Remotion 碾压** |
| 字幕干扰 | ✅ 底部居中，不挡正文 | ✅ 底部居中，不挡正文 | 平局 |
| 节奏与旁白匹配 | ✅ 字幕分句合理 | ✅ 字幕分句 + 停留时间更长 | Remotion 稍优 |
| 生成稳定性 | ✅ 路径确定，无构建风险 | ⚠️ Remotion 构建可能失败 | **Pillow 优** |
| 生成速度 | ✅ 快速（秒级帧合成） | ❌ 慢（Remotion 渲染分钟级） | **Pillow 碾压** |
| 时长 | 56.8s（偏短但合规） | 85.3s（更从容） | Remotion 优 |
| 适合场景 | 快速批量、稳定输出 | 精品单片、封面感重要 | 场景分离 |

---

## 结论

### Pillow 更适合

- **批量生成场景**：无构建风险，路径稳定，出片速度快（秒级）
- **不需要封面感的内容**：信息密集的干货分享，不需要动画封面
- **技术/代码类内容**：静态排版清晰，无视觉噪音
- **需要稳定可复现的管道**：没有 Remotion 的 Node.js 构建依赖

### Remotion 更适合

- **需要成片感的对外分享**：封面动画、卡片入场、数字动效带来更强的"视频感"
- **精品内容**：有时间和资源做单片打磨的场景
- **强调视觉吸引力的内容**：开篇 8.9s 的标题动画是 Pillow 难以复制的

### 当前默认主路线建议

| 场景 | 推荐路线 |
|---|---|
| 每日资讯速览 / 批量产出 | **Pillow**（local_frame_compose） |
| 精品单片 / 重要选题 | **Remotion**（template_programmatic_render） |

**本轮验证结论**：Pillow 完整音频链路技术可行性已确认，输出质量满足"信息传递清晰、无明显错误"标准。Ken Burns 效果极轻微，如需提升成片感应优先考虑其他过渡方案（如 crossfade），而非依赖当前的 4×0.08s fade 序列。

---

## 发现的问题

1. **Ken Burns 过渡过于轻微**：当前 fade_XX_XXX.png 每组仅 4 帧 × 0.08s = 0.32s 的推进，视觉几乎不可感知。如需提升画面活力，需要更长的过渡动画或更强的缩放幅度。

2. **Pillow 总结页停留时间偏短**：3.7s vs Remotion 8.4s，旁白已结束但画面可能未充分消化。建议检查 TTS 尾端与画面时序对齐。

3. **Remotion 关键点2时长偏长**（26.4s），导致整体节奏前轻后重，与 Pillow 节奏差异较大，不适合直接逐帧对比。

---

## 下一步建议

1. **Pillow 过渡增强**：尝试 8-12 帧 Ken Burns（0.27-0.4s 推进），或引入 crossfade 替代序列帧
2. **Pillow 封面帧**：封面没有 Ken Burns，建议给封面帧增加标题打字机效果或淡入
3. **Remotion vs Pillow 横向 A/B 测试**：用同一内容各生成 5 条，收集用户主观评分（成片感/可读性/分享意愿）
4. **AI素材路线**（mini_max_asset_compose）尚未体验，本轮范围外，待后续验证
