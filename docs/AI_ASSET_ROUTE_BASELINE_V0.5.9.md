# V0.5.9 AI素材路线 Baseline 体检报告

## 分支与 Commit

- 分支：`feature/v0.3.6-b1-shotplan-standardization`
- 本次 commit：`docs: add ai asset route baseline inspection v0.5.9`
- 对比分支（V0.5.8 Pillow）：`e56f424`

## 使用内容摘要

同一份 AI 新闻内容（与 V0.5.8 Pillow 报告相同）：

| # | 标题 | 正文摘要 |
|---|---|---|
| 1 | ProReviewer评审系统突破 | 马尔可夫决策过程，5个质量维度比提示工程方法高39% |
| 2 | 购物AI助手测评结果不佳 | GPT/Claude/Gemini在Shopping Reasoning Bench通过率57–77% |
| 3 | 企业级AI加速落地 | Anthropic+TCS/DXC全球联盟；DeepMind千万美元多智能体安全研究 |

开篇语：**"不是模型更强，而是AI正在落地。"**

## AI素材路线当前实现位置

```
app/video_lab/adapters/ai_asset_then_compose.py    # Adapter（当前为mock，但visual route通了）
app/video_lab/renderers/visual/ai_asset_renderer.py # AiAssetVisualRenderer（已实现，接MiniMax图像API）
app/video_lab/renderers/frame_preview.py           # 支持ai_asset_then_compose的frame_preview
app/video_lab/renderers/visual/registry.py         # 已注册AiAssetVisualRenderer
app/video_lab/method_registry.py                   # 已注册ai_asset_then_compose
app/video_lab/models.py                            # AI_ASSET_THEN_COMPOSE = "ai_asset_then_compose"
```

**结论：AI素材路线是完整可运行的视觉合成路线（visual route），不是部分preview。**

通过 `run_tts_subtitle_compose` + `visualRoute=ai_asset_then_compose` 参数即可跑完整链路。

## Preview 运行结果

### 单帧 Preview（keypoint）

| 项目 | 值 |
|---|---|
| 是否成功 | ✅ 成功 |
| 输出路径 | `runtime/video_lab/experiments/preview_167e39b6/frames/frame_001.png` |
| 是否调用图像 API | ✅ 是（MiniMax image-01） |
| 耗时 | 28.1s（主要在AI生图） |
| 警告 | 无 |

### 单帧 Preview（cover）

| 项目 | 值 |
|---|---|
| 是否成功 | ✅ 成功 |
| 输出路径 | `runtime/video_lab/experiments/preview_60ce571b/frames/cover.png` |
| 是否调用图像 API | ✅ 是（MiniMax image-01） |
| 耗时 | 21.5s |
| 警告 | 无 |

### 动效片段 Preview（5s Ken Burns）

| 项目 | 值 |
|---|---|
| 是否成功 | ✅ 成功 |
| 输出路径 | `runtime/video_lab/experiments/preview_8c2998e3/frames/clip.mp4` |
| 效果 | ken_burns（FFmpeg zoompan缓慢缩放+淡入） |
| 耗时 | 27.6s |
| 警告 | 无 |

## 完整链路结果

通过 `run_tts_subtitle_compose(visualRoute=ai_asset_then_compose)` 执行：

| 项目 | 值 |
|---|---|
| 是否执行 | ✅ 是 |
| final video | `runtime/video_lab/experiments/ai_asset_full_95e8de24/final_with_audio.mp4` (3.0MB) |
| audio | `runtime/video_lab/experiments/ai_asset_full_95e8de24/audio/voiceover.mp3` (72.076s) |
| subtitle | `runtime/video_lab/experiments/ai_asset_full_95e8de24/subtitles/subtitles.srt` + `.ass` (13条) |
| manifest | `runtime/video_lab/experiments/ai_asset_full_95e8de24/manifest.json` |
| duration | 72.076s |
| failed | ❌ 否 |
| failed_reason | — |
| 背景生成 | ✅ 生成4张AI背景图（封面 + KP1 + KP2 + KP3） |
| 路由 | `route=ai_asset_then_compose`（通过tts_subtitle_compose的visualRoute参数传入） |
| 字幕烧入 | ✅ ASS字幕已烧入（subtitleBurned=True, subtitleFallback=False） |
| quality score | 5.0/5.0（全维度通过） |

### 生成背景详情

| 帧 | 主题词（prompt） | 背景图 | 意象 |
|---|---|---|---|
| 封面 | "AI前沿资讯" + 科技风 | `cover_bg.png` | 深蓝光斑+抽象线条 |
| KP1 | "ProReviewer评审系统突破" + 科技风 | `kp_1_bg.png` | 深蓝+神经网络/大脑意象 |
| KP2 | "Shopping Reasoning Bench测评结果" + 科技风 | `kp_2_bg.png` | 深蓝+金色光斑 |
| KP3 | "企业级AI加速落地" + 科技风 | `kp_3_bg.png` | 深蓝+城市/建筑意象 |

## 抽帧观察

帧位于 `D:/tmp/ai_asset_inspection/`（本地临时目录，不提交）。

### 封面帧

- **AI背景**：深蓝科技风格抽象背景，光斑+线条+光晕效果，电影质感
- **标题**："AI前沿资讯"白色大字，清晰
- **副标题**："今日要点速览"
- **三个标签**：ProReviewer / Shopping Reasoning / 企业级AI，清晰排列
- **整体氛围**：科技感强，有电影感，明显高于纯色/Pillow背景
- **问题**：无

### 关键点 1（frame_001，对应 KP1）

- **AI背景**：深蓝+神经网络/大脑意象，光感柔和
- **信息卡**：白色半透明背景（blur+opacity），左侧强调图标
- **标题**："ProReviewer评审系统突破"，清晰
- **正文**："马尔可夫决策过程，5维超提示工程"，高对比度可读
- **数字高亮**："39%"红色突出
- **字幕**：在底部，不遮挡正文
- **问题**：无明显问题

### 关键点 2（frame_002，对应 KP2）

- **AI背景**：深蓝+金色光斑，抽象线条
- **信息卡**：同KP1结构，白底黑字
- **标题**："Shopping Reasoning Bench测评结果"，清晰
- **正文**：GPT/Claude/Gemini通过率 57%/73%/77%，数字红色高亮
- **问题**：无明显问题

### 关键点 3（frame_003，对应 KP3）

- **AI背景**：深蓝+城市/建筑意象，橙色光斑点缀
- **信息卡**：同结构
- **标题**："企业级AI加速落地"，清晰
- **正文**：Anthropic与TCS/DXC联盟，DeepMind千万美元研究
- **问题**：无明显问题

### 总结页

- 左侧：深蓝科技风抽象背景（与封面风格统一）
- 右侧：三个要点简要回顾列表
- 无AI生图内容（总结页用代码渲染）
- 整体清晰简洁

## AI素材路线问题

### 当前无阻塞问题

本轮链路完整跑通，未遇到阻塞问题。

### 观察到的警告（非阻塞）

1. `Invalid highlightMode 'gradient', using 'auto'` — 参数名回退，不影响
2. `av-sync: frame durations aligned to 5 narration segments` — 正常的音画同步对齐信息

### 潜在风险（非本轮阻塞，但需关注）

1. **AI背景一致性**：4张背景图各有不同意象（大脑/光斑/建筑），整体视觉风格统一但有差异。正式使用时可能需要更严格控制风格一致性。
2. **图像生成失败回退**：单张图失败时会有警告但整体继续（设计上如此），极端情况可能部分帧无背景。
3. **风格固化**：默认风格为"深蓝科技风"，换主题（如娱乐、生活方式）需要手动调整 `imageStyle` 参数。

## Pillow / Remotion / AI素材 三路线初步对比

| 维度 | Pillow | Remotion | AI素材 | 判断 |
|---|---|---|---|---|
| 可读性 | ★★★★★ | ★★★★☆ | ★★★★☆ | Pillow文字最清晰；AI素材文字清晰但背景略抢眼 |
| 成片感 | ★★☆☆☆ | ★★★★★ | ★★★★☆ | Remotion最强；AI素材明显优于Pillow |
| 视觉氛围 | ★★☆☆☆ | ★★★★☆ | ★★★★★ | AI素材最强，科技感突出 |
| 信息密度 | ★★★★☆ | ★★★★☆ | ★★★★☆ | 三路线相近 |
| 字幕干扰 | ★★★★★ | ★★★★☆ | ★★★★★ | 底部字幕均不遮挡正文 |
| 生成速度 | ★★★★★（秒级） | ★★☆☆☆（分钟级） | ★★★☆☆（~50秒） | Pillow最快；AI素材中等 |
| 稳定性 | ★★★★★ | ★★★☆☆ | ★★★☆☆ | Pillow最稳；AI素材依赖API |
| 成本风险 | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | Pillow成本最低；AI素材单次多张图成本最高 |
| 适合场景 | 日常快讯、常规内容 | 精品内容、动效展示 | 重大发布、深度分析、氛围感强的内容 | — |

## 结论

### AI素材更适合

- 需要强视觉氛围的 AI 新闻/科技内容
- 重大产品发布、深度分析视频
- 需要在信息准确基础上增加"电影感"的场景
- 配合深蓝科技风主题（如本项目当前定位）

### AI素材不适合

- 日常快速产出（Pillow更合适）
- 成本敏感场景（AI图像生成成本明显高于纯渲染）
- 需要快速迭代的内容（AI生图 ~40s 额外耗时）
- 非科技/AI主题内容（如生活、娱乐、美食）
- 需要逐帧精确控制的场景（AI生图有随机性）

### 是否建议继续投入 AI素材路线

**建议：继续投入，但作为"视觉增强路线"而非"默认主路线"。**

理由：
1. **技术链路已通**：完整 TTS + 字幕 + AI背景 + 视频合成已跑通，质量评分 5.0
2. **视觉优势明确**：科技感显著强于 Pillow，适合 AI 新闻定位
3. **风险可控**：生成失败不影响整体（回退机制）；当前警告为非阻塞性
4. **与项目定位匹配**：AI新闻短视频 = 科技感 + 信息准确，AI素材路线天然契合
5. **与 Remotion 互补**：Remotion 强在动效，AI素材强在视觉氛围，可并行发展

**建议推进方式**：
- 下一阶段可探索 AI素材路线 + Remotion 字幕/动效的混合模式（Remotion 渲染文字+动效，AI素材做背景）
- 当前默认主路线保持 Pillow（或 Remotion），AI素材作为用户可选的高质量路线

## 下一步建议

1. **AI素材路线 - 视觉增强模式**：探索 AI背景 + Remotion 信息卡叠加的混合模式
2. **风格模板化**：固化 2-3 个 AI 背景风格模板（如科技蓝、暗黑金属、暖色调），降低风格随机性
3. **Prompt 优化**：针对不同内容类型（学术、商业、娱乐）优化图像生成 Prompt
4. **成本评估**：量化单次视频的图像生成成本，与 TTS API 成本对比
5. **稳定性监控**：连续生成 10 条视频，统计图像生成成功率
