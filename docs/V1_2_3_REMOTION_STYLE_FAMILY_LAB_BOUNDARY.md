# V1.2.3 Remotion Style Family Lab 边界与现状核查

> 本文档冻结「remotion-style-family」作为旁路实验区的**当前状态与边界**，**不做任何功能开发**。
> 范围：核查仓库中是否已有相关实现；明确与主链路（Style Sweep / Style Gallery）的关系；定义实验目标与候选接入门槛。

---

## 1. 阶段结论

1. remotion-style-family 实验区**已经存在**（V0.6.1 起），不是规划阶段
2. 当前包含 5 个 family（Data News / Card Stack / Timeline / Dashboard / Subtitle Story），已有 UI 预览和对比能力
3. 渲染走 `template_programmatic_render` 路线 + `render_clip_preview`，**不写 Style Gallery / runtime 历史 / job 记录**
4. 接下来定位为"旁路实验区"，**不直接改造 14 个现有 Remotion style**；先做能力探索，成熟后再走 candidate 流程进入 Style Sweep
5. 与 V1.2.3 现有冻结链路（Style Sweep / Style Gallery / 资产治理）的边界已明确

---

## 2. 现状核查

### 2.1 已存在的实现

| # | 内容 | 路径 | 行数 | 状态 |
|---|------|------|------|------|
| 1 | 前端页面 | `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx` | 1436 | V0.8.8 已实现 |
| 2 | 前端路由 | `frontend/src/App.tsx:41` `/video-lab/remotion-style-family` | — | 已挂载 |
| 3 | 首页入口卡片 | `frontend/src/video-lab/pages/VideoLabHome.tsx:258-261` "🎞️ Remotion 表现范式" | — | 已挂载 |
| 4 | 后端接口 | `app/video_lab/router.py:384-388` `POST /video-lab/style-family/compare` | — | 已挂载 |
| 5 | 后端 service | `app/video_lab/services/style_family_service.py` `run_style_family_compare` | 82 | V0.6.4 起 |
| 6 | 入参 schema | `app/video_lab/schemas.py:182-192` `StyleFamilyCompareRequest` | — | content + params |
| 7 | 范式定义文档 | `docs/REMOTION_STYLE_FAMILY_V0.6.1.md` | 280 | V0.6.1 起 |
| 8 | 范式实现记录 | `docs/CARD_STACK_LAYER_VISIBILITY_FIX_V0.6.5.2.md` 等 | — | 5 个相关文档 |
| 9 | 测试 | `tests/test_style_gallery_presets.py`（grep 命中，但功能不一定为 lab） | — | 待核查 |

### 2.2 渲染路径

```text
frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx
  → POST /video-lab/style-family/compare
  → app/video_lab/router.py:style_family_compare
  → app/video_lab/services/style_family_service.py:run_style_family_compare
  → render_clip_preview(...)  内部走 template_programmatic_render + remotionFamily={data_news|card_stack|timeline_news|dashboard_brief|caption_story}
```

> 5 个 family 都通过 `params["remotionFamily"]` 注入到 `template_programmatic_render` 同一渲染器，与 V1.2.3 Style Sweep 的 `remotionFamily` 字段**共享同一组件入口**。
> 但 lab 走 `render_clip_preview`（短片片段，仅用于旁路预览），Style Sweep 走 `run_style_sweep_endpoint`（完整长片 + job 记录 + 历史），两者不互通数据。

### 2.3 5 个 family 范围

来自 `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx:59-266`：

| family id | 名称 | 当前状态（页面标注） | 已有 styleSweepMapping |
|-----------|------|---------------------|------------------------|
| `data_news` | Data News | 已有基础 — AiNewsVideo 当前形态 | remotion_metric_motion, remotion_minimal_clean, remotion_chart_story, remotion_ranking_strip |
| `card_stack` | Card Stack | V0.6.5.2 已支持 UI 预览对比 | remotion_card_stack |
| `timeline` | Timeline | V0.8.9 已有最小实现 (TimelineNewsLayout) | remotion_timeline_news, remotion_timeline_route_map |
| `dashboard` | Dashboard | 已有最小可生成预设 (remotion_dashboard_brief) | remotion_dashboard_brief, remotion_chart_story, remotion_ranking_strip |
| `subtitle_story` | Subtitle Story | 已有最小可生成预设 (remotion_caption_story) | remotion_caption_story, remotion_caption_intro, remotion_cta_overlay |

> 注：`card_stack` 实际对应 `remotionFamily === "card_stack"`；`timeline` 对应 `timeline_news`；`dashboard` 对应 `dashboard_brief`；`subtitle_story` 对应 `caption_story`。这 5 个 family 在 lab 与 Style Sweep 的 `remotionFamily` 命名上**已经对齐**。

### 2.4 lab 与主链路的关系

| 维度 | lab（`/video-lab/remotion-style-family`） | Style Sweep（`/video-lab/style-sweep`） | Style Gallery |
|------|------------------------------------------|------------------------------------------|---------------|
| 入参 | content + params | content + 14 选 1 的 styleId | 提升自 Style Sweep |
| 渲染路径 | `template_programmatic_render` + clip preview | `template_programmatic_render` + 完整长片 | 复用样片 URL |
| 是否写 job | ❌ 不写 | ✅ 写 `style_sweep/jobs/{job_id}.json` | ❌ 不写 |
| 是否写 runtime | ❌ 短片写到 `runtime/video_lab/...` 但无 job 引用 | ✅ 写 runtime + job | ❌ 不写 |
| 是否进样片库 | ❌ 不进 | ⚠️ 需手动 promote | — |
| 是否进资产清理 | ❌ 不被 referenced_assets 追踪 | ⚠️ 若 promote 则被追踪，否则孤立 | ✅ 全员被追踪 |
| 是否影响 14 style | ❌ 不影响 | — | — |

> 关键观察：lab 走的 `template_programmatic_render` 渲染器**与 Style Sweep 共享**。这意味着 lab 的渲染产物也会落到 `runtime/video_lab/...`（短片文件），但**没有 job 记录**；其引用关系与 V1.2.3 资产治理 dry-run 的 `referenced_assets` **不互通**。

---

## 3. 实验区与主系统的边界

### 3.1 定位

```text
remotion-style-family 是旁路实验区，不是现有 Remotion 主链路。
```

### 3.2 现有主链路（**不**属于 lab 改造范围）

1. `/video-lab/style-sweep` 页面
2. Style Sweep job runner（`app/video_lab/style_sweep_jobs.py` 等）
3. `template_programmatic_render` 路线作为生产入口
4. `app/video_lab/style_gallery/presets.py` 中**现有 14 个 Remotion style**
5. Style Gallery 样片库（`/video-lab/style-gallery`）
6. 已冻结的 Remotion 主生成能力（V0.6.2 / V0.8.9 等）
7. 已冻结的 V1.2.3 三条基线（Style Sweep / Sweep→Gallery / 历史+资产治理）

### 3.3 lab 八条原则

| # | 原则 | 说明 |
|---|------|------|
| 1 | 不影响现有 Style Sweep | lab 渲染走短片 preview，不写 job；Style Sweep 行为不变 |
| 2 | 不影响现有 Style Gallery | lab 产物不写入样片库；不影响 promote 流程 |
| 3 | 不替换现有 14 个 Remotion style | lab 不修改 `presets.py`；不删 style，不重命名 |
| 4 | 不修改现有 Remotion 生产组件 | lab 改组件必须通过 candidate 门槛并合入主版本 |
| 5 | 不改变已有 render API 行为 | `POST /style-family/compare` 字段不变；旧调用方不破 |
| 6 | 不生成正式样片 | lab 产物仅供预览对比，不作为正式成片 |
| 7 | 不写入 Style Gallery | lab 无 promote 入口；不允许"先把 lab 提到样片库" |
| 8 | 不进入资产清理流程 | lab 产物不进入 `style_sweep_assets/scan` 治理范围（孤立无引用 = 正常） |

---

## 4. lab 探索的 5 类能力

> 与 [V1.2.3 Remotion 模板差异化与背景丰富度审计](V1_2_3_REMOTION_TEMPLATE_DIFFERENTIATION_AUDIT.md) 互补：审计是"现有 14 模板静态盘点"；lab 是"探索 Remotion 能力边界"。本阶段**不直接动现有模板**，而是用 lab 试错后再 candidate 化。

### 4.1 Layout Family（版式结构能力）

| 项 | 内容 |
|----|------|
| 探索目标 | 现有 5 family 之外的新版式结构（如双列、左右分屏、上下分屏、卡片墙、网格矩阵） |
| 最小 demo 形态 | 在 RemotionStyleFamilyPage 增加 1 个 prototype family 卡片，点击后生成 1 个 5~10s 短片 |
| 是否适合接入主系统 | ⚠️ 视效果而定；与 data_news/card_stack 等不冲突时可 candidate |
| 验收标准 | 9:16 布局稳定；与现有 5 family 视觉差异 > 60% |

### 4.2 Motion Family（动效节奏能力）

| 项 | 内容 |
|----|------|
| 探索目标 | 高能快剪 / 慢速叙事 / 节奏跟随旁白 / 镜头推拉 / 视差滚动 等 |
| 最小 demo 形态 | 1 个 prototype 短片 + 时长滑杆；用同一份 mock 内容对比 motionIntensity=low/medium/high |
| 是否适合接入主系统 | 适合；motionIntensity/transitionStyle 已有旋钮可复用 |
| 验收标准 | 动效不影响阅读；与 data_news 区别明显 |

### 4.3 Background Family（背景丰富度能力）

| 项 | 内容 |
|----|------|
| 探索目标 | 突破当前 4 个 CSS preset（tech_grid_dark / aurora_blue / glass_dashboard / warm_cinematic）的表达力上限：粒子、视频背景、Ken Burns、AI 背景层叠加 |
| 最小 demo 形态 | 1 个 prototype family + 1~2 个新 CSS preset；用同一份 mock 内容对比 |
| 是否适合接入主系统 | 适合；可作为新 backgroundPreset 候选 |
| 验收标准 | 不破坏 9:16 比例；与现有 4 preset 视觉差异 > 50% |

### 4.4 Text Policy（长文本展示与不丢信息能力）

| 项 | 内容 |
|----|------|
| 探索目标 | 修复 [V1.2.3 审计](V1_2_3_REMOTION_TEMPLATE_DIFFERENTIATION_AUDIT.md) 识别的 P0-2 文本硬截断问题：line-clamp + 动态字号 + 多行排版 |
| 最小 demo 形态 | 1 个 prototype family，喂同一段 80~120 字长正文 + 同一段 30 字短正文，验证长短都可读 |
| 是否适合接入主系统 | **强烈适合**（审计已 P0 标记） |
| 验收标准 | 80~120 字长正文可读完整；30 字短正文不撑出卡片；不破坏节奏 |

### 4.5 Data / Chart（数据与图表表达能力）

| 项 | 内容 |
|----|------|
| 探索目标 | 超越 dashboard_brief 的现有 3 变体：横轴 + 折线 + 当前点高亮；饼图 / 堆叠柱 / 排行榜 / 矩阵热力 等 |
| 最小 demo 形态 | 1 个 prototype family，喂 KPI / benchmark / Top list 三类 mock 数据 |
| 是否适合接入主系统 | 适合；可作为 dashboard_brief 的新 familyVariant |
| 验收标准 | 数据驱动清晰；与 chart_story / ranking_strip 不重复 |

---

## 5. 首批 3 个最小 family demo 建议

> 本阶段**不实现**；仅在文档中建议。
> 目标：把 4.1~4.5 收敛为 3 个"可立刻开干"的 demo，每个对应 1 类能力。

### 5.1 Demo A：Timeline News（时间线快讯）

| 项 | 内容 |
|----|------|
| 适合内容 | 政策演进、产品发布步骤、技术路线变化、论文方法流程 |
| 与现有模板区别 | 现有 14 style 中 timeline_news 已有基础，但 lab 中可探索"事件节点 + 因果箭头 + 进度推进条"等更丰富表达 |
| mock data | `{ events: [{date, title, desc, tone}], title, subtitle }` |
| Remotion 能力 | TimelineNode / ProgressLine / EventCard；vertical 与 horizontal 切换 |
| 预览方式 | RemotionStyleFamilyPage 增加 1 个 "Demo A" 卡片，点击后跑 5s 短片 |
| 接入主系统 | 通过 candidate 流程后作为新 remotion style 入 `presets.py`（不动现有 timeline_news） |

### 5.2 Demo B：Data Panel（动态数据面板）

| 项 | 内容 |
|----|------|
| 适合内容 | Benchmark 矩阵、模型对比、多公司指标对比、Top list |
| 与现有模板区别 | 现有 dashboard_brief 已有 3 变体；lab 中可探索"横轴 + 折线 + 当前点高亮" |
| mock data | `{ metrics: [{label, value, unit, min, max}], title }` |
| Remotion 能力 | LineChart / HeatmapMatrix / SparkLine；当前点高亮；进入/退出动画 |
| 预览方式 | RemotionStyleFamilyPage 增加 1 个 "Demo B" 卡片 |
| 接入主系统 | 通过 candidate 流程后作为 remotion_dashboard_brief 的新 familyVariant |

### 5.3 Demo C：Big Caption Narrative（大字旁白叙事）

| 项 | 内容 |
|----|------|
| 适合内容 | 观点短片、口播内容、情绪化解释、深夜独白 |
| 与现有模板区别 | 现有 caption_story 已有 3 变体；lab 中可探索"长文本不截断 + word-by-word 高亮 + 背景情绪化" |
| mock data | `{ sentences: [{text, emphasisTerms, tone}], title }` |
| Remotion 能力 | WordCaption / SentenceCard / AmbientBackground；line-clamp + 动态字号（修复审计 P0-2） |
| 预览方式 | RemotionStyleFamilyPage 增加 1 个 "Demo C" 卡片 |
| 接入主系统 | 通过 candidate 流程后作为 remotion_caption_story 的新 familyVariant |

> 3 个 demo 都从 lab 起步，**不直接合入 presets.py**。验收通过后再走 candidate 流程。

---

## 6. 接入主系统的门槛

### 6.1 总原则

```text
remotion-style-family 的实验 demo 不能直接进入 Style Sweep。
必须先通过 candidate 机制。
```

### 6.2 candidate 门槛（**8 条全部通过**）

| # | 门槛 | 含义 |
|---|------|------|
| 1 | 能在实验页面预览 | RemotionStyleFamilyPage 能稳定渲染该 demo |
| 2 | 能用固定 mock data 稳定渲染 | 同一 mock data 多次跑结果一致；不随机失败 |
| 3 | 9:16 布局稳定 | 文字不溢出、卡片不重叠、不会上下抖动 |
| 4 | 文本不硬截断、不丢关键句 | body 完整可读；不通过 truncateText 砍字 |
| 5 | 视觉结构和现有模板有明显区别 | 与现有 14 style 至少 1 项主维度（layout / motion / background）差异显著 |
| 6 | 动效不影响阅读 | 不会出现"看不清字""动效抢戏"等问题 |
| 7 | 能导出 mp4 或至少生成稳定 preview | render_clip_preview 返回 videoUrl 且 success=true |
| 8 | 人工验收认为值得进入 Style Sweep | 走 /video-lab/style-sweep 实际跑一次后人工打标 |

### 6.3 接入流程

```text
remotion-style-family prototype
  → candidate
  → 接入 Style Sweep Remotion style list （写入 app/video_lab/style_gallery/presets.py）
  → 生成样片
  → 人工标注
  → 提升到 Style Gallery
```

> 每一步都需要在对应文档（V1.2.3_*.md）记录；不可跳级。
> 不可"先写 presets.py 然后补 lab demo"，必须 lab → candidate → 写入。

---

## 7. 与 V1.2.3 审计文档的关系

| 文档 | 关系 |
|------|------|
| [V1.2_3_REMOTION_TEMPLATE_DIFFERENTIATION_AUDIT.md](V1_2_3_REMOTION_TEMPLATE_DIFFERENTIATION_AUDIT.md) | 是现有 14 个 Remotion style 的**静态盘点**。识别出 P0-2 文本硬截断、P0 data_news 5 样式同质化等问题。 |
| V1.2.3 审计 (302a758) | **作为参考输入**，不作为立即改造任务。 |
| V1.2.3 本文档 | 把"立即改造现有模板"延后；改走 lab 探索 → candidate → 接入主系统的迂回路径。 |
| V0.6.1 `docs/REMOTION_STYLE_FAMILY_V0.6.1.md` | lab 5 family 的**历史规划文档**。本边界文档是其**接续**——冻结 lab 当前能力与下一步边界。 |

> 换句话说：审计告诉我们"现有 14 模板有 8 个问题"；边界文档告诉我们"问题不在 lab 解决，由 lab 探索 candidate 方案，再用 candidate 替换现有 14 模板中最弱项"。

---

## 8. 当前阶段不包含

1. 不修改 Remotion 组件代码（`remotion/src/**`）
2. 不新增实验页面代码（`RemotionStyleFamilyPage.tsx`）
3. 不新增后端接口（`/style-family/compare`）
4. 不修改现有 14 个 Remotion style
5. 不修改 `app/video_lab/style_gallery/presets.py`
6. 不修改 Style Sweep
7. 不修改 Style Gallery
8. 不生成新视频（lab 不写正式样片）
9. 不写入 runtime（lab 短片已由 render_clip_preview 落盘，但不被任何 job 引用）
10. 不写入样片库
11. 不做真实资产 cleanup

---

## 9. 下一阶段建议

### 推荐：3B-2 — 在已有 remotion-style-family 页面中增加 3 个 mock family demo

**原因**：

- lab 页面（`/video-lab/remotion-style-family`）和后端接口（`POST /style-family/compare`）已存在
- V0.8.8 已有 5 family 表格，缺的是**真实验证 demo 短片**（当前仅做 UI 卡片展示）
- 把 4.1~4.5 收敛为 5.1 / 5.2 / 5.3 三个 demo，能直接服务审计识别的 P0-2（文本硬截断）问题
- 不动现有 14 style，**完全在 lab 范围内**，符合本阶段"旁路"定位

**预期工作**：

- 在 `RemotionStyleFamilyPage.tsx` 增加 3 个 prototype 卡片（Demo A/B/C）
- 调用 `POST /style-family/compare` 时附带 `prototype: "timeline_news" | "data_panel" | "big_caption_narrative"` 参数
- 后端按 prototype 选择对应 remotionFamily + 内部 mock data
- 每个 demo 跑 5~10s 短片，作为 lab 内部对比素材
- **不写** `presets.py`、**不写** Style Gallery、**不写** job 记录

### 备选方向

- 继续完善 V0.8.8 范式表格（仅文档层）
- 在 `tests/` 中为 lab 加最小 smoke test（不渲染 mp4，只 mock 渲染调用）

---

## 10. 现状核查执行记录

| 项 | 命令 / 路径 | 结果 |
|----|-------------|------|
| 页面文件存在 | `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx` | 1436 行，V0.8.8 |
| 路由挂载 | `frontend/src/App.tsx:41` | `/video-lab/remotion-style-family` |
| 首页入口 | `frontend/src/video-lab/pages/VideoLabHome.tsx:258-261` | "🎞️ Remotion 表现范式" 卡片 |
| 后端接口 | `app/video_lab/router.py:384-388` | `POST /style-family/compare` |
| 后端 service | `app/video_lab/services/style_family_service.py` | `run_style_family_compare()` |
| 入参 schema | `app/video_lab/schemas.py:182-192` | `StyleFamilyCompareRequest` |
| 5 family 范围 | `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx:59-266` | data_news / card_stack / timeline / dashboard / subtitle_story |
| 渲染路径 | `app/video_lab/services/style_family_service.py:48-65` | `render_clip_preview` + `template_programmatic_render` + `remotionFamily` |
| 历史文档 | `docs/REMOTION_STYLE_FAMILY_V0.6.1.md` | 280 行 |
| 测试 | `tests/test_style_gallery_presets.py` (grep 命中) | 仅 presetal 数据测试，非 lab 端到端测试 |

---

## 11. 相关文档

- [V1.2.3 Style Sweep 验证中心基础闭环冻结记录](V1_2_3_STYLE_SWEEP_VALIDATION_BASELINE.md)
- [V1.2.3 Style Sweep 到 Style Gallery 样片库沉淀闭环冻结记录](V1_2_3_STYLE_SWEEP_TO_GALLERY_BASELINE.md)
- [V1.2.3 Style Sweep 历史记录与运行资产治理基线](V1_2_3_STYLE_SWEEP_HISTORY_AND_ASSET_GOVERNANCE_BASELINE.md)
- [V1.2.3 Remotion 模板差异化与背景丰富度审计](V1_2_3_REMOTION_TEMPLATE_DIFFERENTIATION_AUDIT.md)
- [V0.6.1 Remotion 表现范式探索](REMOTION_STYLE_FAMILY_V0.6.1.md)
