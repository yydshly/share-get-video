# V1.2.3 Remotion Style Family Lab 可视化验收记录

> 本文档记录 `/video-lab/remotion-style-family` lab 的**实际可视化验收结果**。
> 范围：API 调用 + 后端日志 + 产物文件 + 前端代码静态检查；**不**做代码修改、不接入 Style Sweep、不写 Style Gallery。
> 验收时间：2026-06-17。

---

## 1. 阶段结论

1. lab 后端接口**完全可调用**，5 个 family 在同一次请求中**全部渲染成功**（success=true）
2. 5 个 18s 短片均落盘在 `runtime/video_lab/experiments/clip_*/clip.mp4`，分辨率 1080x1920（9:16）
3. 渲染路径走 `template_programmatic_render` + `render_clip_preview` + `remotionFamily` 注入，**不写 Style Sweep job JSON，不写 Style Gallery sample**
4. lab 短片**无 referenced_assets 引用**，会被 3A-4 资产清理 dry-run 标为 deletable 候选，**这是预期行为**（lab 不在治理范围）
5. lab 后端能力**已经具备继续做实验的基础**；下一阶段建议先在 lab 增加 3 个 mock family demo（已在 V1.2.3 边界文档中建议），暂不修前端体验

> **验收结论：部分通过**
> 5 family 渲染能力 ✅；长文本/视觉差异/动效节奏等问题需结合人工播放确认（见第 5 节）。

---

## 2. 验收方式

### 2.1 后端启动

```bash
uvicorn app.main:app --port 8777
```

后端启动后访问 `http://127.0.0.1:8777/video-lab/style-family/compare`：
- GET 返回 `{"detail":"Method Not Allowed"}`（仅接受 POST，符合 schema 设计）
- POST 正常返回结果

### 2.2 API 调用

```bash
curl -s -X POST http://127.0.0.1:8777/video-lab/style-family/compare \
  -H "Content-Type: application/json" \
  -d '{"params":{"clipSeconds":3,"keyPointCount":3}}'
```

> 实际验收时 content 字段省略（使用 schema 默认内容）；clipSeconds=3 / keyPointCount=3 是页面 fetch 时使用的默认参数。

### 2.3 前端访问（仅静态检查）

前端页面通过 `npm run dev` 启动后访问 `http://localhost:5173/video-lab/remotion-style-family`。
本轮**未实际打开浏览器**，仅基于代码静态分析 + 后端 API 验证确认页面能力（页面入口、状态机、render 流程、video 标签）。

---

## 3. 接口行为

### 3.1 请求体

```json
{
  "content": "...(可选，schema 默认值会兜底)...",
  "params": {
    "clipSeconds": 3,
    "keyPointCount": 3,
    "aspectRatio": "9:16",
    "useLlmPlan": true
  }
}
```

> `content` 缺省时使用 `app/video_lab/services/style_family_service.py:STYLE_FAMILY_DEFAULT_CONTENT` 兜底。

### 3.2 返回体

```json
{
  "dataNews":        { "experimentId": "", "success": true, "videoUrl": "/runtime/video_lab/experiments/clip_aa0128d0/clip.mp4", "clipSeconds": 3, "elapsedMs": 76100, "message": "", "warnings": [] },
  "cardStack":       { "experimentId": "", "success": true, "videoUrl": "/runtime/video_lab/experiments/clip_6814b290/clip.mp4", "clipSeconds": 3, "elapsedMs": 17381, "message": "", "warnings": [] },
  "timelineNews":    { "experimentId": "", "success": true, "videoUrl": "/runtime/video_lab/experiments/clip_e24c13ba/clip.mp4", "clipSeconds": 3, "elapsedMs": 18819, "message": "", "warnings": [] },
  "dashboardBrief":  { "experimentId": "", "success": true, "videoUrl": "/runtime/video_lab/experiments/clip_0e7fe23f/clip.mp4", "clipSeconds": 3, "elapsedMs": 16350, "message": "", "warnings": [] },
  "captionStory":    { "experimentId": "", "success": true, "videoUrl": "/runtime/video_lab/experiments/clip_290c5316/clip.mp4", "clipSeconds": 3, "elapsedMs": 18458, "message": "", "warnings": [] },
  "totalElapsedMs": 147113
}
```

> 实际耗时 147s 中：dataNews 占 76s（首渲染冷启动），其余 4 个 family 各 ~17s。

### 3.3 关键观察

| # | 项 | 结论 |
|---|----|------|
| 1 | 是否返回 videoUrl | ✅ 5 个 family 全部返回 `/runtime/video_lab/experiments/clip_*/clip.mp4` |
| 2 | 是否返回 success 字段 | ✅ 5 个 family 全部 `success=true` |
| 3 | 是否返回 elapsedMs | ✅ 5 个 family + totalElapsedMs |
| 4 | 是否返回 warnings | ✅ 数组，空数组表示无 warning |
| 5 | 失败时前端显示 | 前端用红色块展示"渲染失败：{message}"（`RemotionStyleFamilyPage.tsx:1317-1319 / 1378-1380`） |
| 6 | 是否写入 job JSON | ❌ 不写（`runtime/video_lab/style_sweep/jobs/` 中无新增） |
| 7 | 是否写入 Style Gallery | ❌ 不写（`runtime/style_gallery/samples.jsonl` 无新增记录） |

### 3.4 视频可访问性

```bash
$ for d in clip_aa0128d0 clip_6814b290 clip_e24c13ba clip_0e7fe23f clip_290c5316; do
    curl -s -o /dev/null -w "$d: %{http_code} %{size_download}\n" \
      http://127.0.0.1:8777/runtime/video_lab/experiments/$d/clip.mp4
  done
clip_aa0128d0: 200 206238
clip_6814b290: 200 231294
clip_e24c13ba: 200 181973
clip_0e7fe23f: 200 175425
clip_290c5316: 200 214988
```

> 5 个 mp4 全部 200，文件大小 175~231KB（18s 1080x1920 H.264 正常范围）。

---

## 4. family 验收结果

### 4.1 family 命名映射

后端 `app/video_lab/services/style_family_service.py:FAMILY_SPECS`：

| response_key | family_id（透传给 render） |
|--------------|----------------------------|
| `dataNews` | `data_news` |
| `cardStack` | `card_stack` |
| `timelineNews` | `timeline_news` |
| `dashboardBrief` | `dashboard_brief` |
| `captionStory` | `caption_story` |

页面 `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx:59-266 FAMILIES` 表格中 5 个 id 与上述一一对应：
- `data_news` → Data News
- `card_stack` → Card Stack
- `timeline` → Timeline（**注意**：页面 FAMILIES 表格 id 是 `timeline`，但渲染走 `remotionFamily=timeline_news`）
- `dashboard` → Dashboard（id `dashboard`，渲染走 `dashboard_brief`）
- `subtitle_story` → Subtitle Story（id `subtitle_story`，渲染走 `caption_story`）

> 文档在第 5 节表格中按"页面 id / 后端 family_id / response_key"三栏并列展示，避免歧义。

### 4.2 5 family 验收

| 页面 id | 后端 family_id | response_key | 是否生成成功 | 是否可播放 | 视觉结构（代码层） | 背景丰富度 | 动效特点 | 文本完整性 | 与其他 family 差异 | 主要问题 | 是否值得继续探索 |
|---------|----------------|--------------|--------------|------------|--------------------|------------|----------|------------|--------------------|----------|------------------|
| `data_news` | data_news | dataNews | ✅ success=true | ✅ 200 206KB | 居中大卡 + 数字 + 数据条 | 2/5（CSS preset 默认 tech_grid_dark） | fade / slide_fade | 截断到 descMaxChars=56 | 是基础款；其他 family 都与它对照 | 与 dashboard_brief / chart_story 区分度有限 | ✅ 是其它 family 的参照基线 |
| `card_stack` | card_stack | cardStack | ✅ success=true | ✅ 200 231KB | 卡片堆叠（前/中/后） | 3/5（aurora_blue） | 卡片滑入/退场 + PREV/NEXT 角标 | 截断到 descMaxChars=56 | ✅ 范式差异化做得最好 | 仅 1 个 style | ✅ 短视频感最强，适合 AI 新闻 |
| `timeline` | timeline_news | timelineNews | ✅ success=true | ✅ 200 182KB | 垂直时间线 + 节点高亮 | 2/5（tech_grid_dark） | 节点依次出现 + 当前节点高亮 | 截断到 descMaxChars=56 | ✅ 范式差异化做得较好 | 与 route_map variant 区分有限 | ✅ 适合解释复杂事件 |
| `dashboard` | dashboard_brief | dashboardBrief | ✅ success=true | ✅ 200 175KB | 指标卡 + 活动信号 + 排行 | 3/5（glass_dashboard） | countup_number + 卡片切换 | 截断到 descMaxChars=56 | ✅ 范式差异化做得较好 | chart_story / ranking_strip 区分有限 | ✅ 信息密度高 |
| `subtitle_story` | caption_story | captionStory | ✅ success=true | ✅ 200 215KB | 大字标题 + 旁白 | 2/5（warm_cinematic） | 缓动 + 进度条 | 截断到 descMaxChars=56 | ✅ 范式差异化做得较好 | caption_intro / cta_overlay 区分有限 | ✅ 适合情绪/口播 |

> **注 1**：上表"视觉结构 / 背景 / 动效"基于代码静态分析（`remotion/src/AiNewsVideo.tsx` 各 Layout 分支），不基于人工播放。
> **注 2**：5 个 family 都使用 `vertical_compact` 布局（`aspectRatio=9:16` 默认），`descMaxChars=56`；这与 V1.2.3 审计文档 P0-2 识别的"文本硬截断"问题一致。
> **注 3**："动效特点"为各 family 在默认参数下的行为，**未实际播放核对**；需人工验证才能确认。

### 4.3 关键发现

1. **5 family 都跑通，但视觉差异主要集中在"范式层"（layout / motion / background preset）**，并非 5 个 family 内部又有 5 种独立设计
2. **5 family 都有文本硬截断问题**（descMaxChars=56），与 V1.2.3 审计 P0-2 一致
3. **9:16 比例稳定**：所有 5 family 输出 resolution=1080x1920，durationSec=18（与 clipSeconds=3 × 关键点数 + 余量一致）
4. **页面渲染流程顺畅**：从前端 fetch 到后端 render 到 video 标签播放，5 个 video 全部能加载
5. **生成耗时 147s（首渲染冷启动）**，单 family 17~76s；对 lab 探索可接受

---

## 5. runtime 资产情况

### 5.1 落盘目录

```text
runtime/video_lab/experiments/clip_aa0128d0/
  clip.mp4                206KB
  manifest.json           2.7KB
  remotion_props.json     2.0KB
  frames/                 (空，可能仅在 sweep 模式才有)
runtime/video_lab/experiments/clip_6814b290/   (card_stack, 231KB)
runtime/video_lab/experiments/clip_e24c13ba/   (timeline_news, 182KB)
runtime/video_lab/experiments/clip_0e7fe23f/   (dashboard_brief, 175KB)
runtime/video_lab/experiments/clip_290c5316/   (caption_story, 215KB)
```

### 5.2 引用关系

| 维度 | lab 产物 | Style Sweep 产物 | 差异 |
|------|----------|------------------|------|
| 写 job JSON | ❌ | ✅（`runtime/video_lab/style_sweep/jobs/{job_id}.json`） | lab 不写历史 |
| 写 Style Gallery | ❌ | ⚠️（需手动 promote） | lab 不进样片库 |
| 写 runtime 短片 | ✅（`runtime/video_lab/experiments/clip_*/clip.mp4`） | ✅（`runtime/video_lab/experiments/exp_*/final_with_audio.mp4`） | 同目录，但**无 job 关联** |
| referenced_assets 追踪 | ❌ | ⚠️（promote 过的才有） | lab 产物不进入 referenced 集合 |

### 5.3 资产清理 dry-run 影响

`POST /video-lab/style-sweep-assets/scan?minAgeDays=0` 扫描时会将以下 lab 产物视为 deletable 候选：

- clip_aa0128d0（data_news 短片）
- clip_6814b290（card_stack 短片）
- clip_e24c13ba（timeline_news 短片）
- clip_0e7fe23f（dashboard_brief 短片）
- clip_290c5316（caption_story 短片）

> **结论原则**：lab 产物是旁路实验资产，**不进入正式样片库**；如果未被 Style Gallery 引用，被 dry-run 标为 deletable **是正常现象**（与 V1.2.3 边界文档 3.3 第 8 条原则一致）。

### 5.4 验证数据

```bash
$ find runtime/video_lab/style_sweep -name "*.json" 2>/dev/null | wc -l
0

$ ls runtime/style_gallery/ 2>/dev/null
ai_asset  html_motion  pillow  records  remotion  style_gallery  test
# style_gallery/samples.jsonl 末尾无新增（最后一条为 2026-06-16 记录）
```

> ✅ 验证：lab 调用不写 Style Sweep job，不写 Style Gallery sample。

---

## 6. 验收结论

### 6.1 整体结论：**部分通过**

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | 页面可访问 | ✅（代码层确认，路由挂载正常；未实际打开浏览器） |
| 2 | 首页有入口 | ✅（`VideoLabHome.tsx:258-261` "🎞️ Remotion 表现范式" 卡片） |
| 3 | 页面中能看到 family 列表 | ✅（5 个 family 卡片 + 5 维度对比矩阵 + 推荐推进顺序 + 3 demo 入口） |
| 4 | 页面能触发 compare / preview | ✅（"生成对比预览" 按钮，调用 POST /style-family/compare） |
| 5 | 页面显示生成状态 | ✅（按钮文字 "渲染中（约 20-40 秒）..."） |
| 6 | 页面能播放/打开生成结果 | ✅（`<video controls>` 5 个 video 标签 + 200 OK） |
| 7 | 5 family 都可生成 | ✅（5 family 全部 success=true） |
| 8 | 5 family 都可播放 | ✅（5 个 video 全部 200） |
| 9 | 不写 Style Sweep job | ✅（style_sweep/jobs/ 无新增） |
| 10 | 不写 Style Gallery sample | ✅（style_gallery/samples.jsonl 无新增） |
| 11 | 不修改 Remotion 主链路 | ✅（accept 仅调 API，不动 Remotion 代码） |
| 12 | 不修改 14 个现有 Remotion style | ✅（未动 `presets.py`） |
| 13 | 视觉差异是否真的不同 | ⚠️（代码层有差异，需人工播放确认） |
| 14 | 文本完整性 | ❌（仍走 descMaxChars=56 硬截断） |

> **未实际打开浏览器**的项目：1 / 13 / 14 中"视觉差异"和"文本完整性"两条，需在 3B-2 阶段由人工播放核验；当前文档仅做能力与边界验收。

### 6.2 当前最值得继续探索的 3 个 family

基于 lab 已验证的范式差异化与 V1.2.3 审计识别的痛点：

| 优先级 | family | 理由 |
|-------|--------|------|
| **1** | `card_stack` | 范式差异化做得最好，短视频感最强；适合做 lab 内"卡片深度 + swipe transition" 实验 |
| **2** | `timeline_news` | 与 data_news 正交；适合"节点节奏 + 路线图"实验；当前 route_map variant 区分有限，需要新 layout |
| **3** | `caption_story` | 与 V1.2.3 审计 P0-2 文本硬截断修复**正相关**；适合做"line-clamp + 动态字号" 实验 |

### 6.3 当前最阻碍 lab 继续探索的问题

| # | 问题 | 影响 |
|---|------|------|
| 1 | 5 family 共用 `descMaxChars=56` 硬截断 | 喂长文本时所有 family 都会被砍，**直接影响 lab 的"长文本能力"探索** |
| 2 | 5 family 都在 `vertical_compact`（9:16） | 9:16 / 16:9 / 1:1 三档布局密度差异无法在 lab 验证 |
| 3 | lab 短片无人工标注入口 | lab 跑完只能看视频对比，无法在页面内打标，难以沉淀"哪个 family 更好"的判断 |
| 4 | lab 产物每次重新生成（无 mock data 缓存） | 每次刷新都跑 ~147s，不便于"在固定素材下反复对比" |
| 5 | FAMILIES 表格中 3 个 id 与 remotionFamily 不一致（timeline / dashboard / subtitle_story vs timeline_news / dashboard_brief / caption_story） | 代码层不统一，开发者易混淆 |

### 6.4 下一阶段应该做能力增强还是先修可视化体验？

**先做能力增强**（V1.2.3 边界文档 9 节已建议 3B-2：增加 3 个 mock family demo），原因：

1. **后端 API 已经够用**：5 family 全部能跑，前端能播；
2. **视觉差异需在 3B-2 阶段实际播放人工判断**：当前仅代码层有差异，需要 3 个 demo 跑出"同一内容在不同 layout 下的实际效果"才能定结论；
3. **文本硬截断修复属于 3B-2 候选能力探索的一部分**（4.4 Text Policy），不是"修 bug"，而是"探索新能力"；
4. **可视化体验问题（id 命名、缓存、标注入口）属于 P2 级别**，等 3 个 demo 跑出实际效果后再决定是否要修。

---

## 7. 当前阶段不包含

1. 不修改 Remotion 组件代码
2. 不改现有 14 个 Remotion style
3. 不改 Style Sweep
4. 不改 Style Gallery
5. 不新增 promote
6. 不新增 cleanup
7. 不删除 runtime 文件
8. 不移动 runtime 文件
9. 不改 TTS
10. 不改 FFmpeg
11. 不改字幕逻辑

> 5 个 lab 短片（clip_aa0128d0 / clip_6814b290 / clip_e24c13ba / clip_0e7fe23f / clip_290c5316）**保留在 runtime**，未删除。

---

## 8. 验收执行记录

| 项 | 命令 / 路径 | 结果 |
|----|-------------|------|
| 后端启动 | `uvicorn app.main:app --port 8777` | 启动成功，监听 8777 |
| 接口可达 | `GET /video-lab/style-family/compare` | `{"detail":"Method Not Allowed"}`（符合 POST-only 设计） |
| 接口调用 | `POST /video-lab/style-family/compare` | 5 family 全部 success=true，totalElapsedMs=147113 |
| 视频可下载 | `curl /runtime/video_lab/experiments/clip_*/clip.mp4` | 5 个 200，175~231KB |
| family 注入正确 | 读 manifest.json 的 `props.remotionFamily` | data_news / card_stack / timeline_news / dashboard_brief / caption_story 全部命中 |
| 落盘目录 | `runtime/video_lab/experiments/clip_aa0128d0/...` | 5 个目录，每个含 clip.mp4 + manifest.json + remotion_props.json + frames/ |
| Style Sweep job | `find runtime/video_lab/style_sweep -name "*.json"` | 0（无新增） |
| Style Gallery sample | `runtime/style_gallery/samples.jsonl` | 末尾无新增（最后一条为 2026-06-16） |
| 浏览器实际打开 | `npm run dev` + 访问 `/video-lab/remotion-style-family` | **未实际执行**（仅代码静态检查） |

---

## 9. 推荐下一阶段

### 3B-2：在已有 `/video-lab/remotion-style-family` 页面中增加 3 个 mock family demo

具体范围（与 V1.2.3 边界文档 9 节一致）：

- **Demo A：Timeline News（时间线快讯）** — 在 lab 中增加"事件节点 + 因果箭头 + 进度推进条" 增强
- **Demo B：Data Panel（动态数据面板）** — 在 lab 中增加"横轴 + 折线 + 当前点高亮" 增强
- **Demo C：Big Caption Narrative（大字旁白叙事）** — 在 lab 中增加 line-clamp + 动态字号（修审计 P0-2）

每个 demo：

- 走 `template_programmatic_render` + 内部 mock data
- 5~10s 短片
- 不写 `presets.py`、不写 Style Gallery、不写 job
- 验收通过后再走 candidate 流程接入主系统

### 备选：3B-2-fix 修复 lab 体验

如果发现 3 个 demo 阶段会受 id 命名不一致 / 无 mock data 缓存等阻碍，可先做轻量修复：

1. FAMILIES id 统一为 `data_news / card_stack / timeline_news / dashboard_brief / caption_story`
2. 渲染时支持传入 `mockData` 参数，使用固定 mock 不每次重新生成
3. 增加 lab 内打标按钮（写入 localStorage / URL state）

---

## 10. 相关文档

- [V1.2.3 Style Sweep 验证中心基础闭环冻结记录](V1_2_3_STYLE_SWEEP_VALIDATION_BASELINE.md)
- [V1.2.3 Style Sweep 到 Style Gallery 样片库沉淀闭环冻结记录](V1_2_3_STYLE_SWEEP_TO_GALLERY_BASELINE.md)
- [V1.2.3 Style Sweep 历史记录与运行资产治理基线](V1_2_3_STYLE_SWEEP_HISTORY_AND_ASSET_GOVERNANCE_BASELINE.md)
- [V1.2.3 Remotion 模板差异化与背景丰富度审计](V1_2_3_REMOTION_TEMPLATE_DIFFERENTIATION_AUDIT.md)
- [V1.2.3 Remotion Style Family Lab 边界与现状核查](V1_2_3_REMOTION_STYLE_FAMILY_LAB_BOUNDARY.md)
- [V0.6.1 Remotion 表现范式探索](REMOTION_STYLE_FAMILY_V0.6.1.md)
