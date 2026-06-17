# V1.2.3 Remotion 模板差异化与背景丰富度审计

> 本文档审计 V1.2.3 当前 Remotion 模板体系的视觉差异化与背景丰富度，**不包含任何代码改造**。
> 范围：`remotion/src/AiNewsVideo.tsx`、`remotion/src/Root.tsx`、`remotion/src/data.ts`、`app/video_lab/style_gallery/presets.py`、`app/video_lab/renderers/remotion/`。

---

## 1. 阶段结论

1. Remotion 路线（`template_programmatic_render`）共 **14 个 style** 预置，分布在 **5 个表现范式**（family）下
2. 14 个样式中：
   - **5 个**走默认 `data_news` 范式 + 配色/动效旋钮差异（高变体密度，但视觉差异不够大）
   - **3 个**走 `dashboard_brief` 范式 + familyVariant 差异（chart_story / ranking_strip / 默认）
   - **2 个**走 `caption_story` 范式 + familyVariant 差异（caption_intro / cta_overlay）
   - **2 个**走 `timeline_news` 范式（默认 + route_map 变体）
   - **1 个**走 `card_stack` 范式（card_stack_peek）
3. 表现范式层（family）差异化做得较好，但**同一范式内的样式几乎只换了配色 + 动效强度**，版式结构高度同质化
4. 背景实现走 4 个 CSS preset（`tech_grid_dark` / `aurora_blue` / `glass_dashboard` / `warm_cinematic`），但 **CSS 表达力有限**，无图片/视频/粒子层，背景丰富度偏弱
5. 文本展示存在 **descMaxChars 硬截断 + 卡片高度固定（cardMinHeight 480~620）** 两个问题，长正文会被截断或撑出卡片
6. 优先改造目标（按 P0 / P1 / P2 分级）已识别，建议先做 **3B-2A 修复文本硬截断**

---

## 2. 当前 Remotion 样式清单

> 14 个 style 全部来自 `app/video_lab/style_gallery/presets.py`，由 `app/video_lab/renderers/remotion/props_builder.py` 透传到 Remotion。

| # | styleId | styleName | remotionFamily | familyVariant | cover / overview / metric | 入口组件 | 主要布局 | 背景特征 | 动效强度 | 文本策略 | 初步问题 |
|---|---------|-----------|----------------|---------------|---------------------------|----------|----------|----------|----------|----------|----------|
| 1 | `remotion_metric_motion` | 动态数据栏目 | `data_news` | — | editorial / timeline / countup_bar | AiNewsVideo（DataNewsLayout） | 居中大卡 + 数字条 | tech_grid_dark | medium | 截断 56 字 | 与 #2 #3 #4 配色/动效差异小 |
| 2 | `remotion_cinematic` | 电影感快讯 | `data_news` | — | cinematic / grid / countup_number | 同上 | 居中大卡 + 数字 | warm_cinematic | low | 截断 56 字 | 强氛围，但版式与 #1 几乎一致 |
| 3 | `remotion_minimal_clean` | 极简动效 | `data_news` | — | minimal / clean / none | 同上 | 居中大卡（无数据图） | tech_grid_dark | low | 截断 56 字 | 动效去除后，版式仍与 #1 几乎一致 |
| 4 | `remotion_high_energy` | 高能快剪 | `data_news` | — | editorial / timeline / countup_bar | 同上 | 居中大卡 + 数字条 | tech_grid_dark | high | 截断 56 字 | 节奏最快，但版式仍与 #1 几乎一致 |
| 5 | `remotion_neon_grid` | 霓虹网格 | `data_news` | — | cinematic / grid / countup_bar | 同上 | 居中大卡 + 数字条 | tech_grid_dark | high | 截断 56 字 | 配色不同，版式仍与 #1 几乎一致 |
| 6 | `remotion_card_stack` | 卡片叠层 | `card_stack` | — | editorial / timeline / countup_bar | `CardStackLayout` | 卡片堆叠（前/中/后） | aurora_blue | medium | 截断 56 字 | 范式差异化做得最好，但仅 1 个 |
| 7 | `remotion_timeline_news` | 时间线快讯 | `timeline_news` | — | editorial / timeline / countup_number | `TimelineNewsLayout` | 垂直时间线 + 节点高亮 | tech_grid_dark | medium | 截断 56 字 | 范式差异化做得较好，但仅 1 个默认变体 |
| 8 | `remotion_timeline_route_map` | 路线图时间线 | `timeline_news` | `route_map` | editorial / timeline / countup_number | 同上 | 横向路线节点 | tech_grid_dark | medium | 截断 56 字 | variant 变体；与 #7 仅在节点排布上略有差异 |
| 9 | `remotion_dashboard_brief` | 指标看板快报 | `dashboard_brief` | — | minimal / grid / countup_number | `DashboardBriefLayout` | 指标卡 + 活动信号 | glass_dashboard | medium | 截断 56 字 | 范式差异化做得较好 |
| 10 | `remotion_chart_story` | 图表叙事 | `dashboard_brief` | `chart_story` | minimal / grid / countup_number | 同上 | 逐步激活柱状图 | glass_dashboard | medium | 截断 56 字 | variant 变体；与 #9 共享底座，差异有限 |
| 11 | `remotion_ranking_strip` | 排行条快报 | `dashboard_brief` | `ranking_strip` | minimal / grid / countup_number | 同上 | 大编号 + 横向强弱条 | glass_dashboard | medium | 截断 56 字 | variant 变体；与 #9 共享底座，差异有限 |
| 12 | `remotion_caption_story` | 大字旁白叙事 | `caption_story` | — | cinematic / clean / none | `CaptionStoryLayout` | 大字标题 + 旁白 | warm_cinematic | low | 截断 56 字 | 范式差异化做得较好 |
| 13 | `remotion_caption_intro` | 电影感开场字幕 | `caption_story` | `caption_intro` | cinematic / clean / none | 同上 | 居中大标题开场 | warm_cinematic | low | 截断 56 字 | variant 变体；与 #12 仅开场形式不同 |
| 14 | `remotion_cta_overlay` | 行动号召叠层 | `caption_story` | `cta_overlay` | cinematic / clean / none | 同上 | 大字 + 底部 CTA 条 | warm_cinematic | medium | 截断 56 字 | variant 变体；与 #12 仅结尾 CTA 不同 |

> 入口组件位于 `remotion/src/AiNewsVideo.tsx`，由 `Root.tsx` 中 `Composition id="AiNewsVideo"` 注册。
> 调度逻辑：`AiNewsVideo` → `remotionFamily === "card_stack"` 走 `CardStackLayout`；`=== "timeline_news"` 走 `TimelineNewsLayout`；`=== "dashboard_brief"` 走 `DashboardBriefLayout`；`=== "caption_story"` 走 `CaptionStoryLayout`；默认走内嵌的 DataNewsLayout。

---

## 3. 视觉差异审计维度

### 3.1 五范式对比

| 范式 | 代表样式 | 版式结构 | 背景 | 动效 | 信息密度 | 风格辨识度 | 背景丰富度 | 可读性 | 优先级 |
|------|----------|----------|------|------|----------|------------|------------|--------|--------|
| `data_news` | #1 #2 #3 #4 #5 | 大标题型 | CSS 网格 / 极光 | fade / slide_fade / slide | 中 | 3/5 | 2/5 | 4/5 | P0（5 个样式彼此差异小） |
| `card_stack` | #6 | 卡片堆叠 | aurora_blue | 上滑 / 缩放 | 中 | 4/5 | 3/5 | 4/5 | P2（已差异化） |
| `timeline_news` | #7 #8 | 时间线 / 路线图 | tech_grid_dark | 节点高亮 | 中 | 4/5 | 2/5 | 4/5 | P1（route_map 变体差异有限） |
| `dashboard_brief` | #9 #10 #11 | 指标看板 | glass_dashboard | countup_number | 高 | 4/5 | 3/5 | 4/5 | P1（chart/ranking 变体差异有限） |
| `caption_story` | #12 #13 #14 | 大字标题 | warm_cinematic | 缓动 | 低 | 4/5 | 2/5 | 3/5 | P1（caption_intro/cta_overlay 变体差异有限） |

### 3.2 关键尺寸参数

来自 `remotion/src/AiNewsVideo.tsx` 第 120-174 行的 `LAYOUT_CONFIGS`：

| 模式 | 适用比例 | cardTitle | cardDesc | cardMinHeight | descMaxChars |
|------|----------|-----------|----------|---------------|--------------|
| `vertical_compact` | 9:16（默认） | 38 | 26 | 620 | **56** |
| `horizontal_balanced` | 16:9 | 32 | 22 | 480 | **72** |
| `square_compact` | 1:1 / 4:5 | 30 | 21 | 520 | **52** |

> 由 `app/video_lab/renderers/remotion/props_builder.py` 第 175-186 行从 `outputAspectRatio` 推导，未显式传时 9:16 → `vertical_compact`。

---

## 4. 相似模板分组

### Group A：大标题 + 居中卡片（data_news 5 样式）

包含：

- `remotion_metric_motion`（动态数据栏目）
- `remotion_cinematic`（电影感快讯）
- `remotion_minimal_clean`（极简动效）
- `remotion_high_energy`（高能快剪）
- `remotion_neon_grid`（霓虹网格）

**相似原因**：

- 入口都是 `AiNewsVideo` 内嵌的 DataNewsLayout（`remotion/src/AiNewsVideo.tsx` 第 900-1280 行）
- 都是"封面 → 单卡大标题 + 描述 + 数据图 → 摘要"流水
- 背景都在 4 个 CSS preset 里选（实际只用 `tech_grid_dark` / `warm_cinematic` 两个）
- 文字策略完全一致：标题 + body 截断到 56 字
- 主要差异仅在配色（accent / highlight）、动效强度（low/medium/high）和 metricAnimation（bar / number / none）

**问题**：

- 5 个样式看起来像同一套模板换皮，**Style Sweep 并排对比时差异辨识度低**
- 极简动效 / 电影感快讯 / 动态数据栏目三种"气质"应该走完全不同的版式，目前只是配色和动效强度不同

**建议**：

- 保留 `remotion_metric_motion` 作为 data_news 基础款
- `remotion_cinematic` → 改为真正的电影感宽幅版式（参考 16:9 上下分屏）
- `remotion_minimal_clean` → 改为全留白 + 居中标题 + 底部 caption（参考 caption_story 但更克制）
- `remotion_high_energy` → 改为快剪/多卡叠层（接近 card_stack 但节奏更快）
- `remotion_neon_grid` → 改为数据网格 + 数字矩阵

### Group B：指标看板（dashboard_brief 3 样式）

包含：

- `remotion_dashboard_brief`（指标看板快报）
- `remotion_chart_story`（图表叙事，variant=chart_story）
- `remotion_ranking_strip`（排行条快报，variant=ranking_strip）

**相似原因**：

- 入口都是 `DashboardBriefLayout`，共享 glass_dashboard 背景
- 字体、字号、动效强度（medium）、transitionStyle（fade）都一致
- chart_story 和 ranking_strip 仅在 variant 字段做了分支（`remotion/src/AiNewsVideo.tsx` 第 1834-1980 行）

**问题**：

- 三个样式视觉上都很"dashboard"，区分度集中在"用条形还是柱状图还是编号"上
- 字体、配色、动效都相近，并排时容易混淆

**建议**：

- 保留 `remotion_dashboard_brief` 作为基础款
- `remotion_chart_story` → 强化 chart 表达（横轴、对比柱、当前柱高亮）
- `remotion_ranking_strip` → 强化 ranking 表达（大编号 + 强势条 + 排行徽章）

### Group C：时间线（timeline_news 2 样式）

包含：

- `remotion_timeline_news`（时间线快讯）
- `remotion_timeline_route_map`（路线图时间线，variant=route_map）

**相似原因**：

- 入口都是 `TimelineNewsLayout`，共享 tech_grid_dark 背景
- variant=route_map 在 1506 行附近分支，但节点排布仅是横向/纵向切换

**问题**：

- 两个样式共享底座，route_map 区分度有限
- route_map 适合"路线、路径、阶段"语义，目前更像是 timeline_news 的微调

**建议**：

- 把 `remotion_timeline_route_map` 强化为"路线 + 阶段徽章 + 进度推进条"
- 拆分为新 layout 而非 variant

### Group D：大字旁白（caption_story 3 样式）

包含：

- `remotion_caption_story`（大字旁白叙事）
- `remotion_caption_intro`（电影感开场字幕，variant=caption_intro）
- `remotion_cta_overlay`（行动号召叠层，variant=cta_overlay）

**相似原因**：

- 入口都是 `CaptionStoryLayout`，共享 warm_cinematic 背景
- variant 切换开场形式（居中大字）和结尾 CTA

**问题**：

- 三个样式在中间段落（keypoint 卡片）几乎一致，差异集中在首尾
- warm_cinematic 背景在 caption 范式下已经够用，但缺少情绪化背景层

**建议**：

- 保留 `remotion_caption_story` 作为基础款
- `remotion_caption_intro` → 强化开场大字幕动画
- `remotion_cta_overlay` → 强化结尾 CTA 动效

### Group E：孤本（card_stack 1 样式）

包含：

- `remotion_card_stack`（卡片叠层）

**评价**：

- 14 个样式中唯一一个真正范式差异化的样式
- aurora_blue 背景 + 卡片堆叠，辨识度好
- 但孤本会让 Style Sweep 对比时出现"1 个特立独行 + 13 个相对相似"的不平衡

**建议**：

- 保持现状，作为差异化参考标杆
- 在 3B-2 中可作为 backgroundPreset 切换的样板

---

## 5. 重点问题清单

### P0-1：data_news 5 样式版式同质化

- **现象**：5 个样式走同一个 DataNewsLayout，仅靠 accent / highlight / motionIntensity / metricAnimation 区分
- **代码位置**：`remotion/src/AiNewsVideo.tsx` 内的 DataNewsLayout（第 900-1280 行）
- **影响**：Style Sweep 并排对比时，用户难以看出"动态数据栏目"与"电影感快讯"的本质差异
- **优先级**：**P0**（最严重）

### P0-2：文本硬截断（descMaxChars）

- **现象**：所有 keypoint 卡片的 body 文本被 `truncateText()` 截断到 56 字（vertical_compact 默认）
- **代码位置**：
  - `remotion/src/AiNewsVideo.tsx:188-194` `truncateText()` 函数
  - `remotion/src/AiNewsVideo.tsx:130-144` `LAYOUT_CONFIGS.vertical_compact.descMaxChars = 56`
  - `remotion/src/AiNewsVideo.tsx:732` 概览页 keypoint 列表调用 `truncateText(kp.body, layout.descMaxChars)`
  - `remotion/src/AiNewsVideo.tsx:968` data_news 卡片 body 调用 `truncateText(kp.body, layout.descMaxChars)`
  - `remotion/src/AiNewsVideo.tsx:1284` 第二处 data_news 卡片 body 截断
  - `remotion/src/AiNewsVideo.tsx:2328 / 2348` 封面摘要与封面预览列表截断
- **影响**：长正文被砍到 56 字（不到 30 个汉字），关键信息可能丢失；Style Sweep 排查报告里常被用户反馈"看不到完整句子"
- **优先级**：**P0**（直接影响信息完整性）

### P0-3：卡片高度固定（cardMinHeight 480~620）

- **现象**：每张 keypoint 卡片最小高度固定为 480~620 px（vertical_compact = 620）
- **代码位置**：`remotion/src/AiNewsVideo.tsx:141 / 155 / 169` 三个 LAYOUT_CONFIGS 的 `cardMinHeight`
- **影响**：短正文时卡片有大段空白；长正文时（即便不截断）会撑高破坏节奏
- **优先级**：**P1**（影响节奏，但被 P0-2 截断掩盖）

### P1-1：背景丰富度偏弱

- **现象**：4 个 CSS preset 都是 radial-gradient + 网格 + 模糊，没有任何粒子、视频、Ken Burns、AI 背景
- **代码位置**：`remotion/src/AiNewsVideo.tsx:199-360` BackgroundLayer 4 个分支
- **影响**：remotion_metric_motion / remotion_high_energy 等强动效样式，背景仍是静态 CSS，看几遍就能看出"模板感"
- **优先级**：**P1**（影响辨识度，但不如文本严重）

### P1-2：动效节奏相似

- **现象**：除 high_energy / minimal_clean 外，多数样式都是 fade / slide_fade 节奏
- **代码位置**：`remotion/src/AiNewsVideo.tsx` 的 motionIntensity 与 transitionStyle 应用
- **影响**：连续看多个 data_news 样式会感觉"在循环同一支片"
- **优先级**：**P1**

### P1-3：familyVariant 区分度有限

- **现象**：chart_story / ranking_strip / route_map / caption_intro / cta_overlay 都在共享底座上做小变体
- **代码位置**：`remotion/src/AiNewsVideo.tsx:1834 / 1866 / 1506` 等 familyVariant 分支
- **影响**：5 个 variant 样式在 Style Sweep 对比中区分度不高
- **优先级**：**P1**

### P2-1：9:16 竖屏空间利用不均

- **现象**：垂直画面大量上下留白（封面与摘要之间、卡片上方），中部信息密度高
- **代码位置**：`vertical_compact` 模式下 cardMinHeight = 620、cardPadding = 40
- **影响**：9:16 短视频本来信息量有限，过多留白让节奏拖沓
- **优先级**：**P2**

### P2-2：info-debug 数据未在成片展示

- **现象**：Remotion `reportOverview` / `sourceRefs` 字段由 `props_builder.py` 透传，但成片中无可见展示
- **代码位置**：`app/video_lab/renderers/remotion/props_builder.py:222-225` 写入；`remotion/src/AiNewsVideo.tsx` 中无对应渲染分支
- **影响**：信息密度无法进一步提升
- **优先级**：**P2**

---

## 6. 优先优化模板建议（3~5 个）

| 优先级 | styleId / styleName | 当前问题 | 改造方向 | 预期视觉差异 |
|-------|---------------------|----------|----------|--------------|
| **P0** | 全范式统一修复 | `descMaxChars` 硬截断 | 改为动态字号 + 最多行数（如 4 行）+ 自动 ellipsis；不再使用 `truncateText` 字符截断 | 长正文可读完；不再被砍到 30 汉字 |
| **P0** | `remotion_high_energy` 高能快剪 | 与 metric_motion 几乎同版 | 改为多卡快速叠层（接近 card_stack 但切卡更快）+ 数字闪烁 | 与 data_news 范式形成明显对比 |
| **P1** | `remotion_cinematic` 电影感快讯 | 配色和动效差异小 | 改为 16:9 上下分屏版（horizontal_balanced）+ 顶部 cinematic 字幕条 | 版式与 9:16 data_news 完全不同 |
| **P1** | `remotion_chart_story` 图表叙事 | 与 dashboard_brief 共享底座 | 拆分为独立 layout，强化横轴、对比柱、当前柱高亮 | 与 ranking_strip / dashboard_brief 形成明显差异 |
| **P2** | `remotion_timeline_route_map` 路线图时间线 | 与 timeline_news 仅方向不同 | 强化为"路线 + 阶段徽章 + 进度推进条" | 与 timeline_news 形成明显差异 |

> **注**：上表"优先级"是相对当前差异化收益排序；第一步建议先做 P0 全范式文本截断修复，再做 P0 / P1 模板改造。

---

## 7. 下一阶段改造建议

### 推荐：3B-2A — 修复 Remotion 报告卡片文本硬截断问题

**原因**：

- 文本截断直接破坏信息完整性，比背景美化更基础
- 涉及 5 个调用点（`remotion/src/AiNewsVideo.tsx:732 / 968 / 1284 / 2328 / 2348`），改造面可控
- 改造后能直接服务后续 3B-2B / 3B-2C 模板差异化（先让文字撑得下，再谈版式）
- 不动 family / 范式层，回归风险小

**预期工作**：

- 移除 `truncateText()` 字符级截断，改为 `line-clamp` + 动态字号
- 在 `LAYOUT_CONFIGS` 中新增 `maxBodyLines` 字段（如 4 行）
- 同步调整 `cardMinHeight`，由"固定"改为"min(max-content, minHeight)"
- 封面预览列表（keypoint preview）保留 56 字截断，因为封面空间有限

### 备选拆分（如果 3B-2A 之后再分阶段）

| 子阶段 | 名称 | 范围 |
|--------|------|------|
| 3B-2A | 修复文本硬截断与信息呈现 | `truncateText` → 动态字号 + 行数限制；cardMinHeight 调整 |
| 3B-2B | 挑 3 个模板做背景差异化 | `metric_motion` / `high_energy` / `neon_grid` 各自换 backgroundPreset + 背景层 |
| 3B-2C | 挑 2 个模板做动效节奏差异化 | `high_energy`（快剪）/ `caption_story`（缓动） |
| 3B-2D | Style Sweep 重新生成样片并人工验收 | 对每个新模板在 `/video-lab/style-sweep` 跑一遍，逐个播放标记问题 |

> 如果继续模板差异化，下一步先做 3B-2A 文本截断修复，**不直接做版式改造**。

---

## 8. 当前阶段不包含

1. 不修改 Remotion 组件代码（`remotion/src/AiNewsVideo.tsx` / `Root.tsx` / `data.ts`）
2. 不修改前端页面（`frontend/src/video-lab/**`）
3. 不修改后端接口（`app/video_lab/router.py` / `app/video_lab/renderers/**`）
4. 不修改 Style Sweep 参数逻辑
5. 不修改 Style Gallery
6. 不修改字幕逻辑
7. 不修改 TTS
8. 不修改 FFmpeg
9. 不生成新视频
10. 不删除 runtime 文件
11. 不做真实资产 cleanup

---

## 9. 审计执行记录

| 项 | 命令 / 路径 | 结果 |
|----|-------------|------|
| 模板清单来源 | `app/video_lab/style_gallery/presets.py` | 14 条 `template_programmatic_render` 样式 |
| 范式定义 | `remotion/src/data.ts:83-88` `RemotionFamily` | 5 范式（data_news / card_stack / timeline_news / dashboard_brief / caption_story） |
| 范式分发 | `remotion/src/AiNewsVideo.tsx:2488-2530` 4 个三元链 | remotionFamily → Layout 分发 |
| 截断函数 | `remotion/src/AiNewsVideo.tsx:188-194` `truncateText` | 字符级 slice + ellipsis |
| 截断配置 | `remotion/src/AiNewsVideo.tsx:120-174` `LAYOUT_CONFIGS` | descMaxChars = 52 / 56 / 72 |
| 截断调用点 | `remotion/src/AiNewsVideo.tsx` | 5 处（732 / 968 / 1284 / 2328 / 2348） |
| 参数透传 | `app/video_lab/renderers/remotion/props_builder.py:159-200` | remotionFamily / familyVariant / backgroundPreset / aspectRatioLayoutMode |

---

## 10. 相关文档

- [V1.2.3 Style Sweep 验证中心基础闭环冻结记录](V1_2_3_STYLE_SWEEP_VALIDATION_BASELINE.md)
- [V1.2.3 Style Sweep 到 Style Gallery 样片库沉淀闭环冻结记录](V1_2_3_STYLE_SWEEP_TO_GALLERY_BASELINE.md)
- [V1.2.3 Style Sweep 历史记录与运行资产治理基线](V1_2_3_STYLE_SWEEP_HISTORY_AND_ASSET_GOVERNANCE_BASELINE.md)
