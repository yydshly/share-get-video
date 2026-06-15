# Video Lab Open Issues

> V0.7.4 起统一在此文件登记 Video Lab 当前阶段已知问题。
> 历史问题（V0.6.5 前的）已并入下方分类；本文件不再做时间线追溯。
> 关联前端入口：[/video-lab 首页底部"已知问题"区](../frontend/src/video-lab/pages/VideoLabHome.tsx)

---

## 当前策略

先打通 UI 主流程，再逐项修复质量和细节问题。

| 阶段 | 目标 | 状态 |
| --- | --- | --- |
| 阶段 1 | UI 主流程打通（Workbench → 保存样片 → Style Gallery） | ✅ V0.7.2 + V0.7.3 已完成 |
| 阶段 2 | 首页改造成「流程总控台」入口分组 | ✅ V0.7.4 |
| 阶段 3 | 按下方问题清单逐项排查与修复 | ⏳ 待启动 |

主线流程（V0.7.4 起为「主路径」）：

```text
Workbench 生成完整视频
  → 人工观察确认
  → 保存为样片
  → 加入对比
  → Style Gallery 查看与比较
```

所有 5 步当前状态：**已通**。

---

## 已知问题

### P0 · 成片质量问题

- **Remotion 样式差异偏小**：当前更像 theme variation（换色/换字体），不是真正的不同 Composition。
- **Remotion 成片可能缺图片 / 缺素材**：偶发整段画面缺图。
- **部分视频存在音画不对应**：TTS 时长与画面节拍错位。
- **部分视频字幕节奏和画面不一致**：字幕条 / 关键点切换不同步。
- **结构评分不能代表人工观看质量**：video_quality 给出 5.0/5.0/4.87 时人工感觉差距明显大于分数差。
- **Workbench Pillow preview 文本溢出 / 重叠（V0.7.6 手工验收发现）**：长内容或多要点时，本地图像帧合成 preview 可能出现文字拥挤、重叠、可读性差。
- **Remotion timeline 对齐问题（V0.8.1 已修复前端模板时间轴计算）**：V0.8.0 人工标注发现 6 个 Remotion 样式普遍存在画面 / 音频 / 字幕 / 结尾总结页不同步。根因为 Remotion 模板在已接收 `voiceover segment duration` 后，又用 `motionIntensity` 缩放 scene duration，并通过 `transitionOverlap` 让 scene start 提前（`acc += f - transitionOverlap`），导致视觉时间轴短于或偏离音频时间轴。V0.8.1 已禁止 `useAligned` 模式下再用 motionIntensity 缩放 scene duration，并改为按真实 `segmentDurations` 累计 scene start；transitionOverlap 在该模式下被夹到 ≤ 6 帧且不再加在 Summary 上。**仍需用户重新跑 Style Sweep 验证**。
- **targetDuration 未约束旁白长度（V0.8.3 已加入预算控制）**：V0.8.2 复测发现 `targetDuration=45` 时，Remotion 各样式实际 `audioDurationSec` 为 52-58 秒，说明 `plan_shots` 未按目标时长控制 opening / narration / closing。V0.8.3 已：`plan_shots` 接收 `target_duration_sec` 参数；LLM prompt 显式给出 opening/narration/closing 字数预算（≤45s 短视频默认 18/45/16）；`_normalize_plan` 对 narration ≤48 字、opening ≤22 字、closing ≤18 字做硬截断；`coverTitle` 在等于第一条要点标题时降级为 `AI前沿趋势速览`；`manifest.planDebug` 新增 `budgetDebug`（含 `actualAudioDurationSec` / `overBudget`）；Style Sweep Markdown 报告增加 `failedReason` / `logsTail` 和「样式参数说明」（`showDataViz` / `metricAnimation` 含义）。**仍需下一轮 Style Sweep 验证实际 audioDurationSec 是否接近目标时长**。
- **Style Sweep 人工标注统计可能失真（V0.8.4 已增强）**：用户可能在备注中描述字幕截断、音画不同步、黑屏、生成失败等问题，但未勾选人工问题标签，导致统计结果显示各类问题为 0。V0.8.4 增加：备注关键词推断的 `suggestedIssues`（`inferIssueHintsFromNote`，覆盖"失败/黑屏/音画/字幕截断/文字溢出"等关键词）；新增「生成失败」标签（`render_failed`）；卡片级标注提醒（`有备注但未勾标签` / `失败但未标生成失败` 时显式提示）；顶部「标注完整性检查」面板（3 个数：有备注但未勾标签、失败但未标生成失败、有建议标签待确认）；Markdown 报告增加「## 标注完整性检查」小节 + 每个样式小节增加 `suggestedIssues` / `markingWarning` 字段；单个排查 JSON 同步增加 `suggestedIssues` / `markingWarning`。**本轮不做后端持久化**，刷新页面后丢失。

### P1 · UI / 产品流程问题

- **首页入口过多**：V0.7.4 前 16 张卡片无差别堆叠。V0.7.4 已分组（主线 / 验证 / 历史），但旧页面未清理。
- **部分历史页面仍可访问但定位不清**：V0.7.4 已降级为「历史 / 待清理」分组。
- **Advisor / 总结建议可能不是完全基于真实数据**：当前仍以硬编码 + 弱数据驱动为主，结论谨慎采纳。
- **Style Sweep 人工问题标注能力（V0.8.0）**：已在 `/video-lab/style-sweep` 接入人工问题标签 + 备注 + 排查信息折叠区 + Markdown 报告导出。**当前仅前端临时标注，刷新页面后丢失**；后续可考虑持久化到样片库或单独质量审计记录（不在 V0.8.0 范围）。
- **Remotion 诊断信息不足（V0.8.2 已增强）**：manifest 写入 planDebug（`planSource` / `coverTitle` / `opening` / `closing` / `shotCount` / `shots[]` / `voiceoverSegments[]`），`remotion_props.json` 写入 contentDebug（`title` / `subtitle` / `keyPointTitles` / `keyPointBodies` / `metricsByKeyPoint` / `hasMetrics` / `style` / `remotionFamily`）+ timelineDebug（保留 V0.8.1），Style Sweep 排查 JSON 和 Markdown 报告增加 `manifestUrl` / `steps` / `warnings` / `params` / `audioDurationSec` / `subtitleCount` / `logsTail`（仅末 30 行）。**仍需结合下一轮 Style Sweep 产物验证具体问题**。本轮**不直接修生成质量**。
- **首页不再宣传「8 类技术路线」**：V0.7.4 起不再展示，改为只列当前主线 / 验证 / 历史。
- **V0.7.5 巡检发现：5 个对比页冗余**（route-benchmark / route-playground / route-baseline-comparison / compare / visual-compose）：多数被技术探测台覆盖；后续应收敛为 1 条主线。详见 [docs/UI_ENTRY_AUDIT.md](UI_ENTRY_AUDIT.md) §7 P1。
- **VideoMethodsPage 能力边界表达已澄清（V0.8.5）**：V0.7.5 巡检发现 `/video-lab/methods` 文案提到「6 类视频生成方案」，实际渲染器只接入了 3 类（Pillow / Remotion / AI 素材），但文案给用户"6 类都完整可用"的错觉。V0.8.5 已：① 标题改为「视频生成路线库」+「6 类视频生成路线参考（不表示都已在主流程中可调用）」；② 顶部红字提示"并非所有路线都已接入当前主流程"；③ 新增主流程入口卡片（Workbench / Style Sweep / Style Gallery）+ 「返回 Video Lab 总控台」次级按钮；④ 顶部增加 `available / mock / reserved / not_configured` 状态说明面板，并明确"当前主流程渲染器只接入了 Pillow 与 Remotion 两条"；⑤ 每张方法卡顶部增加蓝色「当前定位」条（按 id 路由），例如 "主流程重点验证：对应 Remotion 动态模板路线" / "部分验证：AI 素材路线仍非 Workbench 默认可用" / "后续预留"。**状态 badge 未被改动**：seedData 中全部方法仍是 `mock` 或 `reserved`，本轮**不强行改为 available**。
- **结果对比页 localStorage 数据来源已澄清（V0.8.6）**：`/video-lab/compare` 当前定位为"本地结果对比页"，数据来源为当前浏览器 `localStorage["vl_experiments"]`，不是后端真实实验库，也不代表 Workbench / Style Sweep / Style Gallery 的全部最新结果。页面已增加数据来源提示、本地实验数、清空本地对比数据按钮、主流程快捷入口和空状态说明。后续如需全局真实对比，应另做后端实验库 / 样片库对比能力。
- **V0.7.6 手工验收发现：Style Gallery 样片卡片展示弱**：Workbench 样片虽然可见，但视频预览小、缺少放大预览 / 查看详情入口，用户难以判断样片效果。V0.7.7 已加"查看效果"提示 + 原生全屏按钮，不做 modal 大重构。
- **Style Gallery 样片预览缺失（V0.8.7 已增强）**：用户在 `/video-lab/style-gallery` 看到样片记录「稳定数据卡」已保存并显示时长 / 音频时长，但卡片预览区显示「暂无预览」。说明样片元数据存在，但 `video_url / output.path / poster_url` 缺失或前端保存字段映射不完整。V0.8.7 已：① 为 `generateAndSaveSample` 增加 `final_video_url / cover_url` fallback（`output_path = data.output.path || data.final_video_url`、`poster_path = data.output.poster || data.cover_url`、`audio_url / srt_url / manifest_url` 同步增加回落）；② 生成接口"成功"但缺视频路径时直接 `throw`，不再静默保存无预览样片；③ 保存样片接口（`/style-samples` POST）增加 `resp.ok` 校验，失败时 throw 包含状态码与响应文本的错误；④ 样片卡片在缺少 video/poster 时显示"样片资产缺失"提示（含 id / route_id / style_name / manifest_url / audio_url / srt_url / duration_sec / audio_duration_sec），并新增"🩺 复制样片诊断 JSON"按钮便于反馈时直接粘出；⑤ 样片库 tab 顶部新增定位提示（黄色边框），明确"记录存在但预览路径缺失建议删除后重新生成"并引导 Style Sweep；⑥ 预置风格 tab 顶部新增蓝色提示 + "进入 Style Sweep"按钮，区分"单独生成样片"与"系统比较 Remotion"。**仍需用户重新生成样片验证新记录是否可预览**。
- **V0.7.6 手工验收发现：历史 / 参考 / 待清理入口位置不够直观**：用户需要下滚才能看到，首页"🗄️ 历史 / 参考 / 待清理（不参与主流程）"标题之上 V0.7.7 已增加一个次级按钮 / 锚点，引导用户快速跳到该区。
- **V0.7.6 手工验收发现：Advice 页面当前只是文字建议页**：不能当作真实数据驱动推荐系统，V0.7.7 已在页面顶部加定位 banner 明确"当前为历史建议页 / 文字规则页，尚未接入完整真实实验数据"，并提供返回主流程的按钮。

### P2 · 能力扩展问题

- **AI 素材路线尚未成为 Workbench 默认可用路线**：当前 V0.7.x 中 AI 素材路线在 Workbench 标记为 `preview_only`。
- **Remotion 表现范式探索不足（V0.8.8 已增强研究页 / V0.8.9 已实现 Timeline News 最小模板）**：当前 Remotion 样式多数仍停留在同一信息卡模板上的颜色、动效强度、转场差异，缺少真正的 Composition Family 差异。V0.8.8 已增强 `/video-lab/remotion-style-family`：补充 Remotion 官方模板 / Showcase / Prompt Showcase 可抽象出的参考样例类型（如 News article headline highlight / TikTok word-by-word captions / Rocket Launches Timeline / Three.js Ranking / Bar + Line Chart / Cinematic Tech Intro / Travel Route Map / Transparent CTA overlay 等），扩展 Data News / Card Stack / Timeline / Dashboard / Subtitle Story 的 `referenceExamples` / `implementationPattern` / `requiredComponents` / `styleSweepMapping` / `nextExperiment` 五个字段，并新增「参考样例 → 可落地范式」「当前实现覆盖度」「下一步最小实验推荐」三个区块；页面顶部增加 Style Sweep / Style Gallery / Video Lab 入口，标题改为"Remotion 表现范式研究台 · V0.8.8"。**V0.8.9 已新增 `remotion_timeline_news` 最小模板，并接入 Style Sweep**：`RemotionFamily` 类型扩展 `timeline_news`；`AiNewsVideo` 新增 `TimelineNewsLayout`（竖向时间线 + 节点高亮 + 进度线，包装在 `Sequence from=coverFrames` 内复用 `cardStarts/cardFramesArr`），主分支由二分变三分支 `card_stack | timeline_news | data_news`；`presets.py` 新增 `remotion_timeline_news`（Remotion 动态模板路线第 7 个 style）；StyleSweepPage 的 `template_programmatic_render.styleCount` 由 6 改为 7；研究页 Timeline 状态从"待探索"更新为"V0.8.9 已有最小实现"，覆盖度面板把 Timeline News 移入"已实现基础"，下一步推荐改为进入 Style Sweep 实测的 4 条观察清单。`Dashboard` / `Subtitle Story` / `Map Journey` / `Code Walkthrough` / `Audio Wave` 仍未实现。本轮**不引入 Three.js / D3 / 外部图片**，复用现有 HighlightedText / CountUpNumber / findPrimaryStat 工具。
- **结构评分需要多帧 / 偏好对比增强**：见 `app/video_lab/quality/visual_judge.py` 已知限制。

---

## 当前不处理

本阶段**不直接处理**：

- 不修 Remotion 模板（避免引入新变量）
- 不重做 Advisor
- 不清理全部历史页面（V0.7.4 仅做分组降级）
- 不做问题标注系统的后端持久化（V0.8.0 已接入前端临时标注；后端保存另起）
- 不新增后端接口
- 不接入新的 AI 素材路线到 Workbench 默认

---

## 与首页的对应关系

首页（`/video-lab`）的"已知问题"区当前只展示 P0/P1 关键项的精简版，全量以本文件为准。
任何"暂时不修但需要让用户知道"的问题都应该登记在本文件，并由首页聚合显示。

V0.7.5 起，UI 入口层面的可访问性 / 状态一致性巡检单独维护在 [docs/UI_ENTRY_AUDIT.md](UI_ENTRY_AUDIT.md)。两份文档配合使用：
- 本文件 = 质量问题 / 产品流程问题的统一登记；
- UI_ENTRY_AUDIT.md = 入口可达性、首页状态文案与实际行为是否一致。
